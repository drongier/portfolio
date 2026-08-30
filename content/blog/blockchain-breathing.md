---
title: Blockchain Breathing, une œuvre générée par le pouls d'Ethereum
date: 2026-08-27
tags: javascript, ethereum, art-generatif, canvas
excerpt: Comment j'ai construit une œuvre d'art qui respire au rythme de la blockchain Ethereum, étape par étape, des données brutes jusqu'au moteur de génération.
---

# Blockchain Breathing, une œuvre générée par le pouls d'Ethereum

L'idée est simple à raconter : une œuvre d'art qui se dessine toute seule, dont la forme, la couleur et l'énergie sont dictées en temps réel par l'activité de la blockchain Ethereum. Pas un NFT, pas un smart contract. Juste un canvas qui écoute le réseau et respire avec lui.

Voici comment je l'ai construit, étape par étape, et tout ce que ça m'a appris en chemin.

## Le concept : la blockchain comme horloge

Ethereum fonctionne en Proof of Stake. Toutes les 12 secondes, un validateur produit un bloc. C'est le battement de cœur du système.

J'ai calé toute l'œuvre sur cette horloge :

- **Le slot** (12 s) : chaque nouveau bloc ajoute une étape au dessin.
- **L'epoch** (32 slots, 6 min 24) : une œuvre complète, puis la toile se réinitialise.

Deux données pilotent l'esthétique : le **prix de l'ETH** choisit la palette (bleu froid quand il est bas, ambre chaud quand il monte), et le **nombre de transactions** dans le bloc choisit l'énergie du trait.

## Étape 1 : récupérer les données, sans clé API

Le site devait être 100 % statique, hébergé gratuitement sur GitHub Pages, sans backend et sans clé. Deux sources gratuites suffisent :

- Un **RPC Ethereum public** (`ethereum.publicnode.com`) pour le dernier bloc : timestamp et transactions.
- **CoinGecko** pour le prix de l'ETH.

Le calcul du tempo se fait à partir du timestamp du bloc :

```javascript
const slotIndex = Math.floor(ts / 12) % 32;
const epochId = Math.floor(ts / 384);
```

Une requête toutes les 8 secondes. Léger, fiable, gratuit.

## Étape 2 : la leçon du payload (le premier bug)

Première version : je demandais le bloc avec le paramètre `true` dans `eth_getBlockByNumber`. Résultat : le navigateur téléchargeait plusieurs **mégabytes** par bloc, car chaque transaction était renvoyée en entier. Sur une connexion lente, la page restait figée, rien ne se dessinait.

Le correctif tient en un mot : `false`. On ne récupère plus que les hashes des transactions. Le comptage est identique, le payload passe de plusieurs Mo à quelques Ko. Leçon retenue : avant d'envoyer une requête, regarde ce que le serveur va te renvoyer.

## Étape 3 : le premier moteur, des courbes calligraphiques

Au début, chaque slot dessinait une courbe, façon pinceau japonais. Un trait par bloc, qui s'accumulait sur la toile. Ça marchait, c'était joli, mais je sentais que le moteur avait un plafond.

## Étape 4 : l'inspiration UJI, puis un moteur original

J'adore [UJI](https://github.com/doersino/uji), le générateur d'art de Noah Doersing. C'est une machine à dessiner incroyable : une forme de base dont chaque point se déforme au fil des itérations.

Première idée : copier son moteur. Deuxième réflexion : autant écrire le mien. J'ai gardé le principe (une forme qui évolue) mais avec mes propres mécaniques :

- **Formes** : cercle, étoile, spirale, nœud de lemniscate, polygone.
- **Déformations** : respiration (pulsation radiale), torsion, ondes, fusion, dérive, champs de bruit.

Chaque déformation est appliquée par petites étapes, et l'activité du réseau module son amplitude. Plus le bloc est chargé, plus la forme bouge.

## Étape 5 : une seule forme par epoch

Premier essai : une nouvelle forme aléatoire à chaque slot. Le résultat partait dans tous les sens. Le déclic : et si on gardait **une seule forme** pendant toute l'epoch, qui évolue au fil des blocs ?

Chaque slot applique deux à quatre petites étapes de déformation à la même forme. La toile finale montre la trajectoire complète : la forme qui respire, se tord, ondule pendant 6 minutes. C'est exactement le rendu que je cherchais.

Un autre bug m'est tombé dessus : la forme pouvait sortir de l'écran et on ne voyait plus qu'un bout. J'ai ajouté une normalisation : après chaque slot, la forme est recentrée et réduite si elle déborde. Elle vit toujours dans le cadre, quelle que soit la taille de l'écran.

## Étape 6 : dix moteurs, seedés par l'epoch

Ensuite, j'ai voulu la même magie que les presets d'UJI : une dizaine d'archétypes, chacun avec sa personnalité.

Le seed, c'est l'identifiant de l'epoch. À chaque epoch, le réseau tire un nombre, et ce nombre choisit le moteur parmi dix : orbite, respiration, étoile filante, vortex, nœud, cristal, tapis, galaxie, fleur, tempête.

Chaque moteur a sa forme, ses déformations, son énergie et son style de trait. On ne sait jamais sur lequel on va tomber. Le nom du moteur est affiché en bas de l'écran.

## La galerie : un replay déterministe

Dernier détail qui change tout : l'art est **déterministe**. Les mêmes données produisent exactement la même image. Du coup, pas besoin de stocker des captures : je sauvegarde juste les données brutes de chaque epoch (32 lignes de timestamp, prix, transactions) dans le localStorage, et la galerie **rejoue** les toiles à l'identique. Clic sur une vignette pour l'ouvrir en plein écran.

## Après le lancement : la chasse aux bugs

Un site "qui marche", c'est souvent un site dont on n'a pas encore trouvé les bugs. Les miens ne se sont pas fait attendre.

### Le canvas qui débordait de l'écran

Premier test sur téléphone : la forme n'était plus centrée, je ne voyais qu'un bout du cercle coincé en bas à droite. Le rendu semblait "zoomé".

Le coupable, c'était le canvas sur écran retina. J'avais bien réglé la résolution interne (`canvas.width = W * devicePixelRatio`), mais pas sa taille CSS. Un canvas est un élément dit "remplacé" : sans `width` en CSS, il garde sa taille intrinsèque en pixels physiques et déborde du viewport. Deux lignes ont tout réglé : `canvas.style.width` et `canvas.style.height`.

### La galerie qui rejouait toujours la même chose

Dans le live, chaque epoch avait son archétype. Dans la galerie, toutes les toiles se ressemblaient. En creusant : je seedais le moteur avec l'identifiant de l'epoch, mais je n'archivais jamais cet identifiant. La galerie rejouait donc tout avec le seed zéro.

C'est la leçon la plus importante du projet : dans un système déterministe, le seed fait partie des données. L'oublier, c'est briser la fidélité du replay.

### Le trait qui se dessine en direct

Jusque-là, chaque trait apparaissait d'un coup. Pour la V2, je voulais le voir se tracer, comme un stylo qui suit le contour.

Le principe est simple : chaque trait connaît son instant de naissance, et le rendu ne dessine que la fraction du chemin correspondant au temps écoulé. Calé sur 11 secondes, le trait se termine juste avant que le prochain bloc arrive. Le réseau dessine littéralement sous tes yeux.

### Une galerie toute verte

Après le tracé, un nouveau décalage : le live était coloré, la galerie toute verte. Le vert, c'est le milieu de ma palette. La galerie ajoutait une marge de 100 dollars autour du prix pour calculer les couleurs, ce qui écrasait la variation réelle (quelques dollars sur 6 minutes) et envoyait tout au milieu.

Le correctif : supprimer la marge et adopter le même mapping progressif que le live. Les deux sont désormais cohérents.

### Des tags pour figer les versions

Dernier point, plus méthodologique : j'ai posé des tags Git (`v1.0.0`, `v1.1.0`) pour garder un instantané de chaque étape. C'est la bonne pratique pour revenir en arrière sans encombrer l'historique.

## Ce que j'ai appris

Ce projet m'a appris beaucoup de choses, dans l'ordre où les bugs me les ont enseignées :

1. **Le déterminisme est un superpouvoir** : quand un rendu ne dépend que de ses données, tu peux le rejouer, le partager, l'archiver sans le stocker.
2. **Regarde toujours la taille de la réponse** : un paramètre mal choisi dans une API peut te coûter des mégaoctets.
3. **Itérer sur le concept, pas sur les paramètres** : le vrai saut qualitatif n'est pas venu d'un réglage, mais d'un changement de modèle (une forme par epoch au lieu de trente).
4. **Le seed est une donnée** : un système déterministe ne vaut que si tu archives tout ce qui détermine le rendu, y compris le point de départ.
5. **Un écran, ce n'est pas qu'une résolution** : le devicePixelRatio et la taille CSS du canvas comptent, le moindre oubli décale tout sur les écrans retina.
6. **Le live et le replay doivent partager le même code** : dès que deux chemins calculent la même chose différemment, un écart apparaît.

Le résultat, c'est [Blockchain Breathing](https://drongier.github.io/blockchain-breathing/) : une œuvre qui se construit sous tes yeux, trait après trait, dont chaque toile est une photographie organique de l'état du réseau à cet instant. Ouvre la page, laisse-la vivre 6 minutes, et regarde ce que la blockchain a dessiné.
