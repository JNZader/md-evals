"""Tests for md_evals utilities."""

import pytest
from pathlib import Path

from md_evals.utils import read_file, ensure_dir


class TestReadFile:
    """Test read_file utility."""
    
    def test_read_file(self, tmp_path):
        """Test reading a file."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Hello, World!")
        
        content = read_file(str(test_file))
        
        assert content == "Hello, World!"
    
    def test_read_file_utf8(self, tmp_path):
        """Test reading UTF-8 file."""
        test_file = tmp_path / "unicode.txt"
        test_file.write_text("¡Hola, mundo! 你好")
        
        content = read_file(str(test_file))
        
        assert "¡Hola" in content
        assert "你好" in content


class TestEnsureDir:
    """Test ensure_dir utility."""
    
    def test_ensure_dir_creates(self, tmp_path):
        """Test creating directory."""
        new_dir = tmp_path / "new" / "nested" / "dir"
        
        result = ensure_dir(str(new_dir))
        
        assert result.exists()
        assert result.is_dir()
    
    def test_ensure_dir_existing(self, tmp_path):
        """Test with existing directory."""
        result = ensure_dir(str(tmp_path))
        
        assert result.exists()
        assert result.is_dir()
    
    def test_ensure_dir_returns_path(self, tmp_path):
        """Test return value is Path."""
        result = ensure_dir(str(tmp_path / "test"))
        
        assert isinstance(result, Path)
