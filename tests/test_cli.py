from typer.testing import CliRunner

from main import ExitCode, app

runner = CliRunner()


def test_run_without_key_fails_clearly(sample_prd, monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)  # no .env here
    result = runner.invoke(app, ["run", str(sample_prd)])
    assert result.exit_code == ExitCode.CONFIG, result.output
    assert "ANTHROPIC_API_KEY" in result.output and "--replay" in result.output


def test_replay_with_empty_cache_is_an_llm_error(sample_prd, monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)  # empty .cache/llm here
    result = runner.invoke(app, ["run", str(sample_prd), "--replay", "--out", str(tmp_path / "out")])
    assert result.exit_code == ExitCode.LLM, result.output
    assert "no cached response" in result.output


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


def test_failed_run_still_writes_run_stats(sample_prd, monkeypatch, tmp_path):
    import json

    monkeypatch.chdir(tmp_path)
    out = tmp_path / "out"
    result = runner.invoke(app, ["run", str(sample_prd), "--replay", "--out", str(out)])
    assert result.exit_code == ExitCode.LLM
    stats = json.loads((out / "run_stats.json").read_text(encoding="utf-8"))
    assert stats["exit_code"] == ExitCode.LLM and "no cached response" in stats["error"]
    assert stats["provider"] == "anthropic" and "load_prd" in stats["stage_seconds"]
    assert not any("api_key" in k or "token" == k for k in stats)  # no secret fields
