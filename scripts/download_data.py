import json
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCES = ROOT / "data" / "sources.json"
OUT_DIR = ROOT / "data" / "raw"


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    sources = json.loads(SOURCES.read_text(encoding="utf-8"))

    for item in sources:
        target = OUT_DIR / item["name"]
        if target.exists():
            print(f"Skipping {item['name']} (already downloaded)")
            continue
        print(f"Downloading {item['name']}...")
        request = urllib.request.Request(
            item["url"], headers={"User-Agent": "Mozilla/5.0"}
        )
        with urllib.request.urlopen(request) as response:
            target.write_bytes(response.read())

    print(f"Done. Files are in {OUT_DIR}")


if __name__ == "__main__":
    main()