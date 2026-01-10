from __future__ import annotations

from pathlib import Path
import sys


ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from scripts import ci_guardrails


def main() -> None:
    """يوجه التنفيذ إلى الماسح المركزي للحواجز المعمارية."""
    raise SystemExit(ci_guardrails.main())


if __name__ == "__main__":
    main()
