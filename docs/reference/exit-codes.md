<!-- docs/reference/exit-codes.md -->
# Exit Codes

md-evals uses specific exit codes to indicate the result:

| Code | Meaning | Description |
|------|---------|-------------|
| 0 | Success | All tests passed |
| 1 | Invalid config | Configuration error |
| 2 | Linter violation | SKILL.md validation failed |
| 3 | API error | LLM API error (after retries) |
| 4 | Test failures | All tests failed (with fail_fast) |

## Usage in Scripts

```bash
md-evals run
if [ $? -eq 0 ]; then
  echo "All tests passed!"
elif [ $? -eq 2 ]; then
  echo "Linter failed - check your SKILL.md"
elif [ $? -eq 3 ]; then
  echo "API error - check your keys"
fi
```
