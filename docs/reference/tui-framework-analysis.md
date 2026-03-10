# TUI Framework Analysis: PyTermGUI vs Alternatives

**Date**: March 10, 2026  
**Project**: md-evals  
**Current Stack**: Typer + Rich (CLI + tables/panels)

---

## Executive Summary

**For md-evals, PyTermGUI is NOT the right choice right now.**

PyTermGUI es un framework maduro (2.6k ⭐) pero está en **transición de mantenimiento**. El autor está migrando todas las nuevas features a **Shade 40**, su successor. Para md-evals, que tiene un caso de uso simple (CLI + reportes tabulares), **Rich + Typer ya es óptimo**.

---

## Current md-evals Usage

```python
# CLI Framework: Typer
- Simple CLI with commands (init, run, etc)
- Argument parsing, --options, help text
- No interactive input needed beyond basic args

# Output Rendering: Rich
- Tables (results, comparisons)
- Panels (status, errors, info)
- Colors, styles, progress bars
- Console output only (no interactivity)
```

**Assessment**: Lightweight, stable, covers 100% of needs. No interactive TUI required.

---

## Framework Comparison Matrix

| Feature | PyTermGUI | Textual | Blessed | Rich+Typer |
|---------|-----------|---------|---------|-----------|
| **Stars** | 2.6k | 24k | 3.6k | Combined: 77k |
| **Maturity** | Mature | Very Active | Stable | Very Stable |
| **Maintenance** | ⚠️ Transitioning | ✅ Active | ✅ Active | ✅ Active |
| **Learning Curve** | Medium-High | Medium | Low | **Very Low** |
| **Window System** | ✅ Full WM | ✅ Full WM | ❌ Basic | ❌ None |
| **Mouse Support** | ✅ Yes | ✅ Yes | ❌ No | ❌ No |
| **Interactive Widgets** | ✅ 15+ | ✅ 20+ | ⚠️ Limited | ❌ None |
| **Styling System** | YAML/Python | CSS-like | ANSI codes | Markup strings |
| **For Simple CLI** | Overkill | Overkill | Overkill | **Perfect** |
| **For Interactive Dashboards** | Good | **Best-in-class** | Fair | Not suitable |
| **Terminal Compatibility** | Excellent | Excellent | Very Good | Excellent |
| **Color Support** | Excellent | Excellent | Good | Excellent |
| **Documentation** | Very Good | Excellent | Good | Excellent |
| **Community** | Growing | Large | Stable | Large |

---

## Detailed Analysis

### PyTermGUI (2.6k ⭐)

**Strengths**:
- ✅ Beautiful, modern markup language (TIM - "Terminal Integrated Markup")
- ✅ Full window manager with modals and stacking
- ✅ Mouse support out-of-the-box
- ✅ YAML-based styling with NO_COLOR support
- ✅ Great docs at ptg.bczsalba.com
- ✅ Active development (v7.7.4 - Mar 31, 2025)

**Weaknesses**:
- ⚠️ **CRITICAL**: Author explicitly migrating to Shade 40 (next-gen library)
- ⚠️ While "not yet fully obsolete", PTG is no longer primary focus
- ❌ Overkill for md-evals' simple use case (tables + panels)
- ⚠️ Medium-high learning curve for new maintainers
- ⚠️ 1,456 commits but narrowing contributor base

**Best For**: 
- Complex interactive TUI dashboards with menus/forms
- Desktop-like terminal apps with window management
- Text editors, monitoring tools, admin panels

**Verdict for md-evals**: ❌ Too heavy, wrong maintenance trajectory

---

### Textual (24k ⭐ - #1 Active)

**Strengths**:
- ✅ **Most actively maintained** - extensive development
- ✅ Build on Rich (familiar), extends it perfectly
- ✅ CSS-based styling (familiar to web devs)
- ✅ 20+ widgets, full interactivity
- ✅ Excellent docs and tutorials
- ✅ Best debugging tools (Pilot mode)
- ✅ Growing ecosystem

**Weaknesses**:
- ❌ Massive overkill for md-evals (tables + panels)
- ❌ Requires async event loop + message passing
- ❌ Larger dependency footprint
- ⚠️ Steeper learning curve
- ⚠️ More complex error handling

**Best For**:
- Interactive dashboards, live monitoring
- Multi-pane terminal editors
- Real-time collaborative tools
- Any app needing event-driven architecture

**Verdict for md-evals**: ❌ Overkill, wrong scope

---

### Blessed (3.6k ⭐)

**Strengths**:
- ✅ Lightweight, minimal dependencies
- ✅ Excellent terminal capability detection
- ✅ Cross-platform (Windows, macOS, Linux)
- ✅ Good cursor/color control
- ✅ Used in production by major projects

**Weaknesses**:
- ❌ Lower-level API (more work for complex layouts)
- ❌ Limited widget system
- ❌ No mouse support
- ❌ Requires manual styling management

**Best For**:
- Low-level terminal control
- Progress bars, spinners, animations
- Real-time telemetry displays
- Projects requiring minimal dependencies

**Verdict for md-evals**: ❌ Too low-level, missing table/panel rendering

---

### Rich + Typer (Current) - 77k ⭐ Combined

**Strengths**:
- ✅ **ZERO learning curve** - already integrated
- ✅ Rich: Tables, panels, colors, progress - covers 100% of md-evals needs
- ✅ Typer: CLI args, help, validation - covers 100% of CLI needs
- ✅ Excellent documentation (Will McGugan - same author)
- ✅ Huge ecosystem (TanStack Query, Hydra, etc use Rich)
- ✅ Battle-tested in thousands of projects
- ✅ Console output design (md-evals IS console-only reporting)
- ✅ NO_COLOR support, accessibility first-class
- ✅ Minimal dependencies added

**Weaknesses**:
- ❌ No interactive widgets (but md-evals doesn't need them)
- ❌ No window manager (but md-evals doesn't need it)
- ❌ Output-only (perfect for evaluation reports!)

**Best For**:
- CLI apps with rich output formatting
- Simple reports, logs, tables
- Command-line tools (exactly md-evals!)
- Scripts and automation tools

**Verdict for md-evals**: ✅ **OPTIMAL** - purpose-built for this use case

---

## Migration Cost Analysis

### If we switched to PyTermGUI

**Time Investment**: 40-60 hours
- Rewrite CLI structure (Typer → PTG Window Manager)
- Migrate table/panel rendering to PTG widgets
- Update styling system
- Test on multiple terminals
- Update documentation

**Risk**: 🔴 High
- Maintenance is shifting (might break with Shade 40 transition)
- More complex codebase to maintain
- New team members need to learn PTG

**Benefit**: 🟡 Low for md-evals
- Prettier output? (Rich already does this well)
- Interactive features? (Don't need them)
- Window management? (Not needed for reports)

**ROI**: Negative ❌

---

### If we stay with Rich + Typer

**Time Investment**: 0 hours (already done!)

**Risk**: 🟢 Very Low
- Both libraries are stable, widely used
- Both libraries are actively maintained
- Both libraries have huge communities

**Benefit**: 🟢 High
- Keep focus on md-evals' core value (evaluation engine)
- Leverage existing expertise
- Maximize team productivity

**ROI**: Positive ✅

---

## Shade 40: The Future?

**What is it?**
- Next-generation TUI framework by PyTermGUI's author
- Spiritual successor to PyTermGUI
- Built from lessons learned in PTG
- Not ready for production yet (early alpha)

**For md-evals**: Not relevant (console-only reporting app)

---

## Recommendation

### ✅ KEEP Rich + Typer

**Why**:
1. **Perfectly matched use case** - Console output rendering is Rich's forte
2. **Zero migration cost** - Already implemented, tested, deployed
3. **Future-proof** - Both projects are stable and widely used
4. **Team velocity** - No learning curve, all devs already know it
5. **Minimal dependencies** - Lean, fast, reliable

**Possible Future Enhancements** (if needed):
- Rich: `progress.track()` for batch evaluations
- Typer: `prompt()` for interactive config (already possible)
- Rich Jupyter notebook integration for analysis
- Rich markdown export for reports

### ❌ DON'T switch to PyTermGUI

**Why**:
1. Wrong use case (TUI dashboards, not console reports)
2. Transitioning maintenance (author focusing on Shade 40)
3. 40-60 hour migration cost with zero feature gain
4. Adds complexity without solving real problems
5. Team needs to learn new framework

### 🔶 CONSIDER Textual only if...

**...project requirements change to**:
- Interactive real-time dashboard (live metric updates)
- Multi-pane layout with user input
- Browser-like terminal interface
- Monitoring tool rather than reporting tool

**Otherwise**: Leave it to Textual's best-in-class use cases

---

## Final Assessment

**md-evals is fundamentally a console reporting tool**, not a TUI dashboard:

```
Input: YAML config + Markdown files
Processing: LLM evaluation engine
Output: Tables, panels, JSON, markdown

= Rich + Typer use case ✅
≠ PyTermGUI/Textual use case ❌
```

**Recommendation**: Archive this investigation and focus engineering effort on:
1. Improving mutation testing kill rate ✅ (DONE - 58-64%)
2. Comprehensive documentation ✅ (PLANNED - openspec/docs-tasks.md)
3. Advanced evaluation scenarios
4. Performance optimization
5. LLM provider integrations

---

## References

- PyTermGUI: https://github.com/bczsalba/pytermgui
- Shade 40: https://github.com/shade40
- Textual: https://github.com/Textualize/textual
- Blessed: https://github.com/jquast/blessed
- Rich: https://github.com/Textualize/rich
- Typer: https://github.com/tiangolo/typer
