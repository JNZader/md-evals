# Design: Documentación Docsify

## Tech Stack
- **Docsify**: `docsify-cli` para desarrollo local
- **Hosting**: GitHub Pages
- **CI/CD**: GitHub Actions

## Architecture

```
md-evals/
├── docs/                    # Documentación fuente
│   ├── index.html          # Entry point Docsify
│   ├── _sidebar.md         # Navegación
│   ├── _coverpage.md       # Cover
│   ├── guide/              # Guías
│   ├── examples/           # Ejemplos
│   ├── reference/          # Referencia
│   └── troubleshooting/    # FAQ
├── .github/
│   └── workflows/
│       └── docs.yml        # Deploy automático
└── README.md               # Links a docs
```

## Docsify Configuration

```html
<!-- docs/index.html -->
window.$docsify = {
  name: 'md-evals',
  repo: 'https://github.com/JNZader/md-evals',
  loadSidebar: true,
  loadNavbar: true,
  coverpage: true,
  subMaxLevel: 3,
  search: {
    maxAge: 86400000,
    paths: 'auto',
    placeholder: 'Search',
    noData: 'No Results!',
  },
  pagination: {
    previousText: 'Previous',
    nextText: 'Next',
    crossChapter: true,
  },
  themeColor: '#6366f1',
}
```

## GitHub Pages Config

1. Settings → Pages
2. Source: Deploy from a branch
3. Branch: main, folder: /docs
4. Guardar

## Deployment Flow

```
push to main (docs/**)
       ↓
GitHub Actions triggered
       ↓
npm install -g docsify-cli
docsify build docs/
       ↓
actions/github-pages
       ↓
https://jnzader.github.io/md-evals/
```
