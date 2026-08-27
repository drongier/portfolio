# portfolio

Mon blog / portfolio de développeur, site 100 % statique, généré par un script Python **sans aucune dépendance** (stdlib uniquement), hébergé gratuitement sur GitHub Pages.

## Structure

```
content/
  site.json        → nom, bio, liens (à personnaliser)
  projects.json    → liste des projets
  blog/*.md        → articles en Markdown
templates/         → gabarits HTML (base, home, blog, post)
assets/style.css   → styles
build.py           → génère le site dans public/
```

## Utilisation

```bash
python3 build.py              # génère le site dans public/
python3 -m http.server -d public   # prévisualiser sur http://localhost:8000
```

## Ajouter un article

1. Créer `content/blog/mon-article.md` avec un en-tête :

```markdown
---
title: Mon article
date: 2026-08-27
tags: python, web
excerpt: Courte description affichée sur la page du blog.
---

Contenu en Markdown.
```

2. Relancer `python3 build.py`.

Le script génère automatiquement : la page d'accueil (bio + projets + 3 derniers articles), la page blog, et chaque article.

## Déploiement GitHub Pages

1. Pousser le dépôt sur GitHub (`git push origin main`).
2. Sur GitHub : **Settings → Pages → Source : GitHub Actions**.
3. Le workflow `.github/workflows/pages.yml` build et déploie automatiquement à chaque push sur `main`.

Le site sera publié sur `https://drongier.github.io/portfolio/`.
