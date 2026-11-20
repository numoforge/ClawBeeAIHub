"""ClawBee prototype tests — stdlib unittest only. Run: python3 -m unittest discover -s tests -v"""
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from clawbee.directory import load_directory, search, summary
from clawbee.factory import agent_fingerprint, generate_agent, write_agent
from clawbee.orchestration import ApprovalRequired, Run, RunAborted, run_parallel
from clawbee.providers import StubAdapter, get_adapter, litellm_config
from clawbee.schema import ValidationError, validate_agent, validate_directory_entry
from clawbee.skills import validate_skill


class TestDirectory(unittest.TestCase):
    def test_load_and_summary(self):
        entries = load_directory()
        self.assertEqual(len(entries), 10)
        s = summary(entries)
        self.assertEqual(s["total"], 10)
        self.assertEqual(s["active"], 8)
        self.assertEqual(s["archived_or_eol"], 2)
        self.assertEqual(s["recommendable"], 8)

    def test_search(self):
        entries = load_directory()
        self.assertEqual(len(search(entries, "langgraph")), 1)
        # 5 category=orchestration + Haystack (description mentions orchestration)
        self.assertEqual(len(search(entries, "orchestration")), 6)
        self.assertEqual(len(search(entries, "", recommendable_only=True)), 8)

    def test_archived_entry_warns_but_validates(self):
        entries = {e["id"]: e for e in load_directory()}
        warns = validate_directory_entry(entries["autogen"])
        self.assertTrue(any("archived" in w for w in warns))
        warns = validate_directory_entry(entries["dify"])
        self.assertTrue(any("not OSI-approved" in w for w in warns))

    def test_missing_license_fails(self):
        bad = {k: v for k, v in load_directory()[0].items() if k != "license"}
        with self.assertRaises(ValidationError):
            validate_directory_entry(bad)


class TestFactory(unittest.TestCase):
    def test_generate_is_reproducible(self):
        a1 = generate_agent(agent_id="demo", name="Demo", purpose="test")
        a2 = generate_agent(agent_id="demo", name="Demo", purpose="test")
        self.assertEqual(agent_fingerprint(a1), agent_fingerprint(a2))

    def test_write_agent_roundtrip(self):
        agent = generate_agent(agent_id="demo", name="Demo", purpose="test")
        with tempfile.TemporaryDirectory() as td:
            out = write_agent(agent, Path(td) / "demo", generated_at="2026-11-20")
            data = json.loads(out.read_text())
            self.assertEqual(data["id"], "demo")
            self.assertTrue((Path(td) / "demo" / "HISTORY.md").exists())

    def test_agent_requires_model_adapter(self):
        bad = generate_agent(agent_id="x", name="X", purpose="p")
        del bad["model"]["adapter"]
        with self.assertRaises(ValidationError):
            validate_agent(bad)


class TestOrchestration(unittest.TestCase):
    def _steps(self):
        return [
            {"id": "a", "fn": lambda d: {"x": 1}},
            {"id": "b", "fn": lambda d: {"y": d["x"] + 1}},
        ]

    def test_sequential(self):
        with tempfile.TemporaryDirectory() as td:
            run = Run("r1", self._steps(), state_dir=td)
            state = run.execute()
            self.assertEqual(state["status"], "completed")
            self.assertEqual(state["results"]["b"], {"y": 2})

    def test_resume_does_not_rerun(self):
        calls = {"n": 0}
        def once(d):
            calls["n"] += 1
            return {"v": calls["n"]}
        steps = [{"id": "a", "fn": once},
                 {"id": "b", "fn": lambda d: {"w": 1}, "requires_approval": True}]
        with tempfile.TemporaryDirectory() as td:
            run = Run("r2", steps, state_dir=td)
            with self.assertRaises(ApprovalRequired):
                run.execute()
            self.assertEqual(calls["n"], 1)
            run2 = Run("r2", steps, state_dir=td)
            state = run2.execute(approvals={"b": True})
            self.assertEqual(state["status"], "completed")
            self.assertEqual(calls["n"], 1)  # step a was not re-run

    def test_approval_reject_aborts(self):
        steps = [{"id": "danger", "fn": lambda d: {}, "requires_approval": True}]
        with tempfile.TemporaryDirectory() as td:
            run = Run("r3", steps, state_dir=td)
            with self.assertRaises(RunAborted):
                run.execute(approvals={"danger": False})

    def test_retry_then_continue(self):
        attempts = {"n": 0}
        def flaky(d):
            attempts["n"] += 1
            if attempts["n"] < 3:
                raise RuntimeError("boom")
            return {"ok": True}
        steps = [{"id": "f", "fn": flaky}]
        with tempfile.TemporaryDirectory() as td:
            state = Run("r4", steps, state_dir=td).execute()
            self.assertEqual(state["results"]["f"], {"ok": True})

    def test_hierarchical_subrun(self):
        sub = [{"id": "s1", "fn": lambda d: {"z": 5}}]
        steps = [{"id": "parent", "fn": {"run": sub}}]
        with tempfile.TemporaryDirectory() as td:
            state = Run("r5", steps, state_dir=td).execute()
            self.assertEqual(state["status"], "completed")

    def test_parallel(self):
        steps = [
            {"id": "p1", "fn": lambda d: 1},
            {"id": "p2", "fn": lambda d: (_ for _ in ()).throw(RuntimeError("x"))},
        ]
        out = run_parallel(steps, {})
        self.assertEqual(out["results"]["p1"], 1)
        self.assertIn("p2", out["errors"])


class TestProvidersSkills(unittest.TestCase):
    def test_stub_adapter(self):
        out = StubAdapter().complete([{"role": "user", "content": "hi"}])
        self.assertEqual(out["content"], "[stub] hi")

    def test_unknown_adapter_fails_closed(self):
        with self.assertRaises(Exception):
            get_adapter("nope")

    def test_litellm_config(self):
        cfg = litellm_config([{"model_name": "qwen", "litellm_params": {"model": "ollama/qwen3:8b"}}])
        self.assertEqual(cfg["model_list"][0]["model_name"], "qwen")

    def test_skill_validates(self):
        skill = Path(__file__).resolve().parent.parent / "data" / "skills" / "example-research-skill"
        info = validate_skill(skill)
        self.assertEqual(info["name"], "example-research-skill")


if __name__ == "__main__":
    unittest.main()
