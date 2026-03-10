# Specification: Documentación Docsify para md-evals

## Objetivos
1. Documentación profesional desplegada en GitHub Pages
2. Guía completa de uso para desarrolladores
3. Ejemplos ejecutables y reproducibles
4. Referencia completa de API/CLI
5. Search functionality

## Estructura de Documentación

```
docs/
├── .nojekyll              # Prevent GitHub Pages Jekyll
├── index.html             # Docsify entry point
├── _sidebar.md            # Sidebar navigation
├── _coverpage.md         # Cover page
├── _navbar.md             # Top navigation
│
├── guide/
│   ├── getting-started.md     # Instalación rápida
│   ├── quick-start.md         # Tutorial 5 min
│   ├── configuration.md        # Config eval.yaml
│   ├── treatments.md          # Treatments explained
│   ├── evaluators.md          # Evaluators explained
│   ├── linting.md            # Linter guide
│   └── advanced.md            # Features avanzados
│
├── examples/
│   ├── basic-evaluation.md    # Ejemplo básico
│   ├── multi-treatment.md     # Múltiples treatments
│   ├── llm-judge.md          # LLM Judge ejemplo
│   ├── wildcards.md          # Wildcards
│   └── results-analysis.md    # Análisis de resultados
│
├── reference/
│   ├── cli-commands.md        # Referencia CLI
│   ├── yaml-schema.md         # Schema completo
│   ├── environment.md         # Variables de entorno
│   └── exit-codes.md          # Códigos de salida
│
└── troubleshooting/
    ├── common-issues.md       # Problemas comunes
    └── faq.md                 # FAQ
```

## Features de Docsify

| Feature | Implementación |
|---------|---------------|
| Search | docsify-search plugin |
| Code highlighting | Prism.js (incluido) |
| Theme | Custom con variables CSS |
| Mermaid | diagrams.net support |
| Copy button | docsify-plugin |
| Pagination | docsify-pagination |

## UI/UX

### Colores (Theme)
- Primary: `#6366f1` (Indigo)
- Secondary: `#8b5cf6` (Purple)
- Background: `#0f172a` (Dark)
- Text: `#f8fafc` (Light)
- Accent: `#22d3ee` (Cyan)

### Cover Page
- Logo/Título
- Descripción breve
- Badges (GitHub stars, Python version)
- Links a GitHub

### Sidebar
- Collapsible sections
- Active state highlighting
- Badge counts

## GitHub Pages Integration

### Workflow
```yaml
# .github/workflows/deploy-docs.yml
name: Deploy Docs
on:
  push:
    branches: [main]
    paths: ['docs/**']

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Deploy
        uses: actions/github-pages@v3
```

### Rama docs
- Usar rama `docs/` para fuentes
- GitHub Pages sirve desde `gh-pages` o `/docs`

## Contenido por Sección

### Getting Started
1. Requisitos (Python 3.12+)
2. Instalación (pip, uv)
3. Configuración de API keys
4. Verificación (md-evals --version)

### Quick Start
1. Crear eval.yaml
2. Escribir SKILL.md
3. Ejecutar evaluación
4. Ver resultados

### Configuration Guide
- YAML schema completo
- Ejemplos por sección
- Valores por defecto
- Validación

### Treatments
- ¿Qué es un treatment?
- CONTROL baseline
- Wildcards (LCC_*)
- Variables de entorno

### Evaluators
- Regex evaluator
- Exact match
- LLM Judge
- Scoring y thresholds

### Examples
- Paso a paso con screenshots
- Código reproducible
- Expected output

### Reference
- CLI commands completos
- YAML schema
- Environment variables
- Exit codes

## Success Criteria
- [ ] Docsify instalado y configurado
- [ ] GitHub Pages deployado
- [ ] Search funcionando
- [ ] Todas las secciones completadas
- [ ] Ejemplos ejecutables
- [ ] Responsive design
- [ ] Links funcionando
