import argparse
import json
from pathlib import Path

from app.core.config import Settings
from app.main import create_app


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate the public API contract.")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    destination = Path(__file__).resolve().parents[3] / "docs" / "openapi.json"
    payload = json.dumps(create_app(Settings()).openapi(), indent=2, sort_keys=True) + "\n"
    if args.check:
        if not destination.exists() or destination.read_text(encoding="utf-8") != payload:
            raise SystemExit("OpenAPI contract drift detected.")
        print("OpenAPI contract is current.")
    else:
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(payload, encoding="utf-8", newline="\n")
        print("Generated public OpenAPI contract.")


if __name__ == "__main__":
    main()
