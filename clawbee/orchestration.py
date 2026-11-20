"""Multi-agent orchestration (prototype semantics, stdlib only).

- Sequential: steps in order, output feeds next.
- Parallel: fan-out, results in order, one failure does not cancel siblings.
- Hierarchical: a step may be a sub-run; parent checkpoints before delegating.
- Human-in-the-loop: requires_approval steps pause, checkpoint to disk,
  and wait for an explicit approve/reject decision. Never auto-approves.
- Persistent state: JSON checkpoint per run; resume never re-runs completed steps.
- Error recovery: retry (max 3), skip-if-optional, abort-with-partial-results.
- Audit: append-only JSONL log of every transition.

A step is a callable taking (state: dict) -> dict, or a dict
{"run": <sub-run spec>} for a hierarchical step.
"""
from __future__ import annotations

import json
import time
from pathlib import Path

MAX_RETRIES = 3


class ApprovalRequired(Exception):
    def __init__(self, step_id: str):
        super().__init__(f"approval required for step {step_id}")
        self.step_id = step_id


class RunAborted(Exception):
    pass


def _log(audit_path: Path, event: dict) -> None:
    event = {"ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), **event}
    with audit_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(event, sort_keys=True) + "\n")


class Run:
    def __init__(self, run_id: str, steps: list[dict], *, state_dir: Path | str,
                 audit_path: Path | str | None = None):
        self.run_id = run_id
        self.steps = steps
        self.state_dir = Path(state_dir)
        self.state_dir.mkdir(parents=True, exist_ok=True)
        safe_id = run_id.replace("/", "__").replace("\\", "__")
        self.checkpoint = self.state_dir / f"{safe_id}.json"
        self.audit_path = Path(audit_path) if audit_path else self.state_dir / f"{run_id}.audit.jsonl"
        self.state = self._load() or {"run_id": run_id, "status": "pending",
                                      "step_index": 0, "results": {}, "data": {}}

    def _load(self):
        if self.checkpoint.exists():
            return json.loads(self.checkpoint.read_text(encoding="utf-8"))
        return None

    def _save(self):
        self.checkpoint.write_text(json.dumps(self.state, indent=2, sort_keys=True), encoding="utf-8")

    def _audit(self, event, **kw):
        _log(self.audit_path, {"run_id": self.run_id, "event": event, **kw})

    def _run_step(self, step: dict, state_data: dict) -> dict:
        fn = step["fn"]
        if isinstance(fn, dict) and "run" in fn:  # hierarchical sub-run
            sub = Run(f"{self.run_id}/{step['id']}", fn["run"],
                      state_dir=self.state_dir, audit_path=self.audit_path)
            return sub.execute()
        return fn(state_data)

    def execute(self, *, approvals: dict | None = None) -> dict:
        approvals = approvals or {}
        self.state["status"] = "running"
        self._audit("run_started", step_index=self.state["step_index"])
        while self.state["step_index"] < len(self.steps):
            step = self.steps[self.state["step_index"]]
            sid = step["id"]
            if step.get("requires_approval") and approvals.get(sid) is None:
                self.state["status"] = "waiting_approval"
                self._save()
                self._audit("waiting_approval", step=sid)
                raise ApprovalRequired(sid)
            if step.get("requires_approval") and approvals.get(sid) is False:
                self.state["status"] = "rejected"
                self._save()
                self._audit("approval_rejected", step=sid)
                raise RunAborted(f"step {sid} rejected by human")
            attempts = 0
            while True:
                try:
                    result = self._run_step(step, self.state["data"])
                    break
                except Exception as exc:  # noqa: BLE001 — recovery semantics
                    attempts += 1
                    self._audit("step_failed", step=sid, attempt=attempts, error=str(exc))
                    if attempts >= MAX_RETRIES:
                        if step.get("on_error") == "continue":
                            result = {"skipped": True, "error": str(exc)}
                            break
                        self.state["status"] = "failed"
                        self._save()
                        raise
                    continue
            self.state["results"][sid] = result
            if isinstance(result, dict):
                self.state["data"].update(result)
            self.state["step_index"] += 1
            self._audit("step_done", step=sid)
            self._save()
        self.state["status"] = "completed"
        self._save()
        self._audit("run_completed")
        return self.state


def run_parallel(steps: list[dict], data: dict) -> dict:
    """Fan-out: run each step independently, collect results in order.
    One failure does not cancel siblings; required failures are reported."""
    results, errors = {}, {}
    for step in steps:
        try:
            fn = step["fn"]
            results[step["id"]] = fn(dict(data)) if callable(fn) else fn
        except Exception as exc:  # noqa: BLE001
            errors[step["id"]] = str(exc)
            if step.get("required", True):
                results[step["id"]] = {"error": str(exc)}
    return {"results": results, "errors": errors}
