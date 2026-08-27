---
title: Hello World
date: 2026-08-27
tags: meta, blog
excerpt: Bienvenue sur mon blog ! Premier article : comment fonctionne ce site et comment écrire de nouveaux articles.
---

# Hello World ! 👋

Bienvenue sur mon blog. C'est le premier article d'un site que je construis **en public** — littéralement : le code source est sur [GitHub](https://github.com/drongier/portfolio).

## Comment ce site fonctionne

- Les articles sont écrits en **Markdown**, dans `content/blog/`
- Un script Python (`build.py`) génère le HTML statique dans `public/`
- Le site est hébergé gratuitement sur **GitHub Pages**

## Écrire un article

Crée un fichier `content/blog/mon-article.md` avec un petit en-tête :

```markdown
---
title: Mon article
date: 2026-08-27
tags: python, web
excerpt: Une courte description affichée sur la page du blog.
---

Contenu de l'article en Markdown.
```

Puis lance :

```bash
python3 build.py
```

> Le Markdown supporté pour l'instant : titres, paragraphes, listes, blocs de code, citations, gras, italique et liens. Suffisant pour commencer !

À bientôt pour la suite !
