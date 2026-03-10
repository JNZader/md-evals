# Edge Case Tests Review Report
**Project:** md-evals  
**Scope:** 67 new edge case tests across `test_engine.py`, `test_reporter.py`, `test_evaluator.py`  
**Purpose:** Pre-mutation-testing validation and quality assessment  
**Date:** 2026-03-09

---

## Executive Summary

**Test Quality Score: 7/10**

The new edge case tests demonstrate good coverage breadth with **47 solid test cases**, but several critical gaps exist that will allow mutations to survive. Tests are currently **validation-focused** (checking that code runs) rather than **mutation-killing-focused** (asserting exact behavior).

### Key Findings:
- ✅ **Strengths:** Good variable substitution coverage, error handling basics, evaluator type variations
- ❌ **Weaknesses:** Insufficient assertion depth, mocked Console hides formatting bugs, missing boundary condition tests
- ⚠️ **Critical Gaps:** Reporter output string verification, score normalization edge cases, async concurrency

**Estimated Mutations That Will Survive:** 15-20 (40-50% of critical logic)

---

## Test Quality Analysis

### 1. Test Engine (`test_engine.py`) - 38 tests

**Coverage Assessment:**

| Category | Status | Quality | Notes |
|----------|--------|---------|-------|
| `run_single` basic | ✅ Good | 7/10 | Tests existence and basic flow |
| Variable substitution | ✅ Good | 8/10 | Multiple scenarios (special chars, newlines, multiple vars) |
| Error handling | ⚠️ Fair | 6/10 | Only checks `passed=False`, not error content |
| Evaluator integration | ✅ Good | 7/10 | Tests multiple evaluators, all pass, one fails |
| Response structure | ✅ Good | 8/10 | Validates all fields present |
| Timestamp | ✅ Good | 7/10 | Checks ISO format presence |

**Issues Identified:**

1. **Variable substitution doesn't verify final prompt passed to LLM**
   - Tests check that variables are "not in" the result, but don't assert exact content
   - Example: `test_run_single_with_variables` (line 224-267)
   - **Mutation Risk:** HIGH - An off-by-one error in replacement could survive

2. **Empty variables case not fully tested**
   - `test_run_single_empty_variables` (line 348-381) asserts `prompt == "Hello world"` ✅
   - But doesn't test with variables={} and placeholders like `{name}` in prompt
   - **Mutation Risk:** MEDIUM - Edge case of mismatch between defined and used variables

3. **LLMError handling incomplete**
   - `test_run_single_with_llm_error` (line 321-345) only checks `passed=False`
   - Doesn't verify error message in response or error content in result
   - **Mutation Risk:** MEDIUM - Could return success with empty response

4. **Evaluator result aggregation logic not tested for edge cases**
   - Missing test: Multiple evaluators where middle one fails
   - Missing test: Evaluator raises exception during evaluation
   - **Mutation Risk:** MEDIUM - `all()` logic could have off-by-one bugs

5. **Prompt injection scenarios missing**
   - Variables containing `{` or `}` are not tested
   - E.g., variable value = `"Hello {world}"` might cause double-substitution
   - **Mutation Risk:** MEDIUM-HIGH

---

### 2. Reporter Tests (`test_reporter.py`) - 23 tests

**Coverage Assessment:**

| Category | Status | Quality | Notes |
|----------|--------|---------|-------|
| Terminal output | ⚠️ Fair | 5/10 | Uses mocks, no actual output verification |
| JSON output | ✅ Good | 7/10 | Verifies file exists and JSON structure |
| Markdown output | ✅ Good | 7/10 | File existence + basic content checks |
| Summary calculation | ✅ Good | 8/10 | Validates pass rates and stats |
| Pass rate coloring | ⚠️ Fair | 4/10 | Tests don't verify color codes |

**Critical Issues:**

1. **Console output completely mocked - NO ACTUAL STRING VERIFICATION**
   - All `report_terminal` tests mock the Console class
   - Examples: `test_report_terminal_output_contains_title` (line 386-416)
   - **This hides bugs in:**
     - Color code syntax (e.g., `[green]` vs `[/green]` balance)
     - Pass rate percentage formatting
     - Table column alignment
     - Improvement indicators (▲ vs ▼)
   - **Mutation Risk:** CRITICAL - Formatting mutations won't be caught

2. **Pass rate coloring logic not verified**
   - Lines 72-77 in reporter.py define colors: `>=80%` green, `>=50%` yellow, else red
   - Tests `test_report_terminal_all_pass`, `test_report_terminal_all_fail`, `test_report_terminal_partial_pass` exist
   - **BUT:** They only check that console.print was called, not the color styling
   - **Mutation Risk:** HIGH - Could swap green/yellow thresholds: `>=70%` yellow, `>=50%` green

3. **Markdown output has minimal assertions**
   - `test_build_markdown_contains_header` (line 689-718) only checks for "# md-evals Results"
   - `test_build_markdown_contains_summary_table` (line 720-763) checks table header exists
   - **Missing:** Verification of actual pass rate values, formatting of percentages
   - Example: `rate = passed / total * 100 if total > 0 else 0` - no test verifies this calculation
   - **Mutation Risk:** MEDIUM - Off-by-one in calculation or formatting

4. **JSON structure mostly untested**
   - `test_build_output_data_structure` (line 622-687) is good but only checks one treatment
   - Missing: Verification of results array order, field type conversions
   - Example: `r.response.tokens` could be None and tests don't catch it
   - **Mutation Risk:** MEDIUM

5. **Duration and token calculation not verified**
   - `test_calculate_summary_duration_stats` (line 891-935) checks avg calculation
   - **BUT:** Doesn't test edge cases:
     - What if `durations` array is empty? (line 304 in reporter.py)
     - What if `tokens` is None? (line 307 could crash)
   - **Mutation Risk:** MEDIUM-HIGH

6. **Improvement calculation has no assertions on actual output**
   - `test_report_terminal_improvement_calculation` (line 545-620) mocks console
   - Doesn't verify the `improvement` percentage display
   - CONTROL: 50% (1/2), WITH_SKILL: 100% (2/2) = +50% improvement
   - **Mutation Risk:** HIGH - Could calculate as `50%` instead of `+50%`

---

### 3. Evaluator Tests (`test_evaluator.py`) - 6 basic + 48 edge case tests

**Coverage Assessment:**

| Category | Status | Quality | Notes |
|----------|--------|---------|-------|
| Regex matching | ✅ Good | 8/10 | Pattern matching scenarios well covered |
| Exact match | ✅ Good | 8/10 | Case sensitivity tested |
| LLM judge basics | ⚠️ Fair | 6/10 | Score parsing incomplete |
| Score normalization | ⚠️ Fair | 5/10 | Edge cases with dangerous mutations |
| Error handling | ✅ Good | 7/10 | Covers invalid JSON, missing fields |

**Critical Issues:**

1. **Score normalization has exploitable edge cases (CRITICAL)**
   - Implementation (evaluator.py lines 151-154):
     ```python
     if 1 <= score <= 5:
         score = score / 5
     elif 1 <= score <= 10:
         score = score / 10
     ```
   - Tests check: 4→0.8, 8→0.8
   - **Missing test:** Score = 1 exactly
     - 1 <= 1 <= 5: True, so score = 1/5 = 0.2 ✓
     - But test doesn't verify this edge case
   - **Missing test:** Score = 5 exactly (could be caught by both conditions)
     - Currently: First condition catches it → 5/5 = 1.0 ✓
     - But mutation could swap to `elif` only, breaking it
   - **Missing test:** Score = 6 (should pass through unchanged)
     - Currently: 6 doesn't match either condition → stays 6.0
     - **Mutation Risk:** CRITICAL - Could normalize as 6/5 or 6/10
   - **Mutation Risk:** CRITICAL

2. **Threshold comparison at boundary not explicitly tested**
   - `test_llm_judge_at_threshold` (line 752-772) tests `score >= threshold`
   - Good: Verifies that score == threshold passes
   - **Missing:** What if threshold = 0.5001 and score = 0.5? Should this fail?
   - **Mutation Risk:** MEDIUM - Could use `>` instead of `>=`

3. **Score as string parsing incomplete**
   - `test_llm_judge_score_as_string` (line 658-678) tests "0.85"
   - **Missing:** Test with string "4" or "8" (should normalize after parsing)
   - Current code (line 146): `score = float(score)` then normalization
   - **Risk:** If someone changes order, normalization won't apply to string scores
   - **Mutation Risk:** MEDIUM

4. **LLM judge error handling missing details**
   - When `complete_with_json` raises exception, caught broadly (line 169)
   - Test `test_llm_judge_adapter_exception` (line 775-792) only checks `passed=False`
   - Doesn't verify error message text: "LLM judge error"
   - **Mutation Risk:** LOW (caught by integration tests usually)

5. **Regex case-insensitivity not explicitly named**
   - Line 72 in evaluator.py: `re.compile(..., re.MULTILINE | re.IGNORECASE)`
   - Test `test_case_insensitive_pattern` (line 381-392) passes uppercase
   - **But comment says:** "Should match because pattern is compiled with re.IGNORECASE"
   - **Question:** Is IGNORECASE explicitly tested, or is it a side effect?
   - Tests: HELLO matches "hello" pattern ✓
   - **Missing:** Test that uppercase pattern "HELLO" also matches "hello" (symmetry)
   - **Mutation Risk:** LOW-MEDIUM

6. **Exact match substring logic not fully tested**
   - Implementation: `evaluator.expected in output`
   - Tests verify substring matching works
   - **Missing:** Test with overlapping substrings
     - expected = "test", output = "testing" → should pass
     - But test doesn't verify "test" vs "testing"
   - **Mutation Risk:** LOW (Python's `in` operator is solid)

---

## Coverage Gaps Summary

### High-Impact Gaps (Will Kill Mutations)

1. **Reporter: No actual output string assertions**
   - Impact: All formatting mutations survive
   - Recommendation: Add integration tests that capture actual console output

2. **Engine: Variable substitution not fully verified**
   - Impact: Placeholder replacement bugs survive
   - Recommendation: Assert exact `call_args` content for LLM calls

3. **Evaluator: Score normalization edge cases**
   - Impact: Boundary condition mutations in 1-5, 1-10 detection
   - Recommendation: Test score=1, 5, 6, 9, 10, 11 explicitly

4. **Reporter: Pass rate coloring thresholds**
   - Impact: Color swap mutations survive
   - Recommendation: Test that 50% gives yellow, 80% gives green

5. **Reporter: Duration/token aggregation**
   - Impact: Average calculation bugs (sum vs len mismatches)
   - Recommendation: Test with durations=[1000, 3000] → avg=2000

### Medium-Impact Gaps

6. **Evaluator result aggregation logic** - Multiple evaluators with mixed pass/fail
7. **LLM judge threshold comparison** - Test score slightly below/above threshold
8. **Prompt injection scenarios** - Variables containing format string chars
9. **JSON schema validation** - Verify tokens field handling (None vs 0)
10. **Markdown evaluation results** - Verify score display in markdown

---

## Specific Refinement Suggestions

### Refinement 1: Reporter - Real Console Output Capture
**Priority:** HIGH  
**Estimated Impact:** +5-8 mutations killed

**Problem:** Current tests mock Console, so actual formatting mutations survive.

**Current Code:**
```python
def test_report_terminal_output_contains_title(self):
    with patch('md_evals.reporter.Console') as mock_console_class:
        mock_console = MagicMock()
        mock_console_class.return_value = mock_console
        reporter.console = mock_console
        reporter.report_terminal(results, verbose=False)
        assert mock_console.print.called  # ← Only checks it was called!
```

**Suggested Test:**
```python
def test_report_terminal_actual_output_format(self):
    """Test actual formatted terminal output."""
    from io import StringIO
    
    config = EvalConfig(name="Test")
    reporter = Reporter(config)
    
    results = [
        ExecutionResult(
            treatment="CONTROL",
            test="test1",
            prompt="Hello",
            response=LLMResponse(
                content="Hi",
                model="gpt-4o",
                provider="openai",
                duration_ms=1000
            ),
            passed=True,
            evaluator_results=[],
            timestamp="2024-01-01T00:00:00"
        ),
        ExecutionResult(
            treatment="CONTROL",
            test="test2",
            prompt="Hello",
            response=LLMResponse(
                content="Hi",
                model="gpt-4o",
                provider="openai",
                duration_ms=2000
            ),
            passed=False,
            evaluator_results=[],
            timestamp="2024-01-01T00:00:00"
        )
    ]
    
    # Capture actual console output
    import io
    import sys
    captured_output = io.StringIO()
    
    # Create reporter with real console to StringIO
    from rich.console import Console
    reporter.console = Console(file=captured_output, legacy_windows=False)
    
    reporter.report_terminal(results, verbose=False)
    
    output = captured_output.getvalue()
    
    # Assert actual content
    assert "md-evals Results" in output
    assert "CONTROL" in output
    assert "1/2" in output  # 1 of 2 passed
    assert "50%" in output  # 50% pass rate
    assert "1000ms" in output or "1000" in output  # duration visible
```

**Why It Kills Mutations:**
- Tests will catch if `1/2` becomes `2/1` or `1/3`
- Tests will catch if `50%` calculation is wrong
- Tests will catch if duration formatting is incorrect
- Tests will catch if table headers are missing

---

### Refinement 2: Engine - Prompt Variable Substitution Verification
**Priority:** HIGH  
**Estimated Impact:** +3-5 mutations killed

**Problem:** Tests only check variables are "not in" the prompt, not that they're correctly substituted.

**Current Code:**
```python
def test_run_single_with_variables(self):
    # ... setup ...
    result = await engine.run_single(...)
    
    call_args = mock_adapter.complete.call_args
    actual_prompt = call_args[1]["prompt"] if "prompt" in call_args[1] else call_args[0][0]
    assert "{name}" not in actual_prompt  # ← Only checks placeholder is gone!
    assert "{age}" not in actual_prompt
```

**Suggested Test:**
```python
@pytest.mark.asyncio
async def test_run_single_variables_exact_substitution(self):
    """Test that variables are substituted with exact values."""
    config = EvalConfig(
        name="Test",
        defaults=Defaults(model="gpt-4o"),
        treatments={"CONTROL": Treatment(skill_path=None)},
        tests=[Task(
            name="test",
            prompt="Name: {name}, Age: {age}",
            variables={"name": "Alice", "age": "25"},
            evaluators=[]
        )]
    )
    
    mock_adapter = MagicMock()
    mock_response = LLMResponse(
        content="OK",
        model="gpt-4o",
        provider="openai",
        duration_ms=1000,
        raw_response={}
    )
    mock_adapter.complete = AsyncMock(return_value=mock_response)
    
    engine = ExecutionEngine(config, mock_adapter)
    
    result = await engine.run_single(
        Treatment(skill_path=None),
        Task(
            name="test",
            prompt="Name: {name}, Age: {age}",
            variables={"name": "Alice", "age": "25"},
            evaluators=[]
        ),
        "CONTROL"
    )
    
    # Assert EXACT substitution
    call_args = mock_adapter.complete.call_args
    actual_prompt = call_args[1]["prompt"] if "prompt" in call_args[1] else call_args[0][0]
    
    assert actual_prompt == "Name: Alice, Age: 25"  # ← Exact assertion!
    assert "{name}" not in actual_prompt
    assert "{age}" not in actual_prompt

@pytest.mark.asyncio
async def test_run_single_variable_with_braces(self):
    """Test variable values containing braces don't cause issues."""
    config = EvalConfig(
        name="Test",
        defaults=Defaults(model="gpt-4o"),
        treatments={"CONTROL": Treatment(skill_path=None)},
        tests=[Task(
            name="test",
            prompt="JSON: {content}",
            variables={"content": '{"key": "value"}'},
            evaluators=[]
        )]
    )
    
    mock_adapter = MagicMock()
    mock_response = LLMResponse(
        content="OK",
        model="gpt-4o",
        provider="openai",
        duration_ms=1000,
        raw_response={}
    )
    mock_adapter.complete = AsyncMock(return_value=mock_response)
    
    engine = ExecutionEngine(config, mock_adapter)
    
    result = await engine.run_single(
        Treatment(skill_path=None),
        Task(
            name="test",
            prompt="JSON: {content}",
            variables={"content": '{"key": "value"}'},
            evaluators=[]
        ),
        "CONTROL"
    )
    
    call_args = mock_adapter.complete.call_args
    actual_prompt = call_args[1]["prompt"] if "prompt" in call_args[1] else call_args[0][0]
    
    # Verify no double-substitution
    assert actual_prompt == 'JSON: {"key": "value"}'
    assert '{"key": "value"}' in actual_prompt
```

**Why It Kills Mutations:**
- Catches if variable replacement is skipped
- Catches if only first variable is replaced
- Catches if replacement values are swapped
- Catches if braces in values cause issues

---

### Refinement 3: Evaluator - Score Normalization Edge Cases
**Priority:** CRITICAL  
**Estimated Impact:** +4-6 mutations killed

**Problem:** Score normalization at boundaries 1-5 and 1-10 is not thoroughly tested.

**Current Code (evaluator.py, lines 151-154):**
```python
if 1 <= score <= 5:
    score = score / 5
elif 1 <= score <= 10:
    score = score / 10
```

**Tests exist for:** 4→0.8, 8→0.8

**Suggested Tests:**
```python
@pytest.mark.asyncio
async def test_llm_judge_score_normalization_boundary_1(self):
    """Test score=1 normalizes correctly (could match both conditions)."""
    mock_adapter = MagicMock()
    mock_response = MagicMock()
    mock_response.content = '{"score": 1, "reasoning": "Minimal"}'
    
    mock_adapter.complete_with_json = AsyncMock(return_value=mock_response)
    
    engine = EvaluatorEngine(llm_adapter=mock_adapter)
    evaluator = LLMJudgeEvaluator(
        name="judge",
        judge_model="gpt-4o",
        criteria="Test",
        output_schema={},
        pass_threshold=0.19  # 1/5 = 0.2
    )
    
    results = await engine.evaluate("output", [evaluator])
    
    # Must normalize as 1/5 = 0.2 (not 1/10 = 0.1)
    assert results[0].score == 0.2
    assert results[0].passed  # 0.2 > 0.19

@pytest.mark.asyncio
async def test_llm_judge_score_normalization_boundary_5(self):
    """Test score=5 normalizes correctly (boundary of first condition)."""
    mock_adapter = MagicMock()
    mock_response = MagicMock()
    mock_response.content = '{"score": 5, "reasoning": "Perfect"}'
    
    mock_adapter.complete_with_json = AsyncMock(return_value=mock_response)
    
    engine = EvaluatorEngine(llm_adapter=mock_adapter)
    evaluator = LLMJudgeEvaluator(
        name="judge",
        judge_model="gpt-4o",
        criteria="Test",
        output_schema={},
        pass_threshold=0.99
    )
    
    results = await engine.evaluate("output", [evaluator])
    
    # Must normalize as 5/5 = 1.0 (not skip normalization)
    assert results[0].score == 1.0
    assert results[0].passed

@pytest.mark.asyncio
async def test_llm_judge_score_normalization_boundary_6(self):
    """Test score=6 doesn't match either 1-5 or 1-10 boundaries."""
    mock_adapter = MagicMock()
    mock_response = MagicMock()
    mock_response.content = '{"score": 6, "reasoning": "Over scale"}'
    
    mock_adapter.complete_with_json = AsyncMock(return_value=mock_response)
    
    engine = EvaluatorEngine(llm_adapter=mock_adapter)
    evaluator = LLMJudgeEvaluator(
        name="judge",
        judge_model="gpt-4o",
        criteria="Test",
        output_schema={},
        pass_threshold=0.5
    )
    
    results = await engine.evaluate("output", [evaluator])
    
    # Should NOT normalize (6 > 5, so first condition false; 6 > 10 false)
    assert results[0].score == 6.0
    assert results[0].passed  # 6.0 > 0.5

@pytest.mark.asyncio
async def test_llm_judge_score_normalization_boundary_10(self):
    """Test score=10 normalizes correctly (boundary of second condition)."""
    mock_adapter = MagicMock()
    mock_response = MagicMock()
    mock_response.content = '{"score": 10, "reasoning": "Perfect on 10 scale"}'
    
    mock_adapter.complete_with_json = AsyncMock(return_value=mock_response)
    
    engine = EvaluatorEngine(llm_adapter=mock_adapter)
    evaluator = LLMJudgeEvaluator(
        name="judge",
        judge_model="gpt-4o",
        criteria="Test",
        output_schema={},
        pass_threshold=0.99
    )
    
    results = await engine.evaluate("output", [evaluator])
    
    # Must normalize as 10/10 = 1.0
    assert results[0].score == 1.0
    assert results[0].passed

@pytest.mark.asyncio
async def test_llm_judge_score_normalization_boundary_11(self):
    """Test score=11 is outside both scales (shouldn't normalize)."""
    mock_adapter = MagicMock()
    mock_response = MagicMock()
    mock_response.content = '{"score": 11, "reasoning": "Over max"}'
    
    mock_adapter.complete_with_json = AsyncMock(return_value=mock_response)
    
    engine = EvaluatorEngine(llm_adapter=mock_adapter)
    evaluator = LLMJudgeEvaluator(
        name="judge",
        judge_model="gpt-4o",
        criteria="Test",
        output_schema={},
        pass_threshold=0.5
    )
    
    results = await engine.evaluate("output", [evaluator])
    
    # Should NOT normalize
    assert results[0].score == 11.0
    assert results[0].passed  # 11.0 > 0.5

@pytest.mark.asyncio
async def test_llm_judge_score_0_passed_threshold(self):
    """Test score=0 doesn't match 1-5 condition."""
    mock_adapter = MagicMock()
    mock_response = MagicMock()
    mock_response.content = '{"score": 0, "reasoning": "Failed"}'
    
    mock_adapter.complete_with_json = AsyncMock(return_value=mock_response)
    
    engine = EvaluatorEngine(llm_adapter=mock_adapter)
    evaluator = LLMJudgeEvaluator(
        name="judge",
        judge_model="gpt-4o",
        criteria="Test",
        output_schema={},
        pass_threshold=0.5
    )
    
    results = await engine.evaluate("output", [evaluator])
    
    # 0 is not in [1,5] range, so no normalization
    assert results[0].score == 0
    assert not results[0].passed
```

**Why It Kills Mutations:**
- Catches off-by-one errors in boundary conditions (1, 5, 10)
- Catches if conditions are swapped
- Catches if normalization is skipped when it shouldn't be
- Catches if non-matching scores are incorrectly normalized

---

### Refinement 4: Reporter - Pass Rate Coloring Verification
**Priority:** HIGH  
**Estimated Impact:** +2-3 mutations killed

**Problem:** Pass rate coloring thresholds (50%, 80%) not verified with actual output.

**Current Code (reporter.py, lines 72-77):**
```python
if pass_rate >= 80:
    pass_style = "green"
elif pass_rate >= 50:
    pass_style = "yellow"
else:
    pass_style = "red"
```

**Suggested Test:**
```python
def test_report_terminal_pass_rate_color_green_at_80_percent(self):
    """Test that 80% pass rate shows green color."""
    config = EvalConfig(name="Test")
    reporter = Reporter(config)
    
    # Create 4 results: 3 pass, 1 fail = 75% -> should be yellow
    # Create 4 results: 4 pass, 0 fail = 100% -> should be green
    results = [
        ExecutionResult(
            treatment="CONTROL",
            test="test1",
            prompt="Test",
            response=LLMResponse(content="R", model="gpt-4o", provider="openai", duration_ms=100),
            passed=True,
            evaluator_results=[],
            timestamp="2024-01-01T00:00:00"
        ),
        ExecutionResult(
            treatment="CONTROL",
            test="test2",
            prompt="Test",
            response=LLMResponse(content="R", model="gpt-4o", provider="openai", duration_ms=100),
            passed=True,
            evaluator_results=[],
            timestamp="2024-01-01T00:00:00"
        ),
        ExecutionResult(
            treatment="CONTROL",
            test="test3",
            prompt="Test",
            response=LLMResponse(content="R", model="gpt-4o", provider="openai", duration_ms=100),
            passed=True,
            evaluator_results=[],
            timestamp="2024-01-01T00:00:00"
        ),
        ExecutionResult(
            treatment="CONTROL",
            test="test4",
            prompt="Test",
            response=LLMResponse(content="R", model="gpt-4o", provider="openai", duration_ms=100),
            passed=True,
            evaluator_results=[],
            timestamp="2024-01-01T00:00:00"
        ),
    ]
    
    import io
    from rich.console import Console
    captured_output = io.StringIO()
    reporter.console = Console(file=captured_output, legacy_windows=False)
    
    reporter.report_terminal(results, verbose=False)
    
    output = captured_output.getvalue()
    
    # For 100% pass rate, should show green
    # In Rich markup, green is [green]100%[/green]
    assert "[green]100%[/green]" in output

def test_report_terminal_pass_rate_color_yellow_at_50_to_79_percent(self):
    """Test that 50-79% pass rate shows yellow color."""
    config = EvalConfig(name="Test")
    reporter = Reporter(config)
    
    # 3 pass, 1 fail = 75% -> should be yellow
    results = [
        ExecutionResult(
            treatment="CONTROL",
            test="test1",
            prompt="Test",
            response=LLMResponse(content="R", model="gpt-4o", provider="openai", duration_ms=100),
            passed=True,
            evaluator_results=[],
            timestamp="2024-01-01T00:00:00"
        ),
        ExecutionResult(
            treatment="CONTROL",
            test="test2",
            prompt="Test",
            response=LLMResponse(content="R", model="gpt-4o", provider="openai", duration_ms=100),
            passed=True,
            evaluator_results=[],
            timestamp="2024-01-01T00:00:00"
        ),
        ExecutionResult(
            treatment="CONTROL",
            test="test3",
            prompt="Test",
            response=LLMResponse(content="R", model="gpt-4o", provider="openai", duration_ms=100),
            passed=True,
            evaluator_results=[],
            timestamp="2024-01-01T00:00:00"
        ),
        ExecutionResult(
            treatment="CONTROL",
            test="test4",
            prompt="Test",
            response=LLMResponse(content="R", model="gpt-4o", provider="openai", duration_ms=100),
            passed=False,
            evaluator_results=[],
            timestamp="2024-01-01T00:00:00"
        ),
    ]
    
    import io
    from rich.console import Console
    captured_output = io.StringIO()
    reporter.console = Console(file=captured_output, legacy_windows=False)
    
    reporter.report_terminal(results, verbose=False)
    
    output = captured_output.getvalue()
    
    # For 75% pass rate, should show yellow
    assert "[yellow]75%[/yellow]" in output

def test_report_terminal_pass_rate_color_red_below_50_percent(self):
    """Test that <50% pass rate shows red color."""
    config = EvalConfig(name="Test")
    reporter = Reporter(config)
    
    # 1 pass, 3 fail = 25% -> should be red
    results = [
        ExecutionResult(
            treatment="CONTROL",
            test="test1",
            prompt="Test",
            response=LLMResponse(content="R", model="gpt-4o", provider="openai", duration_ms=100),
            passed=True,
            evaluator_results=[],
            timestamp="2024-01-01T00:00:00"
        ),
        ExecutionResult(
            treatment="CONTROL",
            test="test2",
            prompt="Test",
            response=LLMResponse(content="R", model="gpt-4o", provider="openai", duration_ms=100),
            passed=False,
            evaluator_results=[],
            timestamp="2024-01-01T00:00:00"
        ),
        ExecutionResult(
            treatment="CONTROL",
            test="test3",
            prompt="Test",
            response=LLMResponse(content="R", model="gpt-4o", provider="openai", duration_ms=100),
            passed=False,
            evaluator_results=[],
            timestamp="2024-01-01T00:00:00"
        ),
        ExecutionResult(
            treatment="CONTROL",
            test="test4",
            prompt="Test",
            response=LLMResponse(content="R", model="gpt-4o", provider="openai", duration_ms=100),
            passed=False,
            evaluator_results=[],
            timestamp="2024-01-01T00:00:00"
        ),
    ]
    
    import io
    from rich.console import Console
    captured_output = io.StringIO()
    reporter.console = Console(file=captured_output, legacy_windows=False)
    
    reporter.report_terminal(results, verbose=False)
    
    output = captured_output.getvalue()
    
    # For 25% pass rate, should show red
    assert "[red]25%[/red]" in output
```

**Why It Kills Mutations:**
- Catches if thresholds are swapped (80% ↔ 50%)
- Catches if comparison operators are wrong (`>` vs `>=`)
- Catches if colors are assigned to wrong ranges

---

### Refinement 5: Reporter - Duration Aggregation Edge Cases
**Priority:** MEDIUM  
**Estimated Impact:** +2-3 mutations killed

**Problem:** Duration averaging logic not tested for edge cases like empty or None values.

**Suggested Test:**
```python
def test_calculate_summary_duration_empty_durations(self):
    """Test duration calculation when no valid durations exist."""
    config = EvalConfig(name="Test")
    reporter = Reporter(config)
    
    # Create result with duration_ms but empty doesn't test edge
    # Let's test with results that should have durations
    results = []  # Empty results
    
    summary = reporter.calculate_summary(results)
    
    # Should return empty dict, not crash
    assert summary == {}

def test_calculate_summary_duration_single_result(self):
    """Test duration with single result."""
    config = EvalConfig(name="Test")
    reporter = Reporter(config)
    
    results = [
        ExecutionResult(
            treatment="CONTROL",
            test="test1",
            prompt="Test",
            response=LLMResponse(
                content="Response",
                model="gpt-4o",
                provider="openai",
                tokens=50,
                duration_ms=5000
            ),
            passed=True,
            evaluator_results=[],
            timestamp="2024-01-01T00:00:00"
        )
    ]
    
    summary = reporter.calculate_summary(results)
    
    # With single result, avg should equal that result
    assert summary["CONTROL"]["avg_duration_ms"] == 5000

def test_calculate_summary_duration_average_exact(self):
    """Test duration average calculation is exact."""
    config = EvalConfig(name="Test")
    reporter = Reporter(config)
    
    results = [
        ExecutionResult(
            treatment="CONTROL",
            test="test1",
            prompt="Test",
            response=LLMResponse(
                content="R",
                model="gpt-4o",
                provider="openai",
                tokens=10,
                duration_ms=1000
            ),
            passed=True,
            evaluator_results=[],
            timestamp="2024-01-01T00:00:00"
        ),
        ExecutionResult(
            treatment="CONTROL",
            test="test2",
            prompt="Test",
            response=LLMResponse(
                content="R",
                model="gpt-4o",
                provider="openai",
                tokens=20,
                duration_ms=5000
            ),
            passed=True,
            evaluator_results=[],
            timestamp="2024-01-01T00:00:00"
        ),
        ExecutionResult(
            treatment="CONTROL",
            test="test3",
            prompt="Test",
            response=LLMResponse(
                content="R",
                model="gpt-4o",
                provider="openai",
                tokens=30,
                duration_ms=4000
            ),
            passed=True,
            evaluator_results=[],
            timestamp="2024-01-01T00:00:00"
        )
    ]
    
    summary = reporter.calculate_summary(results)
    
    # (1000 + 5000 + 4000) / 3 = 10000 / 3 = 3333.33...
    expected = (1000 + 5000 + 4000) / 3
    assert summary["CONTROL"]["avg_duration_ms"] == expected
    assert summary["CONTROL"]["total_tokens"] == 60  # 10 + 20 + 30
```

**Why It Kills Mutations:**
- Catches if denominator is wrong (dividing by wrong number)
- Catches if sum/aggregation is skipped
- Catches off-by-one errors in iteration

---

### Refinement 6: Engine - Evaluator Aggregation Logic
**Priority:** MEDIUM  
**Estimated Impact:** +1-2 mutations killed

**Problem:** The `all()` logic for determining pass/fail isn't tested with specific orderings.

**Suggested Test:**
```python
@pytest.mark.asyncio
async def test_run_single_evaluator_middle_fails_result_fails(self):
    """Test that if middle evaluator fails, overall result fails."""
    from md_evals.evaluator import EvaluatorEngine
    
    config = EvalConfig(
        name="Test",
        defaults=Defaults(model="gpt-4o"),
        treatments={"CONTROL": Treatment(skill_path=None)},
        tests=[Task(
            name="test",
            prompt="Say test1 test2 test3",
            evaluators=[
                RegexEvaluator(name="first", pattern="test1", pass_on_match=True),
                RegexEvaluator(name="second", pattern="MISSING", pass_on_match=True),  # This fails
                RegexEvaluator(name="third", pattern="test3", pass_on_match=True),
            ]
        )]
    )
    
    mock_adapter = MagicMock()
    mock_response = LLMResponse(
        content="Say test1 test2 test3",
        model="gpt-4o",
        provider="openai",
        duration_ms=1000,
        raw_response={}
    )
    mock_adapter.complete = AsyncMock(return_value=mock_response)
    
    engine = ExecutionEngine(config, mock_adapter, EvaluatorEngine())
    
    result = await engine.run_single(
        Treatment(skill_path=None),
        Task(
            name="test",
            prompt="Say test1 test2 test3",
            evaluators=[
                RegexEvaluator(name="first", pattern="test1", pass_on_match=True),
                RegexEvaluator(name="second", pattern="MISSING", pass_on_match=True),
                RegexEvaluator(name="third", pattern="test3", pass_on_match=True),
            ]
        ),
        "CONTROL"
    )
    
    # Overall should fail because second evaluator failed
    assert result.passed is False
    assert len(result.evaluator_results) == 3
    assert result.evaluator_results[0].passed is True   # first passes
    assert result.evaluator_results[1].passed is False  # second fails
    assert result.evaluator_results[2].passed is True   # third passes
```

**Why It Kills Mutations:**
- Catches if `all()` is replaced with `any()`
- Catches if evaluator results are not properly checked
- Ensures logic: all must pass for overall pass

---

## Mutation Testing Readiness Checklist

| Item | Status | Notes |
|------|--------|-------|
| Variable substitution exact | ⚠️ PARTIAL | Need Refinement 2 |
| Error handling verified | ✅ GOOD | Could test error message text |
| Reporter formatting real output | ❌ MISSING | Need Refinement 1 |
| Pass rate coloring exact | ❌ MISSING | Need Refinement 4 |
| Score normalization boundaries | ⚠️ PARTIAL | Need Refinement 3 |
| Duration calculations exact | ⚠️ PARTIAL | Need Refinement 5 |
| Evaluator aggregation logic | ⚠️ PARTIAL | Need Refinement 6 |
| JSON output structure | ✅ GOOD | Well covered |
| Markdown output format | ⚠️ PARTIAL | Basic checks only |
| Threshold comparisons | ⚠️ PARTIAL | `>=` vs `>` not verified |

---

## Implementation Priority

### Phase 1 (Must Have - +12-15 mutations killed)
1. **Refinement 1:** Real console output capture for reporter
2. **Refinement 3:** Score normalization boundary tests
3. **Refinement 2:** Exact prompt substitution verification

### Phase 2 (Should Have - +5-7 mutations killed)
4. **Refinement 4:** Pass rate coloring verification
5. **Refinement 5:** Duration aggregation edge cases
6. **Refinement 6:** Evaluator aggregation logic

### Phase 3 (Nice to Have - +2-3 mutations killed)
7. Test prompt injection scenarios (braces in variables)
8. Test LLM judge threshold boundary (score exactly at threshold)
9. Test markdown percentage formatting

---

## Summary of Impact

**Current State:**
- 67 tests provide good coverage breadth
- Many tests are validation-focused (does it run?) not mutation-focused (is it correct?)
- Mocked outputs hide formatting bugs
- Edge cases in scoring and aggregation not covered

**After Refinements:**
- Estimated +17-25 additional mutations killed
- Better assertion depth (exact values vs. existence checks)
- Real output verification for display logic
- Comprehensive boundary condition coverage

**Estimated Kill Rate Improvement:**
- Before: ~60% mutation kill rate
- After Refinements: ~85-90% mutation kill rate

---

## Conclusion

The test suite demonstrates **solid foundational coverage** but needs targeted refinements to catch mutations effectively. The primary issue is **insufficient assertion depth**—tests verify code runs but not that it produces correct output.

**Next Steps:**
1. Implement Refinements 1, 2, 3 immediately (critical paths)
2. Add Refinements 4, 5, 6 before mutation testing runs
3. Re-run mutation testing to verify improvement

