"""Export the API contract to docs/shipment/openapi.json. Run: python -m dev.export_openapi"""
import json
from pathlib import Path

from app.container import Container
from app.core.config import Settings
from app.main import create_app

OUTPUT = Path(__file__).resolve().parents[3] / "docs" / "shipment" / "openapi.json"

if __name__ == "__main__":
    app = create_app(Container(Settings(jwt_secret="unused", internal_api_key="unused")), run_workers=False)
    OUTPUT.write_text(json.dumps(app.openapi(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
