"""ClawBee CLI (prototype): `python -m clawbee.cli <command>`.

Commands: status | directory [query] | generate <id> <name> <purpose>
No network, no keys. Exit code 0 on success, 2 on usage error.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from clawbee import __version__  # noqa: E402
from clawbee.directory import load_directory, search, summary  # noqa: E402
from clawbee.factory import generate_agent, write_agent  # noqa: E402
from clawbee.providers import StubAdapter  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or argv[0] in ("-h", "--help", "help"):
        print("clawbee " + __version__)
        print("usage: clawbee status | directory [query] | generate <id> <name> <purpose>")
        return 0
    cmd = argv[0]
    if cmd == "status":
        entries = load_directory()
        print(json.dumps({"clawbee": __version__, "directory": summary(entries)}, indent=2))
        return 0
    if cmd == "directory":
        entries = search(load_directory(), argv[1] if len(argv) > 1 else "")
        for e in entries:
            print(f"{e['id']:28} {e['status']:8} {e['license']['spdx']:18} {e['name']}")
        return 0
    if cmd == "generate":
        if len(argv) < 4:
            print("usage: clawbee generate <id> <name> <purpose>", file=sys.stderr)
            return 2
        agent = generate_agent(agent_id=argv[1], name=argv[2], purpose=" ".join(argv[3:]))
        out = write_agent(agent, Path("out") / argv[1])
        print(f"generated {out}")
        return 0
    if cmd == "demo":
        adapter = StubAdapter()
        print(adapter.complete([{"role": "user", "content": "hello clawbee"}])["content"])
        return 0
    print(f"unknown command: {cmd}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
