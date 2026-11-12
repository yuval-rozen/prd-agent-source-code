from typer.testing import CliRunner

from main import ExitCode, app

runner = CliRunner()


def test_run_on_sample_prd(sample_prd, monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)  # no .env here
    result = runner.invoke(app, ["run", str(sample_prd)])
    assert result.exit_code == ExitCode.OK, result.output
    assert "S1 load_prd" in result.output and "units" in result.output


def test_run_missing_file(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["run", "does-not-exist.md"])
    assert result.exit_code == ExitCode.BAD_INPUT


def test_publish_without_token(sample_prd, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["run", str(sample_prd), "--publish", "--repo", "o/r"])
    assert result.exit_code == ExitCode.CONFIG
    assert "GITHUB_TOKEN" in result.output


def test_repo_without_publish(sample_prd, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["run", str(sample_prd), "--repo", "o/r"])
    assert result.exit_code == ExitCode.BAD_INPUT


def test_preview_without_plan(tmp_path):
    result = runner.invoke(app, ["preview", "--out", str(tmp_path)])
    assert result.exit_code == ExitCode.BAD_INPUT
    assert "No saved plan" in result.output
