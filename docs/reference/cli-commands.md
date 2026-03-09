<!-- docs/reference/cli-commands.md -->
# CLI Commands

## md-evals

Main entry point.

```bash
md-evals [OPTIONS] COMMAND [ARGS]
```

## Commands

### init

Scaffold eval.yaml and SKILL.md.

```bash
md-evals init [DIRECTORY] [OPTIONS]
```

| Option | Description |
|--------|-------------|
| `--force, -f` | Overwrite existing files |

### run

Run evaluations.

```bash
md-evals run [OPTIONS]
```

| Option | Alias | Description |
|--------|-------|-------------|
| `--config, -c` | Config file | Default: `eval.yaml` |
| `--treatment, -t` | Treatment(s) | Comma-separated or wildcard |
| `--model, -m` | Override model | Model name |
| `--count` | Repetitions | Number of runs |
| `-n` | Parallel workers | Number of parallel workers |
| `--output, -o` | Output format | `table`, `json`, or `markdown` |
| `--no-lint` | Skip linting | Skip skill validation |
| `--verbose, -v` | Verbose output | Detailed results |

### lint

Validate SKILL.md.

```bash
md-evals lint [SKILL_PATH] [OPTIONS]
```

| Option | Alias | Description |
|--------|-------|-------------|
| `--fail, -f` | Exit with error | Default: true |
| `--verbose, -v` | Show details | |

### list

List treatments and tasks.

```bash
md-evals list [OPTIONS]
```

| Option | Alias | Description |
|--------|-------|-------------|
| `--config, -c` | Config file | Default: `eval.yaml` |
| `--treatments, -t` | List treatments | |
| `--tasks` | List tasks | |

### version

Show version.

```bash
md-evals version
```
