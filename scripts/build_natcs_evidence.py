from __future__ import annotations

import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    subprocess.run(["node", "scripts/build_natcs_evidence.mjs"], cwd=ROOT, check=True)


if __name__ == "__main__":
    main()
