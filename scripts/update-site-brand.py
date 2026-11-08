#!/usr/bin/env python3
"""Refresh the site's explicit Studio selection; refuse unrecorded byte drift."""
import argparse
import hashlib
import json
from pathlib import Path
import tempfile

ROOT = Path(__file__).resolve().parents[1]
RECEIPT = ROOT / "docs/site-brand.json"
RANGES = [(0x20, 0xFF), (0x100, 0x24F), (0x2000, 0x206F), (0x2190, 0x21FF), (0x2212, 0x2212), (0x25A0, 0x25A0)]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("studio", type=Path, help="subcult-tv checkout at the receipt's revision")
    args = parser.parse_args()
    receipt = json.loads(RECEIPT.read_text())
    # Check the entire selection before writing any destination.
    for item in receipt["files"]:
        source = args.studio / item["source"]
        target = ROOT / item["target"]
        if sha(source) != item["source_sha256"]:
            raise SystemExit(f"Studio source drift: {source}")
        if target.exists() and sha(target) != item["sha256"]:
            raise SystemExit(f"Product destination drift: {target}")
    with tempfile.TemporaryDirectory(prefix="tmux-site-brand-") as work:
        staged = []
        for number, item in enumerate(receipt["files"]):
            source = args.studio / item["source"]
            output = Path(work) / str(number)
            if item["transform"] == "copy":
                output.write_bytes(source.read_bytes())
            else:
                import fontTools
                import brotli
                from fontTools import subset
                from fontTools.ttLib import TTFont
                if fontTools.__version__ != receipt["font_tools"] or brotli.__version__ != receipt["brotli"]:
                    raise SystemExit("Use the fontTools and Brotli versions recorded in docs/site-brand.json")
                font = TTFont(source, recalcTimestamp=False)
                family, style = item["family"], item["style"]
                postscript = family.replace(" ", "") + "-" + style
                names = {1: family, 2: style, 3: postscript + "-20261108", 4: family + " " + style,
                         6: postscript, 16: family, 17: style}
                for record in font["name"].names:
                    if record.nameID in names:
                        record.string = names[record.nameID].encode(record.getEncoding())
                options = subset.Options(layout_features=["*"], name_IDs=["*"], name_legacy=True,
                                         name_languages=["*"], recalc_timestamp=False)
                subsetter = subset.Subsetter(options=options)
                subsetter.populate(unicodes=[c for start, end in RANGES for c in range(start, end + 1)])
                subsetter.subset(font)
                font.flavor = "woff2"
                font.save(output)
            if item["sha256"] and sha(output) != item["sha256"]:
                raise SystemExit(f"Rebuilt output differs: {item['target']}")
            staged.append((output, ROOT / item["target"]))
        for source, target in staged:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(source.read_bytes())
    print(f"Refreshed {len(staged)} selected site assets")


if __name__ == "__main__":
    main()
