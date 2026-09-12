"""Scan publishable repository files; confidential reference comparison is optional."""

import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def git(*args: str) -> bytes:
    return subprocess.check_output(["git", "-C", str(ROOT), *args])


def scan(private_input: Path | None = None) -> dict[str, object]:
    names = sorted(set(git("ls-files", "--cached", "--others", "--exclude-standard", "-z").decode().split("\0")) - {""})
    failures: list[dict[str, str]] = []
    private_hashes: set[str] = set()
    private_names: set[str] = set()
    private_prose: set[str] = set()
    private_count = 0
    if private_input is not None:
        for source in private_input.glob("*.md"):
            private_count += 1
            private_names.add(source.name)
            content = source.read_bytes()
            private_hashes.add(hashlib.sha256(content).hexdigest())
            for line in content.decode("utf-8-sig").splitlines():
                normalized = " ".join(line.split())
                if len(normalized) >= 140:
                    private_prose.add(normalized)
    inspected = 0
    for name in names:
        path = ROOT / name
        if not path.is_file():
            continue
        inspected += 1
        if path.name == ".env" or (path.name.startswith(".env.") and path.name != ".env.example"):
            failures.append({"path": name, "finding": "environment-file"})
        if path.suffix in {".pem", ".key", ".pt", ".pth", ".safetensors"}:
            failures.append({"path": name, "finding": "excluded-secret-or-model-artifact"})
        data = path.read_bytes()
        if path.name in private_names or hashlib.sha256(data).hexdigest() in private_hashes:
            failures.append({"path": name, "finding": "private-reference-file"})
        text = data.decode("utf-8", errors="replace")
        normalized_text = " ".join(text.split())
        if private_input is not None and any(part in text for part in (str(private_input), str(private_input).replace("\\", "/"))):
            failures.append({"path": name, "finding": "private-reference-path"})
        if any(line in normalized_text for line in private_prose):
            failures.append({"path": name, "finding": "private-reference-prose"})
        if re.search(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----", text):
            failures.append({"path": name, "finding": "private-key"})
    commits = int(git("rev-list", "--all", "--count").strip() or b"0")
    history_blobs = 0
    if private_input is not None and commits:
        for line in git("rev-list", "--objects", "--all").decode().splitlines():
            object_id, _, name = line.partition(" ")
            if git("cat-file", "-t", object_id).strip() != b"blob":
                continue
            history_blobs += 1
            data = git("cat-file", "blob", object_id)
            text = " ".join(data.decode("utf-8", errors="replace").split())
            if Path(name).name in private_names or hashlib.sha256(data).hexdigest() in private_hashes or any(part in text for part in private_prose):
                failures.append({"path": name or object_id, "finding": "private-reference-in-history"})
    return {
        "filesInspected": inspected,
        "commitsInspected": commits,
        "historyBlobsInspected": history_blobs,
        "privateReferenceCount": private_count,
        "privateReferenceComparison": "pass" if private_input is not None and not failures else ("fail" if private_input is not None else "not_run_private_inputs_not_available"),
        "failures": failures,
        "result": "pass" if not failures else "fail",
        "limitations": "Exact files, names, private source paths and long verbatim prose are checked; this is not a proof against all possible paraphrases or covert encodings.",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--private-input", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = scan(args.private_input)
    serialized = json.dumps(result, indent=2) + "\n"
    if args.output:
        destination = args.output.resolve()
        if not destination.is_relative_to(ROOT):
            raise ValueError("Report destination must be inside the repository.")
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(serialized, encoding="utf-8")
    print(serialized)
    raise SystemExit(0 if result["result"] == "pass" else 1)


if __name__ == "__main__":
    main()
