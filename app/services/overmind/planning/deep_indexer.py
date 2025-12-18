"""
Ultra Deep Structural / Semantic-Oriented Indexer (Enhanced v2) - FACADE LAYER
==============================================================================
هذا الملف الآن يعمل كواجهة (Facade) فقط. تم نقل المنطق الفعلي إلى `app.services.overmind/planning/deep_indexer_v2/`
لتحقيق مبادئ "النظافة البرمجية" (Clean Code) و "فصل المسؤوليات" (Separation of Concerns).

يحافظ على التوافق الخلفي مع:
    - build_index(root=".")
    - summarize_for_prompt(index: dict, max_len: int = ...)
"""

from app.services.overmind.planning.deep_indexer_v2 import build_index, summarize_for_prompt

# Re-export helpers if needed by other modules (though ideally they should not be used directly)
__all__ = ["build_index", "summarize_for_prompt"]

if __name__ == "__main__":
    import argparse
    import json

    # Simple CLI wrapper around the new core
    ap = argparse.ArgumentParser(description="Ultra Deep Indexer v2 (Modular)")
    ap.add_argument("--root", default=".", help="Root directory")
    ap.add_argument("--summary", action="store_true", help="Print summary only")
    ap.add_argument("--json", action="store_true", help="Print full JSON (truncated)")
    ap.add_argument("--max-len", type=int, default=6000)
    args = ap.parse_args()

    idx = build_index(args.root)
    if args.summary:
        print("---- PROMPT SUMMARY ----")
        print(summarize_for_prompt(idx, max_len=args.max_len))
    if args.json:
        raw = json.dumps(idx, ensure_ascii=False)
        print("---- JSON (TRUNCATED 12000) ----")
        print(raw[:12000])
    if not args.summary and not args.json:
        print(
            f"Scanned: {idx['files_scanned']} files | Functions: {idx['global_metrics']['total_functions']}"
        )
        print(summarize_for_prompt(idx, max_len=2000))
