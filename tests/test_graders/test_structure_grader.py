"""Tests for structure phase graders (JSON validation, fields, types)."""

import json
import pytest
from pathlib import Path

from md_evals.graders.structure_grader import (
    JSONValidGrader,
    RequiredFieldsGrader,
    FieldTypeGrader,
)


class TestJSONValidGrader:
    """Tests for JSONValidGrader."""

    def test_valid_json_file_passes(self, tmp_path: Path):
        (tmp_path / "out.json").write_text('{"key": "value"}')
        grader = JSONValidGrader(name="json_check", path="out.json")
        result = grader.grade(tmp_path)
        assert result.passed is True
        assert result.score == 1.0

    def test_invalid_json_file_fails(self, tmp_path: Path):
        (tmp_path / "out.json").write_text("{invalid json}")
        grader = JSONValidGrader(name="json_check", path="out.json")
        result = grader.grade(tmp_path)
        assert result.passed is False
        assert "Invalid JSON" in result.reason

    def test_valid_json_content_passes(self, tmp_path: Path):
        grader = JSONValidGrader(name="json_check", content='[1, 2, 3]')
        result = grader.grade(tmp_path)
        assert result.passed is True

    def test_invalid_json_content_fails(self, tmp_path: Path):
        grader = JSONValidGrader(name="json_check", content="not json")
        result = grader.grade(tmp_path)
        assert result.passed is False
        assert result.score == 0.0

    def test_file_not_found(self, tmp_path: Path):
        grader = JSONValidGrader(name="json_check", path="missing.json")
        result = grader.grade(tmp_path)
        assert result.passed is False
        assert "not found" in result.reason

    def test_no_content_or_path(self, tmp_path: Path):
        grader = JSONValidGrader(name="json_check")
        result = grader.grade(tmp_path)
        assert result.passed is False
        assert "No content or path" in result.reason

    def test_empty_string_fails(self, tmp_path: Path):
        grader = JSONValidGrader(name="json_check", content="")
        result = grader.grade(tmp_path)
        assert result.passed is False

    def test_valid_json_array(self, tmp_path: Path):
        grader = JSONValidGrader(name="json_check", content='["a", "b"]')
        result = grader.grade(tmp_path)
        assert result.passed is True

    def test_valid_json_number(self, tmp_path: Path):
        grader = JSONValidGrader(name="json_check", content="42")
        result = grader.grade(tmp_path)
        assert result.passed is True

    def test_details_contain_preview_on_failure(self, tmp_path: Path):
        grader = JSONValidGrader(name="json_check", content="{bad}")
        result = grader.grade(tmp_path)
        assert result.details is not None
        assert "raw_preview" in result.details


class TestRequiredFieldsGrader:
    """Tests for RequiredFieldsGrader."""

    def test_all_fields_present(self, tmp_path: Path):
        data = json.dumps({"name": "test", "version": "1.0", "status": "ok"})
        grader = RequiredFieldsGrader(
            name="fields_check",
            content=data,
            required_fields=["name", "version", "status"],
        )
        result = grader.grade(tmp_path)
        assert result.passed is True
        assert result.score == 1.0

    def test_missing_fields(self, tmp_path: Path):
        data = json.dumps({"name": "test"})
        grader = RequiredFieldsGrader(
            name="fields_check",
            content=data,
            required_fields=["name", "version", "status"],
        )
        result = grader.grade(tmp_path)
        assert result.passed is False
        assert "version" in result.reason
        assert "status" in result.reason

    def test_partial_score(self, tmp_path: Path):
        data = json.dumps({"name": "test", "version": "1.0"})
        grader = RequiredFieldsGrader(
            name="fields_check",
            content=data,
            required_fields=["name", "version", "status"],
        )
        result = grader.grade(tmp_path)
        assert result.passed is False
        # 2 of 3 present = 0.666...
        assert 0.6 < result.score < 0.7

    def test_nested_field_dot_notation(self, tmp_path: Path):
        data = json.dumps({"metadata": {"version": "1.0"}})
        grader = RequiredFieldsGrader(
            name="nested_check",
            content=data,
            required_fields=["metadata.version"],
        )
        result = grader.grade(tmp_path)
        assert result.passed is True

    def test_nested_field_missing(self, tmp_path: Path):
        data = json.dumps({"metadata": {}})
        grader = RequiredFieldsGrader(
            name="nested_check",
            content=data,
            required_fields=["metadata.version"],
        )
        result = grader.grade(tmp_path)
        assert result.passed is False
        assert "metadata.version" in result.reason

    def test_non_object_json_root(self, tmp_path: Path):
        grader = RequiredFieldsGrader(
            name="check",
            content='[1, 2, 3]',
            required_fields=["key"],
        )
        result = grader.grade(tmp_path)
        assert result.passed is False
        assert "not an object" in result.reason

    def test_invalid_json(self, tmp_path: Path):
        grader = RequiredFieldsGrader(
            name="check",
            content="not json",
            required_fields=["key"],
        )
        result = grader.grade(tmp_path)
        assert result.passed is False
        assert "Cannot parse" in result.reason

    def test_file_mode(self, tmp_path: Path):
        (tmp_path / "data.json").write_text('{"name": "test"}')
        grader = RequiredFieldsGrader(
            name="check",
            path="data.json",
            required_fields=["name"],
        )
        result = grader.grade(tmp_path)
        assert result.passed is True

    def test_empty_required_fields(self, tmp_path: Path):
        grader = RequiredFieldsGrader(
            name="check", content='{"key": 1}', required_fields=[]
        )
        result = grader.grade(tmp_path)
        assert result.passed is True


class TestFieldTypeGrader:
    """Tests for FieldTypeGrader."""

    def test_correct_types(self, tmp_path: Path):
        data = json.dumps({"name": "test", "count": 5, "active": True})
        grader = FieldTypeGrader(
            name="type_check",
            content=data,
            field_types={"name": "str", "count": "int", "active": "bool"},
        )
        result = grader.grade(tmp_path)
        assert result.passed is True
        assert result.score == 1.0

    def test_wrong_type(self, tmp_path: Path):
        data = json.dumps({"name": 42})
        grader = FieldTypeGrader(
            name="type_check",
            content=data,
            field_types={"name": "str"},
        )
        result = grader.grade(tmp_path)
        assert result.passed is False
        assert "expected str" in result.reason

    def test_number_type_accepts_int_and_float(self, tmp_path: Path):
        data = json.dumps({"score": 3.14, "count": 7})
        grader = FieldTypeGrader(
            name="type_check",
            content=data,
            field_types={"score": "number", "count": "number"},
        )
        result = grader.grade(tmp_path)
        assert result.passed is True

    def test_missing_field(self, tmp_path: Path):
        data = json.dumps({"name": "test"})
        grader = FieldTypeGrader(
            name="type_check",
            content=data,
            field_types={"missing_field": "str"},
        )
        result = grader.grade(tmp_path)
        assert result.passed is False
        assert "not found" in result.reason

    def test_nested_field_type(self, tmp_path: Path):
        data = json.dumps({"meta": {"tags": ["a", "b"]}})
        grader = FieldTypeGrader(
            name="type_check",
            content=data,
            field_types={"meta.tags": "list"},
        )
        result = grader.grade(tmp_path)
        assert result.passed is True

    def test_unknown_type_name(self, tmp_path: Path):
        data = json.dumps({"key": "value"})
        grader = FieldTypeGrader(
            name="type_check",
            content=data,
            field_types={"key": "imaginary_type"},
        )
        result = grader.grade(tmp_path)
        assert result.passed is False
        assert "Unknown type" in result.reason

    def test_partial_score(self, tmp_path: Path):
        data = json.dumps({"name": "ok", "count": "not_an_int"})
        grader = FieldTypeGrader(
            name="type_check",
            content=data,
            field_types={"name": "str", "count": "int"},
        )
        result = grader.grade(tmp_path)
        assert result.passed is False
        assert result.score == 0.5

    def test_non_object_root(self, tmp_path: Path):
        grader = FieldTypeGrader(
            name="type_check",
            content="[1, 2]",
            field_types={"key": "str"},
        )
        result = grader.grade(tmp_path)
        assert result.passed is False
        assert "not an object" in result.reason

    def test_dict_type(self, tmp_path: Path):
        data = json.dumps({"config": {"key": "value"}})
        grader = FieldTypeGrader(
            name="type_check",
            content=data,
            field_types={"config": "dict"},
        )
        result = grader.grade(tmp_path)
        assert result.passed is True
