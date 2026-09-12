"""Verify the local CI container through its HTTP boundary; no provider key."""

import json
import time
import urllib.error
import urllib.request
import uuid

BASE = "http://127.0.0.1:8001"


def main() -> None:
    ready = False
    for _ in range(30):
        try:
            with urllib.request.urlopen(BASE + "/api/v1/health/ready", timeout=2) as response:
                ready = json.load(response)["status"] == "ready"
                if ready:
                    break
        except (urllib.error.URLError, TimeoutError):
            time.sleep(1)
    if not ready:
        raise SystemExit("Container did not become ready.")
    payload = {
        "rawNotes": "Completed the fictional lantern page; plan to inspect the compass layout.",
        "styleProfile": {
            "id": "concise-bullets", "label": "Concise bullets", "layout": "bullets",
            "verbosity": "brief", "tone": "direct",
            "headers": {"yesterday": "Yesterday", "today": "Today", "blockers": "Blockers"},
            "preferredMaxItemsPerSection": 5,
        },
        "clientRequestId": str(uuid.uuid4()),
    }
    request = urllib.request.Request(BASE + "/api/v1/generate", data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(request, timeout=12) as response:
        result = json.load(response)
        if response.headers.get("Cache-Control") != "no-store":
            raise SystemExit("Container response is cacheable.")
    if result["engineVersion"] != "rules-fallback-v1" or not result["draft"]["yesterday"]:
        raise SystemExit("Container no-key fallback smoke failed.")
    print("Container readiness, no-store and no-key generation passed.")


if __name__ == "__main__":
    main()
