import json

import pytest

from ctxblame import cli, replay
from ctxblame.trace import TraceWriter, get_step, load_trace

from test_replay import FAKE_KEY, ServerThread, anthropic_resp, make_upstream


def rec(step, cmd, upstream="http://127.0.0.1:9/anthropic"):
    body = {"model": "deepseek-flash", "max_tokens": 100,
            "system": "You are an agent.\nWorking directory: /home/u/repo",
            "tools": [{"name": "Bash", "input_schema": {"type": "object"}}],
            "messages": [{"role": "user", "content": f"task {step}"}]}
    return {"version": 2, "step": step, "format": "anthropic", "upstream": upstream,
            "started_at": "2026-11-13T10:00:0%dZ" % step,
            "request": {"path": "/v1/messages", "headers": {}, "body": body},
            "response": {"status": 200, "streamed": False, "body": anthropic_resp("Bash", cmd)}}


def test_writer_numbers_steps_and_loader_sorts(tmp_path):
    p = tmp_path / "t.jsonl"
    w = TraceWriter(p)
    s1, s2 = w.next_step(), w.next_step()
    w.save(rec(s2, "ls"))  # finished out of order
    w.save(rec(s1, "cat README.md"))
    assert [s.step for s in load_trace(p)] == [1, 2]
    assert TraceWriter(p).next_step() == 3  # appending continues numbering
    steps = load_trace(p)
    assert get_step(steps, 2).response["content"][0]["input"] == {"command": "ls"}
    with pytest.raises(LookupError, match="choose one with --step"):
        get_step(steps, None)
    with pytest.raises(LookupError, match="no step 7"):
        get_step(steps, 7)


def test_single_record_and_directory_load(tmp_path):
    (tmp_path / "d").mkdir()
    for i in (1, 2):
        (tmp_path / "d" / f"r{i}.json").write_text(json.dumps(rec(i, "ls")))
    assert len(load_trace(tmp_path / "d")) == 2
    assert get_step(load_trace(tmp_path / "d" / "r1.json"), None).step == 1


def test_steps_command(tmp_path, capsys):
    p = tmp_path / "t.jsonl"
    p.write_text("\n".join(json.dumps(rec(i, c)) for i, c in
                           [(1, "cat /home/u/repo/README.md"), (2, "cd web && pnpm add x")]) + "\n")
    assert cli.main(["steps", str(p)]) == 0
    out = capsys.readouterr().out
    assert "read README.md" in out and "run pnpm add" in out


def test_replay_one_step_of_a_trace(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("K", FAKE_KEY)
    app = make_upstream()
    with ServerThread(app) as base:
        p = tmp_path / "t.jsonl"
        p.write_text("\n".join(json.dumps(rec(i, c, base + "/anthropic"))
                               for i, c in [(1, "cat x"), (2, "ls -la")]) + "\n")
        rc = cli.main(["replay", str(p), "--step", "2", "-n", "10", "--api-key-env", "K",
                       "--ledger", str(tmp_path / "s.jsonl"), "--out", str(tmp_path / "runs")])
        assert rc == 0
        out = capsys.readouterr().out
        # intent matching: "ls -la", "ls" and "ls -la /tmp" are all listings,
        # but only the first two list "."
        assert "Decision:  list .   (match: intent)" in out
        assert "Same decision:  8/10" in out
        assert app_body(app, 0)["messages"][0]["content"] == "task 2"
        assert cli.main(["replay", str(p), "--api-key-env", "K", "--ledger", str(tmp_path / "s.jsonl")]) == 5


def app_body(app, i):
    from test_replay import CALLS
    return app[CALLS][i]["body"]


def test_target_modal(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("K", FAKE_KEY)
    with ServerThread(make_upstream()) as base:
        p = tmp_path / "t.jsonl"
        p.write_text(json.dumps(rec(1, "cat README.md", base + "/anthropic")) + "\n")
        rc = replay.main([str(p), "-n", "10", "--api-key-env", "K", "--target", "modal",
                          "--ledger", str(tmp_path / "s.jsonl"), "--out", str(tmp_path / "runs")])
    assert rc == 0
    out = capsys.readouterr().out
    assert "Decision:  list ." in out and "Verdict:   stable" in out
    run = json.loads(next((tmp_path / "runs").glob("*.json")).read_text())
    assert run["summary"]["recorded"] == "read README.md"
