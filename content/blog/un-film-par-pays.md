---
title: Un film par pays, le carnet est devenu un site
date: 2026-09-16
tags: cinema, dev, react, typescript, supabase
excerpt: Voir au moins un film de chaque pays du monde, c'est facile à dire et difficile à suivre. Alors j'ai codé WorldWideMovie, une petite app React pour tenir ma liste.
---

# Un film par pays, le carnet est devenu un site

Je vais au cinéma plusieurs fois par semaine depuis des années. Récemment, je me suis dit que j'aimerais voir au moins un film par pays, avec une tolérance de plus ou moins un pays selon l'évolution politique du moment. Sur le papier, l'idée tient en une phrase.

Dans les faits, j'ai vite calé. Trois pages de carnet plus tard, je notais la même chose deux fois, et je ne me souvenais plus de ce que je pensais d'un film vu six mois avant. Les coproductions m'ont achevé : un film franco-italien, il compte pour quel pays ? C'est cette question toute bête qui m'a décidé à coder l'outil au lieu de le griffonner.

## Ce que fait WorldWideMovie

Le site liste 197 pays, groupés par continent, avec les drapeaux et les noms en français. Pour chaque pays, je cherche un film et l'appli reconnaît toute seule les pays de production : un film franco-italien se propose à la fois pour la France et l'Italie, et les deux restent marqués comme partenaires sur la fiche.

Chaque film garde une note sur cinq étoiles et un commentaire libre. Le commentaire compte plus que la note, parce que ce que je retiens d'un film, c'est ce que j'en ai écrit le soir même.

Il y a aussi les filtres par continent, la recherche par nom, le tri entre les pays où j'ai déjà vu un film et ceux qui n'attendent rien, une barre de statistiques, et un bouton qui tire un pays au hasard parmi ceux qui me restent. C'est la fonction la plus bête du site et c'est celle que j'utilise le plus.

## La stack, et pourquoi celle-là

- React 19 avec TypeScript et Vite pour l'interface. Le typage m'a épargné pas mal d'allers-retours, vu que les données de films arrivent en texte depuis une API.
- Tailwind CSS v4 pour les styles, Lucide pour les icônes, canvas-confetti quand je valide un pays.
- Supabase pour l'authentification et la base Postgres, avec une table `user_movies`. Je voulais retrouver ma liste depuis n'importe quel navigateur.
- TMDB pour les films, appelée depuis une Edge Function Supabase. C'est le choix dont je suis le plus content : la clé d'API reste côté serveur et ne traîne pas dans le code envoyé au navigateur.
- localStorage pour le mode invité, avec export et import en JSON puis migration de la liste vers le compte à la première connexion. Le site est utilisable tout de suite, sans inscription.
- GitHub Pages et GitHub Actions pour le déploiement : un push sur `main` et la nouvelle version est en ligne.

## Ce que j'en garde

Un détail m'amuse encore : la liste des pays embarque des alias pour les entités qui n'existent plus. Yougoslavie, Tchécoslovaquie, URSS, Allemagne de l'Ouest sont reconnues et rattachées à l'État qui a suivi. Un film yougoslave des années 70 se range donc en Serbie sans que j'aie à batailler avec l'outil. La tolérance de plus ou moins un pays n'était pas seulement une blague, il fallait aussi la coder.

Le site tourne sur [drongier.github.io/WorldWideMovie](https://drongier.github.io/WorldWideMovie/) et le code est sur [GitHub](https://github.com/drongier/WorldWideMovie). Il reste du travail : mieux traiter les films dont je n'arrive pas à identifier la production, accélérer l'ajout d'un film vu en salle, et trouver une idée pour les pays où le cinéma est presque impossible à voir depuis l'Europe. En attendant, il me sert chaque semaine, et c'était le but.
