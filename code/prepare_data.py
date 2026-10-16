"""One-time setup for the analysis scripts. Run from the package root:

    python code/prepare_data.py

1. Decompresses every data/**/*.gz next to itself (the .gz is kept), so scripts can read plain files.
2. Builds work/p5/: a flat view of the SWE-bench Verified files (inputs, packs, predictions, raw responses,
   summary grading reports, auxiliary files) plus the trimmed-breadth arm files and the single-retriever
   replication (B1-B3) files. Several analysis scripts
   were written against one flat run directory; they read `work/p5/<file>`.

Nothing in data/ is modified apart from adding the decompressed copies. work/ can be deleted at any time.
"""
import gzip
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
WORK = ROOT / "work" / "p5"

n_gz = 0
for gz in sorted(DATA.rglob("*.gz")):
    if gz.name.endswith(".tar.gz"):
        continue
    out = gz.with_suffix("")
    if not out.exists():
        with gzip.open(gz, "rb") as fi, open(out, "wb") as fo:
            shutil.copyfileobj(fi, fo)
        n_gz += 1

WORK.mkdir(parents=True, exist_ok=True)
FLAT_DIRS = [
    "swe-verified/inputs", "swe-verified/packs", "swe-verified/predictions", "swe-verified/raw_responses",
    "swe-verified/grading/summary", "swe-verified/auxiliary",
    "trimmed-breadth/packs", "trimmed-breadth/predictions", "trimmed-breadth/raw_responses",
    "trimmed-breadth/grading/summary", "trimmed-breadth/build",
    "b1b3-replication",
]
n = 0
for d in FLAT_DIRS:
    for f in sorted((DATA / d).iterdir()):
        if f.is_file() and not f.name.endswith(".gz"):
            dst = WORK / f.name
            if not dst.exists():
                shutil.copy2(f, dst)
                n += 1
print(f"decompressed {n_gz} files; work/p5 now has {sum(1 for _ in WORK.iterdir())} files ({n} added)")
