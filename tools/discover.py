import json
import sys
from pathlib import Path

# اجعل روت المشروع على PYTHONPATH
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# الآن نقدر نستورد run.py
from run import app  # run.py يحتوي Flask app اسمه app  # noqa: E402

out = {}
reports = ROOT / "reports"
reports.mkdir(exist_ok=True)

with app.app_context():
    routes = []
    for rule in app.url_map.iter_rules():
        methods = sorted(m for m in rule.methods if m not in {"HEAD", "OPTIONS"})
        routes.append({"rule": str(rule), "endpoint": rule.endpoint, "methods": methods})
    out["routes"] = routes
    out["blueprints"] = sorted(app.blueprints.keys())

(reports / "api_routes.json").write_text(json.dumps(out, indent=2, ensure_ascii=False))
print("✅ wrote reports/api_routes.json")
