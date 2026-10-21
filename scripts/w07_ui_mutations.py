"""Prove the React rollback and concurrent-response guards, restoring exact source bytes."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "report/w07-evidence"
SOURCE = ROOT / "src/web/frontend/src/Roadmap.tsx"


def main():
    original = SOURCE.read_bytes()
    source = original.decode("utf-8").replace("\r\n", "\n")
    rollback = [line for line in source.splitlines() if "setNodeState(current" in line and "[nodeId]: previous" in line]
    assert len(rollback) == 1
    assert source.count("[nodeId]: confirmed") == 1
    cases = [
        ("rollback", source.replace(rollback[0], "      // Deliberately broken: retain optimistic state after failure."),
         "optimistically updates one concept and restores only that checkbox when its request fails"),
        ("stale-snapshot", source.replace("[nodeId]: confirmed", "...response.nodes"),
         "merges concurrent node responses by their own node so stale full snapshots cannot undo another check"),
    ]
    results = []
    for label, broken, name in cases:
        xml = OUTPUT / f"ui-{label}-red.xml"
        command = ["cmd.exe", "/c", "npm.cmd", "--prefix", "src/web/frontend", "test", "--",
                   "--pool=threads", "--maxWorkers=1", "src/Roadmap.test.tsx", "-t", name,
                   "--reporter=default", "--reporter=junit", f"--outputFile={xml}"]
        try:
            SOURCE.write_bytes(broken.encode("utf-8"))
            with (OUTPUT / f"ui-{label}-red.log").open("w", encoding="utf-8") as log:
                result = subprocess.run(command, cwd=ROOT, stdout=log, stderr=log)
            tree = ET.parse(xml)
            failures, errors = list(tree.iter("failure")), list(tree.iter("error"))
            assert result.returncode == 1 and len(failures) == 1 and not errors, (label, result.returncode)
        finally:
            SOURCE.write_bytes(original)
            assert SOURCE.read_bytes() == original
        results.append({"label": label, "command": command, "native_exit_code": result.returncode,
                        "assertion_failures": len(failures), "setup_errors": len(errors),
                        "source_sha256": hashlib.sha256(original).hexdigest(), "source_restored": True})
    (OUTPUT / "ui-mutations.json").write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
