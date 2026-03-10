# Test Refinement Implementation Guide
**Quick Reference for Adding High-Impact Tests**

---

## Quick Start: Which Tests to Add First?

### 🔴 CRITICAL (Add these first - 12-15 mutations killed)

1. **Real Console Output Test** (Reporter) - 5-8 mutations
2. **Exact Prompt Substitution Test** (Engine) - 3-5 mutations  
3. **Score Normalization Boundaries** (Evaluator) - 4-6 mutations

### 🟠 HIGH (Add next - 5-7 mutations killed)

4. **Pass Rate Coloring Tests** (Reporter) - 2-3 mutations
5. **Duration Aggregation Edge Cases** (Reporter) - 2-3 mutations
6. **Evaluator Aggregation Logic** (Engine) - 1-2 mutations

---

## Copy-Paste Ready Code

### Test 1: Reporter - Real Console Output Capture

**File:** `tests/test_reporter.py`  
**Add to:** `class TestReporter` (around line 450)

```python
def test_report_terminal_actual_output_contains_pass_rate(self):
    """Test actual terminal output shows correct pass rate without mocking."""
    config = EvalConfig(name="Test")
    reporter = Reporter(config)
    
    # Create 2 results: 1 pass, 1 fail = 50%
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
                duration_ms=1000
            ),
            passed=False,
            evaluator_results=[],
            timestamp="2024-01-01T00:00:00"
        )
    ]
    
    # Capture real console output
    import io
    from rich.console import Console
    captured_output = io.StringIO()
    reporter.console = Console(file=captured_output, legacy_windows=False)
    
    reporter.report_terminal(results, verbose=False)
    output = captured_output.getvalue()
    
    # Assert actual string content
    assert "50%" in output, f"Expected '50%' in output, got: {output}"
    assert "1/2" in output or "1 / 2" in output, f"Expected '1/2' passed count in: {output}"
    assert "CONTROL" in output
```

### Test 2: Engine - Exact Prompt Substitution

**File:** `tests/test_engine.py`  
**Add to:** `class TestEvalConfigDefaults` (around line 470)

```python
@pytest.mark.asyncio
async def test_run_single_variables_exact_substitution_all_vars(self):
    """Test that all variables are substituted with exact values."""
    config = EvalConfig(
        name="Test",
        defaults=Defaults(model="gpt-4o"),
        treatments={"CONTROL": Treatment(skill_path=None)},
        tests=[Task(
            name="test",
            prompt="Start {a} middle {b} end {c}",
            variables={"a": "AAA", "b": "BBB", "c": "CCC"},
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
            prompt="Start {a} middle {b} end {c}",
            variables={"a": "AAA", "b": "BBB", "c": "CCC"},
            evaluators=[]
        ),
        "CONTROL"
    )
    
    # Get the actual prompt passed to LLM
    call_args = mock_adapter.complete.call_args
    actual_prompt = call_args[1]["prompt"] if "prompt" in call_args[1] else call_args[0][0]
    
    # Assert EXACT substitution
    expected = "Start AAA middle BBB end CCC"
    assert actual_prompt == expected, f"Expected '{expected}', got '{actual_prompt}'"
    assert "{a}" not in actual_prompt
    assert "{b}" not in actual_prompt
    assert "{c}" not in actual_prompt
```

### Test 3: Evaluator - Score Normalization Boundaries

**File:** `tests/test_evaluator.py`  
**Add to:** `class TestLLMJudgeEvaluatorEdgeCases` (around line 860)

```python
@pytest.mark.asyncio
async def test_llm_judge_score_1_normalizes_as_1_div_5(self):
    """Test score=1 normalizes to 0.2 (1/5 not 1/10)."""
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
        pass_threshold=0.19
    )
    
    results = await engine.evaluate("output", [evaluator])
    
    # CRITICAL: Must be 1/5=0.2, not 1/10=0.1
    assert results[0].score == 0.2, f"Expected 0.2, got {results[0].score}"
    assert results[0].passed, "0.2 should exceed threshold of 0.19"

@pytest.mark.asyncio
async def test_llm_judge_score_10_normalizes_correctly(self):
    """Test score=10 normalizes to 1.0 (10/10)."""
    mock_adapter = MagicMock()
    mock_response = MagicMock()
    mock_response.content = '{"score": 10, "reasoning": "Perfect"}'
    
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
    
    assert results[0].score == 1.0, f"Expected 1.0, got {results[0].score}"
    assert results[0].passed, "1.0 should exceed threshold of 0.99"

@pytest.mark.asyncio
async def test_llm_judge_score_6_no_normalization(self):
    """Test score=6 doesn't match either 1-5 or 1-10 scales."""
    mock_adapter = MagicMock()
    mock_response = MagicMock()
    mock_response.content = '{"score": 6, "reasoning": "Out of scale"}'
    
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
    
    # Should NOT normalize - stays 6.0
    assert results[0].score == 6.0, f"Expected 6.0, got {results[0].score}"
    assert results[0].passed, "6.0 > 0.5"
```

### Test 4: Reporter - Pass Rate Coloring

**File:** `tests/test_reporter.py`  
**Add to:** End of `class TestReporter` (around line 1025)

```python
def test_report_terminal_color_green_at_80_percent(self):
    """Test that exactly 80% shows green color in actual output."""
    config = EvalConfig(name="Test")
    reporter = Reporter(config)
    
    # 4/5 = 80%
    results = [
        ExecutionResult(
            treatment="CONTROL", test="t1", prompt="T",
            response=LLMResponse(content="R", model="gpt-4o", provider="openai", duration_ms=100),
            passed=True, evaluator_results=[], timestamp="2024-01-01T00:00:00"
        ),
        ExecutionResult(
            treatment="CONTROL", test="t2", prompt="T",
            response=LLMResponse(content="R", model="gpt-4o", provider="openai", duration_ms=100),
            passed=True, evaluator_results=[], timestamp="2024-01-01T00:00:00"
        ),
        ExecutionResult(
            treatment="CONTROL", test="t3", prompt="T",
            response=LLMResponse(content="R", model="gpt-4o", provider="openai", duration_ms=100),
            passed=True, evaluator_results=[], timestamp="2024-01-01T00:00:00"
        ),
        ExecutionResult(
            treatment="CONTROL", test="t4", prompt="T",
            response=LLMResponse(content="R", model="gpt-4o", provider="openai", duration_ms=100),
            passed=True, evaluator_results=[], timestamp="2024-01-01T00:00:00"
        ),
        ExecutionResult(
            treatment="CONTROL", test="t5", prompt="T",
            response=LLMResponse(content="R", model="gpt-4o", provider="openai", duration_ms=100),
            passed=False, evaluator_results=[], timestamp="2024-01-01T00:00:00"
        ),
    ]
    
    import io
    from rich.console import Console
    captured_output = io.StringIO()
    reporter.console = Console(file=captured_output, legacy_windows=False)
    
    reporter.report_terminal(results, verbose=False)
    output = captured_output.getvalue()
    
    # Verify green color markup
    assert "[green]80%[/green]" in output, f"Expected green 80% in: {output}"

def test_report_terminal_color_yellow_at_50_75_percent(self):
    """Test that 50-79% shows yellow color."""
    config = EvalConfig(name="Test")
    reporter = Reporter(config)
    
    # 3/4 = 75%
    results = [
        ExecutionResult(
            treatment="CONTROL", test="t1", prompt="T",
            response=LLMResponse(content="R", model="gpt-4o", provider="openai", duration_ms=100),
            passed=True, evaluator_results=[], timestamp="2024-01-01T00:00:00"
        ),
        ExecutionResult(
            treatment="CONTROL", test="t2", prompt="T",
            response=LLMResponse(content="R", model="gpt-4o", provider="openai", duration_ms=100),
            passed=True, evaluator_results=[], timestamp="2024-01-01T00:00:00"
        ),
        ExecutionResult(
            treatment="CONTROL", test="t3", prompt="T",
            response=LLMResponse(content="R", model="gpt-4o", provider="openai", duration_ms=100),
            passed=True, evaluator_results=[], timestamp="2024-01-01T00:00:00"
        ),
        ExecutionResult(
            treatment="CONTROL", test="t4", prompt="T",
            response=LLMResponse(content="R", model="gpt-4o", provider="openai", duration_ms=100),
            passed=False, evaluator_results=[], timestamp="2024-01-01T00:00:00"
        ),
    ]
    
    import io
    from rich.console import Console
    captured_output = io.StringIO()
    reporter.console = Console(file=captured_output, legacy_windows=False)
    
    reporter.report_terminal(results, verbose=False)
    output = captured_output.getvalue()
    
    # Verify yellow color markup
    assert "[yellow]75%[/yellow]" in output, f"Expected yellow 75% in: {output}"

def test_report_terminal_color_red_below_50_percent(self):
    """Test that <50% shows red color."""
    config = EvalConfig(name="Test")
    reporter = Reporter(config)
    
    # 1/4 = 25%
    results = [
        ExecutionResult(
            treatment="CONTROL", test="t1", prompt="T",
            response=LLMResponse(content="R", model="gpt-4o", provider="openai", duration_ms=100),
            passed=True, evaluator_results=[], timestamp="2024-01-01T00:00:00"
        ),
        ExecutionResult(
            treatment="CONTROL", test="t2", prompt="T",
            response=LLMResponse(content="R", model="gpt-4o", provider="openai", duration_ms=100),
            passed=False, evaluator_results=[], timestamp="2024-01-01T00:00:00"
        ),
        ExecutionResult(
            treatment="CONTROL", test="t3", prompt="T",
            response=LLMResponse(content="R", model="gpt-4o", provider="openai", duration_ms=100),
            passed=False, evaluator_results=[], timestamp="2024-01-01T00:00:00"
        ),
        ExecutionResult(
            treatment="CONTROL", test="t4", prompt="T",
            response=LLMResponse(content="R", model="gpt-4o", provider="openai", duration_ms=100),
            passed=False, evaluator_results=[], timestamp="2024-01-01T00:00:00"
        ),
    ]
    
    import io
    from rich.console import Console
    captured_output = io.StringIO()
    reporter.console = Console(file=captured_output, legacy_windows=False)
    
    reporter.report_terminal(results, verbose=False)
    output = captured_output.getvalue()
    
    # Verify red color markup
    assert "[red]25%[/red]" in output, f"Expected red 25% in: {output}"
```

### Test 5: Reporter - Duration Aggregation

**File:** `tests/test_reporter.py`  
**Add to:** `class TestReporter` (around line 936)

```python
def test_calculate_summary_duration_three_results_average(self):
    """Test duration average with three different durations."""
    config = EvalConfig(name="Test")
    reporter = Reporter(config)
    
    results = [
        ExecutionResult(
            treatment="CONTROL", test="t1", prompt="T",
            response=LLMResponse(content="R", model="gpt-4o", provider="openai", tokens=10, duration_ms=1000),
            passed=True, evaluator_results=[], timestamp="2024-01-01T00:00:00"
        ),
        ExecutionResult(
            treatment="CONTROL", test="t2", prompt="T",
            response=LLMResponse(content="R", model="gpt-4o", provider="openai", tokens=20, duration_ms=5000),
            passed=True, evaluator_results=[], timestamp="2024-01-01T00:00:00"
        ),
        ExecutionResult(
            treatment="CONTROL", test="t3", prompt="T",
            response=LLMResponse(content="R", model="gpt-4o", provider="openai", tokens=30, duration_ms=4000),
            passed=True, evaluator_results=[], timestamp="2024-01-01T00:00:00"
        ),
    ]
    
    summary = reporter.calculate_summary(results)
    
    # (1000 + 5000 + 4000) / 3 = 3333.333...
    expected_avg = (1000 + 5000 + 4000) / 3
    assert summary["CONTROL"]["avg_duration_ms"] == expected_avg
    assert summary["CONTROL"]["total_tokens"] == 60
    assert summary["CONTROL"]["total"] == 3
    assert summary["CONTROL"]["passed"] == 3
```

### Test 6: Engine - Evaluator Aggregation

**File:** `tests/test_engine.py`  
**Add to:** `class TestEvalConfigDefaults` (around line 773)

```python
@pytest.mark.asyncio
async def test_run_single_multiple_evaluators_middle_fails(self):
    """Test that middle failing evaluator causes overall failure."""
    from md_evals.evaluator import EvaluatorEngine
    
    config = EvalConfig(
        name="Test",
        defaults=Defaults(model="gpt-4o"),
        treatments={"CONTROL": Treatment(skill_path=None)},
        tests=[Task(
            name="test",
            prompt="test1 test2 test3",
            evaluators=[
                RegexEvaluator(name="e1", pattern="test1", pass_on_match=True),
                RegexEvaluator(name="e2", pattern="MISSING", pass_on_match=True),
                RegexEvaluator(name="e3", pattern="test3", pass_on_match=True),
            ]
        )]
    )
    
    mock_adapter = MagicMock()
    mock_response = LLMResponse(
        content="test1 test2 test3",
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
            prompt="test1 test2 test3",
            evaluators=[
                RegexEvaluator(name="e1", pattern="test1", pass_on_match=True),
                RegexEvaluator(name="e2", pattern="MISSING", pass_on_match=True),
                RegexEvaluator(name="e3", pattern="test3", pass_on_match=True),
            ]
        ),
        "CONTROL"
    )
    
    # Overall should fail because e2 failed
    assert result.passed is False, "Should fail when any evaluator fails"
    assert len(result.evaluator_results) == 3
    assert result.evaluator_results[0].passed is True
    assert result.evaluator_results[1].passed is False
    assert result.evaluator_results[2].passed is True
```

---

## Implementation Checklist

- [ ] Add Test 1: Real Console Output (test_reporter.py)
- [ ] Add Test 2: Exact Prompt Substitution (test_engine.py)
- [ ] Add Test 3: Score Normalization (test_evaluator.py)
- [ ] Add Test 4: Pass Rate Coloring (test_reporter.py)
- [ ] Add Test 5: Duration Aggregation (test_reporter.py)
- [ ] Add Test 6: Evaluator Aggregation (test_engine.py)
- [ ] Run tests: `pytest tests/test_*.py -v`
- [ ] Verify all tests pass
- [ ] Run mutation testing

---

## Expected Results

**Before:** ~60% mutation kill rate  
**After:** ~85-90% mutation kill rate  
**Effort:** ~30 minutes to add all 6 tests
**Impact:** +17-25 additional mutations killed

