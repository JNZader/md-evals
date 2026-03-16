# Phase 10: Advanced Mutation Testing - Code Path Coverage

## Goal
Increase mutation kill rate from 88% → 94%+ by targeting:
- CLI error handling paths (provider errors, GitHub token issues, rate limits)
- GitHub Models provider edge cases (API errors, timeouts, retry logic)
- LLM adapter boundary conditions (model validation, response parsing)
- Evaluator edge cases (regex failures, type mismatches, null handling)

## Coverage Analysis

### Files with Branch Coverage Gaps
1. **cli.py**: 91.28% (16 uncovered branches)
   - Lines 210, 215: Linter failure handling
   - Lines 284-286: GitHub token error path
   - Lines 287-292: Context window / other errors
   - Lines 380-393: Output format handling edge cases

2. **github_models.py**: 91.18% (3 uncovered branches)
   - Lines 224-230: Import/initialization errors
   - Lines 270-273: Rate limit detection
   - Lines 343-354: Streaming error handling
   - Lines 380-384: Timeout/retry logic

3. **llm.py**: 94.74% (4 uncovered statements)
   - Lines 125, 128-131: Model name validation & parsing edge cases

4. **linter.py**: 95.06% (3 uncovered statements)
   - Lines 138-139, 184: Violation severity/rule handling

## Phase 10 Sub-Phase Breakdown

### Phase 10-1: CLI Error Handling (Target: 6 tests)
**Focus**: Provider initialization & execution errors

Tests to add:
1. `test_github_token_error_in_provider_init` - GitHub token missing during init
2. `test_non_github_provider_error` - Generic provider initialization error
3. `test_rate_limit_error_during_execution` - GitHub rate limit hit during run
4. `test_token_error_during_execution` - GitHub token invalid during run
5. `test_context_window_error_handling` - Context exceeds model limit
6. `test_output_format_unknown_option` - Invalid output format fallback

**Mutation targets**: 
- Exception message detection logic (if "github" in error_msg)
- Error code mutations (1 → 2, 3 → 4)
- Help text display mutations
- Condition logic (and → or, in → not in)

---

### Phase 10-2: GitHub Models API Errors (Target: 5 tests)
**Focus**: Azure client initialization & network errors

Tests to add:
1. `test_azure_sdk_import_error` - Missing azure-ai-inference library
2. `test_azure_client_initialization_error` - Generic Azure init failure
3. `test_rate_limit_detection_in_response` - API returns 429 status
4. `test_streaming_network_disconnection` - Mid-stream connection loss
5. `test_timeout_with_retry_logic` - Timeout and automatic retry

**Mutation targets**:
- ImportError vs generic Exception handling
- Rate limit string detection ("rate", "429", "RateLimitError")
- Streaming error categorization
- Retry count mutations (3 → 2, 1)
- Timeout value mutations (30 → 60, 10)

---

### Phase 10-3: LLM Adapter Validation (Target: 4 tests)
**Focus**: Model name parsing & response validation

Tests to add:
1. `test_model_name_with_special_characters` - Model name parsing edge case
2. `test_model_name_case_preservation_variants` - Multiple case variations
3. `test_response_parsing_with_incomplete_fields` - Partial response handling
4. `test_llm_adapter_context_limit_detection` - Detecting context window overflow

**Mutation targets**:
- String parsing logic (split, lower, strip mutations)
- Field existence checks (hasattr → getattr)
- Boundary condition values (0 → 1, 100 → 99)
- Type validation mutations (isinstance checks)

---

### Phase 10-4: Evaluator Boundary Cases (Target: 5 tests)
**Focus**: Edge cases in regex/exact match evaluation

Tests to add:
1. `test_regex_with_multiline_pattern` - Multiline regex handling
2. `test_regex_with_empty_pattern` - Empty regex string
3. `test_exact_match_with_unicode_characters` - Unicode string matching
4. `test_exact_match_empty_string_comparison` - Empty string edge case
5. `test_evaluator_with_very_long_text` - Performance/boundary with huge text

**Mutation targets**:
- Regex compilation error handling (try/except mutations)
- Pattern matching operators (== → !=, in → not in)
- Case sensitivity toggles (lower → upper mutations)
- String length checks (len > 0, etc.)

---

## Phase 10 Deliverables

### Tests
- **Total new tests**: 20 (distributed across 4 sub-phases)
- **Expected duration**: ~3-4 hours (similar to Phase 9d)
- **Expected kill rate improvement**: +5-6% (88% → 93-94%)

### Documentation
- `PHASE10_IMPLEMENTATION_ROADMAP.md` - Detailed test breakdown with code snippets
- `PHASE10_COMPLETION_SUMMARY.md` - Final report with metrics

### Commits
- One atomic commit per sub-phase (4 commits total)
- All tests passing, coverage maintained at 95%+

---

## Success Criteria

✅ All 20 tests passing
✅ Coverage maintained at 95%+
✅ Mutation kill rate ≥ 93%
✅ No breaking changes to source code
✅ All atomic commits with clear messages
✅ Documentation complete

---

## Implementation Start
Ready to begin Phase 10-1 (CLI Error Handling tests).
