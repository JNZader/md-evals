# Proposal: Documentación con Docsify

## Intent
Crear una documentación profesional y beautiful para md-evals usando Docsify, con guías completas, ejemplos y referencias.

## Scope
- **Docsify Setup**: Integrar Docsify con el proyecto para generar documentación estática desde archivos Markdown.
- **Estructura de Docs**: Crear estructura completa de documentación (getting started, guías, referencia, ejemplos).
- **Search**: Agregar funcionalidad de búsqueda.
- **Customización**: Theme personalizado que coincida con la marca md-evals.
- **Deploy**: Configurar GitHub Pages para hosting automático.

## Approach
1. Agregar `docs/` con configuración Docsify
2. Crear archivos Markdown para cada sección
3. Configurar GitHub Actions para deploy automático a GitHub Pages
4. Personalizar theme con colores de md-evals

## Risks
- **Docsify vs MkDocs**: Podría ser mejor MkDocs con mike. *Mitigation*: Docsify es más simple para updates rápidos.
- **Mantenibilidad**: Documentación desactualizada. *Mitigation*: Agregar checks en CI.

## Success Criteria
- Documentación visible en GitHub Pages
- Sección de Quick Start funcional
- Ejemplos ejecutables
- API Reference completa
- Search funcionando
