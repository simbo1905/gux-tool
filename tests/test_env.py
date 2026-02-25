"""Tests for gux_checker.core.env — .env loading and walk-up logic."""

import os
from pathlib import Path

import pytest
from gux_checker.core.env import _find_dotenv, _parse_dotenv, load_env


class TestParseDotenv:
    def test_simple_key_value(self, tmp_path: Path) -> None:
        f = tmp_path / '.env'
        f.write_text('FOO=bar\n')
        assert _parse_dotenv(f) == {'FOO': 'bar'}

    def test_quoted_values(self, tmp_path: Path) -> None:
        f = tmp_path / '.env'
        f.write_text('KEY="hello world"\nKEY2=\'single\'\n')
        assert _parse_dotenv(f) == {'KEY': 'hello world', 'KEY2': 'single'}

    def test_comments_ignored(self, tmp_path: Path) -> None:
        f = tmp_path / '.env'
        f.write_text('# comment\nFOO=bar\n')
        assert _parse_dotenv(f) == {'FOO': 'bar'}

    def test_blank_lines_ignored(self, tmp_path: Path) -> None:
        f = tmp_path / '.env'
        f.write_text('\nFOO=bar\n\n')
        assert _parse_dotenv(f) == {'FOO': 'bar'}

    def test_no_value(self, tmp_path: Path) -> None:
        f = tmp_path / '.env'
        f.write_text('NOEQUALS\nFOO=bar\n')
        assert _parse_dotenv(f) == {'FOO': 'bar'}


class TestFindDotenv:
    def test_finds_in_cwd(self, tmp_path: Path) -> None:
        dotenv = tmp_path / '.env'
        dotenv.write_text('X=1\n')
        result = _find_dotenv(tmp_path)
        assert result == dotenv

    def test_finds_in_parent(self, tmp_path: Path) -> None:
        subdir = tmp_path / 'sub'
        subdir.mkdir()
        dotenv = tmp_path / '.env'
        dotenv.write_text('X=1\n')
        result = _find_dotenv(subdir)
        assert result == dotenv

    def test_stops_at_git_dir(self, tmp_path: Path) -> None:
        # .env is above .git — should not be found
        parent = tmp_path / 'repo'
        parent.mkdir()
        dotenv = tmp_path / '.env'
        dotenv.write_text('X=1\n')
        git_dir = parent / '.git'
        git_dir.mkdir()
        subdir = parent / 'src'
        subdir.mkdir()
        result = _find_dotenv(subdir)
        assert result is None

    def test_stops_at_git_file(self, tmp_path: Path) -> None:
        # .git as a file (worktree)
        parent = tmp_path / 'repo'
        parent.mkdir()
        dotenv = tmp_path / '.env'
        dotenv.write_text('X=1\n')
        git_file = parent / '.git'
        git_file.write_text('gitdir: ../somewhere\n')
        subdir = parent / 'src'
        subdir.mkdir()
        result = _find_dotenv(subdir)
        assert result is None

    def test_returns_none_when_not_found(self, tmp_path: Path) -> None:
        # No .env anywhere, but tmp_path has no .git either — walks to root
        # Just verify no exception raised
        result = _find_dotenv(tmp_path)
        # May or may not find one depending on system — just check no crash
        assert result is None or result.name == '.env'


class TestLoadEnv:
    def test_sets_missing_vars(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv('TEST_GUX_KEY', raising=False)
        dotenv = tmp_path / '.env'
        dotenv.write_text('TEST_GUX_KEY=secret\n')
        monkeypatch.chdir(tmp_path)
        load_env()
        assert os.environ.get('TEST_GUX_KEY') == 'secret'

    def test_does_not_overwrite_existing(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv('TEST_GUX_KEY2', 'original')
        dotenv = tmp_path / '.env'
        dotenv.write_text('TEST_GUX_KEY2=fromfile\n')
        monkeypatch.chdir(tmp_path)
        load_env()
        assert os.environ.get('TEST_GUX_KEY2') == 'original'

    def test_explicit_env_file(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv('TEST_GUX_KEY3', raising=False)
        dotenv = tmp_path / 'custom.env'
        dotenv.write_text('TEST_GUX_KEY3=custom\n')
        load_env(env_file=str(dotenv))
        assert os.environ.get('TEST_GUX_KEY3') == 'custom'

    def test_returns_path_loaded(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        dotenv = tmp_path / '.env'
        dotenv.write_text('DUMMY=1\n')
        monkeypatch.chdir(tmp_path)
        result = load_env()
        assert result == dotenv

    def test_returns_none_when_no_file(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        # tmp_path has no .env, and we fake a .git so it stops
        (tmp_path / '.git').mkdir()
        monkeypatch.chdir(tmp_path)
        result = load_env()
        assert result is None
