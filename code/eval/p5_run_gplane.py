#!/usr/bin/env python3
"""G-plane driver: context-pack (G1), pure-trust (G2), and scarcity (G3) agent
policies, run on the pre-registered slice of SWE-bench Verified (see
docs/plans/2026-07-13-g-plane-design.md, BINDING).

Slice = the first 100 instance_ids in sorted order (pre-declared, no
cherry-picking). Controls (G0-fusion, G0-vanilla) are REUSED from P5 -- already
graded on these instances, not re-run here.

Usage:
  python p5_run_gplane.py --arm pack            [--chunk 20] [--stop-usd 300]
  python p5_run_gplane.py --arm trust           ...
  python p5_run_gplane.py --arm scarce-fusion   ...
  python p5_run_gplane.py --arm scarce-vanilla  ...
  python p5_run_gplane.py --arm pack --limit 1  # smoke: first instance of the slice only

Copies the p5_run_verified.py pattern: chunks of instance ids through
swe_bench.py predict with --resume (interruption-safe), sums actual $ from each
chunk's transcripts (claude stream-json result.total_cost_usd), logs a
checkpoint per chunk, and refuses to start the next chunk if cumulative +
projected > --stop-usd.
Markers: [chunk] / [checkpoint] / [STOP-BUDGET] / [arm-done] for a monitor.
"""
from __future__ import annotations
import argparse, json, os, subprocess, sys
from pathlib import Path

HERE = Path(__file__).parent
INSTANCES = Path(r"work/p5/instances_verified.json")  # MUST live on E: — predict derives its checkout dir from subset.parent, and git clone --local cannot hardlink across drives
OUTDIR = Path(r"work/p5")
ENDPOINT_FUSION = "http://127.0.0.1:8083"
SLICE_N = 100  # pre-registered: first 100 sorted instance_ids (--slice-n extends it;
               # the EXTENSION to n=500 is a disclosed power correction, not a new arm:
               # the underpowered n=83 result stands as reported, this adds instances)

# arm -> (g_plane, mode). mode only matters for scarce-* (pack/trust ignore it).
ARM_CONFIG = {
    "pack": ("pack", "rag"),
    "trust": ("trust", "rag"),
    "scarce-fusion": ("scarce", "rag"),
    "scarce-vanilla": ("scarce", "vanilla"),
    # CONTROL: identical policy to `pack`, but the pack is built by the
    # lexical/BM25 arm alone -- isolates "is the win the POLICY or OUR RETRIEVER?"
    "weakpack": ("weakpack", "rag"),
}


def transcript_cost(outdir: Path, iid: str, label: str) -> float:
    p = outdir / f"{iid}_{label}.stream.jsonl"
    try:
        for line in reversed(p.read_text(encoding="utf-8", errors="replace").splitlines()):
            if '"total_cost_usd"' in line:
                return float(json.loads(line).get("total_cost_usd") or 0.0)
    except Exception:
        pass
    return 0.0


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    ap = argparse.ArgumentParser()
    ap.add_argument("--arm", choices=list(ARM_CONFIG), required=True)
    ap.add_argument("--chunk", type=int, default=20)
    ap.add_argument("--stop-usd", type=float, default=300.0)
    ap.add_argument("--budget", type=float, default=1.5)
    ap.add_argument("--concurrency", type=int, default=3)
    ap.add_argument("--model", default="claude-sonnet-5")
    ap.add_argument("--cache-dir", default="", help="dir holding <repo>.cache clones (default: swe_bench.py's Verified WORK)")
    ap.add_argument("--ids", nargs="*", default=None, help="override the pre-registered slice with explicit instance_ids")
    ap.add_argument("--slice-n", type=int, default=SLICE_N,
                    help="extend the pre-registered slice (disclosed power correction)")
    ap.add_argument("--limit", type=int, default=0,
                    help="truncate the pre-registered slice to its first N ids (smoke tests, e.g. --limit 1)")
    args = ap.parse_args()

    g_plane, mode = ARM_CONFIG[args.arm]

    cells = json.loads(INSTANCES.read_text(encoding="utf-8"))
    # Pre-declared, binding slice: first 100 instance_ids in sorted order (no
    # cherry-picking; covers astropy -> django per the design doc).
    slice_ids = sorted(c["instance_id"] for c in cells)[:args.slice_n]
    ids = args.ids or slice_ids
    if args.limit:
        ids = ids[:args.limit]
    label = f"g_{args.arm}"
    out = OUTDIR / f"preds_{label}.jsonl"
    OUTDIR.mkdir(parents=True, exist_ok=True)

    env = dict(os.environ, SWE_CLAUDE_MODEL=args.model)
    total = 0.0
    done_ct = 0
    for i in range(0, len(ids), args.chunk):
        chunk = ids[i:i + args.chunk]
        print(f"[chunk] {label} {i}-{i+len(chunk)-1} of {len(ids)}", flush=True)
        cmd = [sys.executable, str(HERE / "swe_bench.py"), "predict",
               "--subset", str(INSTANCES),
               "--mode", mode, "--g-plane", g_plane, "--label", label, "--out", str(out),
               "--budget", str(args.budget), "--concurrency", str(args.concurrency),
               "--resume", "--ref-mode", "instance", "--ids", ",".join(chunk)]
        if args.cache_dir:
            cmd += ["--cache-dir", args.cache_dir]
        if args.arm != "scarce-vanilla":  # vanilla ignores --endpoint entirely; only pass it where it matters
            cmd += ["--endpoint", ENDPOINT_FUSION]
        r = subprocess.run(cmd, env=env, cwd=str(HERE.parent.parent))
        if r.returncode != 0:
            print(f"[FAIL] chunk rc={r.returncode} — resumable, rerun this driver", flush=True)
            return 1
        chunk_cost = sum(transcript_cost(OUTDIR / "predict", iid, label) for iid in chunk)
        total += chunk_cost
        done_ct += len(chunk)
        projected = total / max(1, done_ct) * len(ids)
        print(f"[checkpoint] {label} done={done_ct}/{len(ids)} chunk=${chunk_cost:.2f} "
              f"cum=${total:.2f} projected=${projected:.2f}", flush=True)
        if total + (total / max(1, done_ct)) * args.chunk > args.stop_usd:
            print(f"[STOP-BUDGET] cum=${total:.2f} would exceed ${args.stop_usd} — halting; "
                  f"resume with a raised --stop-usd after review", flush=True)
            return 2
    print(f"[arm-done] {label} n={done_ct} cum=${total:.2f}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
