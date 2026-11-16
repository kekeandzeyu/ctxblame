import pytest

from ctxblame.formats import Decision, ToolCall
from ctxblame.match import Matcher, find_cwd, intent
from ctxblame.replay import verdict

CWD = "/home/u/repo"


@pytest.mark.parametrize("call,expected", [
    (ToolCall("Read", {"file_path": "/home/u/repo/config/server.yaml"}), "read config/server.yaml"),
    (ToolCall("Bash", {"command": "cat config/server.yaml"}), "read config/server.yaml"),
    (ToolCall("Bash", {"command": "head -n 50 ./config/server.yaml"}), "read config/server.yaml"),
    (ToolCall("Bash", {"command": "sed -n '1,40p' config/server.yaml"}), "read config/server.yaml"),
    (ToolCall("read_file", {"path": "config/server.yaml"}), "read config/server.yaml"),
    (ToolCall("str_replace_editor", {"command": "view", "path": "/home/u/repo/config/server.yaml"}),
     "read config/server.yaml"),
    (ToolCall("Bash", {"command": "cd apps/web && pnpm add lodash"}), "run pnpm add"),
    (ToolCall("Bash", {"command": "pnpm install --frozen-lockfile"}), "run pnpm install"),
    (ToolCall("shell", {"command": ["bash", "-lc", "npm install lodash"]}), "run npm install"),
    (ToolCall("Bash", {"command": "uv run pytest -q tests/"}), "run pytest"),
    (ToolCall("Bash", {"command": "python -m pytest -x"}), "run pytest"),
    (ToolCall("Bash", {"command": "FOO=1 timeout 60 make clean && make"}), "run make clean"),
    (ToolCall("Bash", {"command": "git status"}), "run git status"),
    (ToolCall("Bash", {"command": "ls -la config"}), "list config"),
    (ToolCall("LS", {"path": "/home/u/repo"}), "list ."),
    (ToolCall("Bash", {"command": "grep -rn TODO src"}), "search TODO"),
    (ToolCall("Grep", {"pattern": "TODO", "path": "src"}), "search TODO"),
    (ToolCall("Edit", {"file_path": "/home/u/repo/src/a.py", "old_string": "x", "new_string": "y"}),
     "edit src/a.py"),
    (ToolCall("Bash", {"command": "sed -i 's/a/b/' src/a.py"}), "edit src/a.py"),
    (ToolCall("check_calendar", {"date": "today"}), "call check_calendar"),
])
def test_intent(call, expected):
    assert intent(call, CWD) == expected


def test_matcher_modes():
    a = Decision([ToolCall("Read", {"file_path": "config/x.yaml"})])
    b = Decision([ToolCall("Bash", {"command": "cat config/x.yaml"})])
    assert Matcher("intent").key(a) == Matcher("intent").key(b)
    assert Matcher("exact").key(a) != Matcher("exact").key(b)
    assert Matcher("name").key(a) == "Read"
    both = Decision([ToolCall("Bash", {"command": "git status"}), ToolCall("Read", {"file_path": "a"})])
    assert Matcher("intent", all_calls=True).key(both) == "read a + run git status"
    assert Matcher("intent").key(Decision([], "done")) == "<no tool call>"
    with pytest.raises(ValueError):
        Matcher("fuzzy")


def test_find_cwd():
    assert find_cwd("...\n - Primary working directory: /root/work/x\n") == "/root/work/x"
    assert find_cwd("<env>\nWorking directory: /tmp/ws.\n</env>") == "/tmp/ws"
    assert find_cwd("no cwd here") is None


def test_verdicts():
    assert verdict("a", [("a", 8), ("b", 2)], 10)[0] == "stable"
    code, text = verdict("b", [("a", 19), ("b", 1)], 20)
    assert code == "atypical" and "usually does a" in text
    assert verdict("a", [("a", 5), ("b", 5)], 10)[0] == "coin_flip"
    assert verdict("a", [("a", 3)], 3)[0] == "too_few"
