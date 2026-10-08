"""Non-blocking release-readiness report for VN SME Ledger.

The report makes incomplete legal, workflow, and verification evidence visible
to the product owner. It intentionally does not block local or distribution
builds; passing tests and legal certification remain separate statements.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


MANIFEST_PATH = Path(__file__).with_name("release_readiness.json")


def evaluate_readiness(path: Path = MANIFEST_PATH) -> tuple[bool, list[str]]:
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return False, [f"Cannot read release manifest: {exc}"]

    errors: list[str] = []
    status = manifest.get("status")
    if status == "ADVISORY":
        errors.append("Readiness status is ADVISORY; certification evidence is incomplete.")
    elif status != "READY_FOR_BUILD":
        errors.append(
            f"Readiness status is {status or '<missing>'}; "
            "use ADVISORY or READY_FOR_BUILD."
        )

    checks = manifest.get("required_checks")
    if not isinstance(checks, dict) or not checks:
        errors.append("required_checks is missing or empty.")
    else:
        errors.extend(
            f"Required check is not green: {name}"
            for name, passed in checks.items()
            if passed is not True
        )

    blockers = manifest.get("blockers", [])
    if blockers:
        errors.append(f"Open blockers: {len(blockers)}")
    if not manifest.get("release_evidence"):
        errors.append("release_evidence is empty.")
    return not errors, errors


def main() -> int:
    ready, errors = evaluate_readiness()
    if ready:
        print("RELEASE READINESS: all listed checks are evidenced.")
    else:
        print("RELEASE READINESS ADVISORY: build is permitted; certification evidence is incomplete.")
        for error in errors:
            print(f"- {error}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
