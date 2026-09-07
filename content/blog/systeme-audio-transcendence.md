---
title: Concevoir le système audio d'un jeu multijoueur
date: 2026-08-31
tags: dev, javascript, babylon, audio, game-dev
excerpt: Comment j'ai construit l'architecture audio de Transcendence, un jeu multijoueur en navigateur : un moteur unique, des bus de mixage et des tables de déclenchement.
---

# Concevoir le système audio d'un jeu multijoueur

Pour mon projet de fin de cursus à l'École 42, j'ai travaillé sur Transcendence, un jeu multijoueur qui tourne entièrement dans le navigateur. La partie qui m'est revenue, c'est l'audio. Et dans un jeu en réseau, le son n'est pas un détail d'habillage.

## Le problème

Un jeu multijoueur impose des contraintes précises sur le son :

- **Synchronisation** : le son doit coller à ce que voit le joueur, en local comme à distance.
- **Spatialisation** : un ennemi à deux mètres ne doit pas sonner comme un ennemi à cinquante mètres.
- **Latence** : une action locale doit paraître immédiate, même si le serveur garde l'autorité.
- **Variation** : rejouer le même sample des centaines de fois fatigue l'oreille. Il faut randomiser la hauteur et le volume.
- **Performance** : beaucoup de sons simultanés sans craquement ni explosion du CPU.
- **Extensibilité** : ajouter un son de gameplay doit rester du travail de données, pas de la chirurgie dans la logique du jeu.

L'approche naïve, des appels `playSound("fichier.wav")` dispersés partout, ne tient pas sur ces six points. Il fallait une vraie architecture.

## Le principe : des événements, pas des fichiers

La règle qui a guidé tout le reste est simple. Le gameplay ne dit jamais "joue `jump_03.wav` au volume 0.7". Il dit "un saut s'est produit à la position (x, y, z)". C'est au système audio de décider comment le rendre.

Cette séparation vient des middlewares comme Wwise ou FMOD, adaptée à notre stack Babylon.js et React. Elle garde le code de gameplay propre, et elle permet d'itérer sur les assets, le mixage ou le routage sans toucher à la logique du jeu.

## L'architecture : un moteur, une banque, quatre bus

Tout repose sur trois piliers partagés par l'application entière :

1. **Un moteur unique** (`GameAudioEngine`), qui enveloppe l'`AudioEngineV2` de Babylon et crée quatre bus : `sfx`, `music`, `ambient` et `ui`, tous routés vers un bus `master`.
2. **Une banque de sons unique** (`SoundBank`), qui charge chaque son une seule fois au démarrage et le réutilise partout.
3. **Un provider React** (`AudioProvider`), monté à la racine, qui possède le cycle de vie du moteur et de la banque et les distribue via deux hooks : `useUIAudio()` pour les menus, `useGameAudio()` pour le jeu.

Les bus sont la clé du mixage. Le master est la seule porte de sortie : régler `master.volume = 0` coupe tout. Les sliders de l'interface mappent directement sur les bus : Musique sur `music`, Interface sur `ui`, Jeu sur `sfx` plus `ambient` plus `music` à la fois.

## Les tables de déclenchement

Le cœur du côté gameplay tient dans un fichier de données, pas dans du code. Trois pipelines transforment les entrées en sons :

- **Entrée locale** : détection de front montant sur des champs comme `isJumping` ou `isGrounded`, pour les sons ponctuels (saut, atterrissage).
- **Entrée locale continue** : les bruits de pas, déclenchés tant qu'un prédicat est vrai, avec un intervalle minimal (550 ms en marchant, 320 ms en courant).
- **Événements serveur** : dégâts, mort, apparition, attaques, compétences, chacun avec sa position dans l'arène.

Un exemple vaut mieux qu'un long discours. Pour ajouter un son de dégâts, on écrit une ligne :

```ts
trigger('Damage', {
  soundId: 'player_hit',
  predicate: (e, ctx) => e.attacker === ctx.localPlayerId,
  position: (e, ctx) => ctx.remotePositions.get(e.victim) ?? ctx.localPosition,
})
```

Ajouter un son de gameplay devient un travail de données. Le système ne grossit pas à chaque nouveau son.

## Les détails qui comptent

**Variations et randomisation.** Chaque son a plusieurs variations, et chaque lecture tire un volume et une hauteur dans une plage définie. Deux bruits de pas consécutifs ne sonnent jamais pareil.

**Fallback procédural.** Si un fichier WAV manque ou renvoie une 404, la banque synthétise un son de remplacement avec la bonne enveloppe : balayage montant pour un saut, impact descendant pour un atterrissage. Le jeu garde son feedback audio même avec des assets incomplets.

**Résolution par classe.** Le joueur peut être chevalier ou voleur. Quand le code demande `player_footstep`, le système résout vers `knight_footstep` ou `rogue_footstep` s'il existe dans la banque, sinon il retombe sur le générique.

**Playlist mélangée.** La musique en jeu ne boucle pas sur un seul morceau. Elle enchaîne aléatoirement les cinq pistes via l'observable de fin de lecture, sans jamais rejouer deux fois le même morceau d'affilée.

**Persistance.** Les volumes et le mute sont stockés dans `localStorage`, avec validation et bornage à la lecture pour qu'un stockage corrompu ne casse jamais le moteur.

## La leçon que je retiens

La décision la plus importante a été un refactor : unifier en un seul moteur ce qui était deux moteurs séparés. Dans une version précédente, le jeu avait son propre moteur audio, et le modal de réglages n'agissait que sur les menus. Résultat : le bouton "couper le son" ne coupait pas le jeu. Unifier a éliminé toute une classe de bugs du type "le slider ne fait rien".

C'est un schéma qui revient sans cesse dans ce projet : mettre la politique (quels sons, à quels volumes, sur quels événements) dans des données, et ne garder que l'exécution dans le code. Le jour où on veut ajouter un son, on n'écrit pas de logique. On ajoute une ligne.
