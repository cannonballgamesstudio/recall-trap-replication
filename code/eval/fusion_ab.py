#!/usr/bin/env python3
"""Fusion vs Srclight A/B — pure retrieval through the RetrievalBackend PORT.

Unlike retrieval_recall.py (which reads srclight's index layout directly), this
drives BOTH backends through their public query() with matched config
(instruct ON, file-dedup ON, mode=hybrid), so the comparison includes each
backend's own tokenization/fusion/dedup pipeline — i.e. it measures what retrievald
would actually serve.

Usage:
  python fusion_ab.py --bench homunc [--k 10] [--build] [--limit-queries N]
  python fusion_ab.py --bench swe    [--k 10] [--build] [--repos django/django ...]

--build: build missing indexes for BOTH arms from the same worktree state with the
same srclight version — fusion into <EVAL_ROOT>/fusion_idx/<slug>, srclight into
<EVAL_ROOT>/srclight_idx/<slug>. (The worktrees' old .srclight indexes were built by an
older srclight with different file coverage — 573 vs 521 files on private-repo —
which confounds the A/B; both arms must share one corpus.) Needs :8080.
"""
from __future__ import annotations
import argparse, hashlib, json, os, random, sqlite3, sys, time
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

os.environ.setdefault("OPENAI_BASE_URL", "http://127.0.0.1:8080")
os.environ.setdefault("OPENAI_API_KEY", "sk-noauth")

EMBED_MODEL = "openai:Qwen/Qwen3-Embedding-8B"
DIMS = 4096
REGISTRY = r"<EVAL_ROOT>\registry.db"
FUSION_IDX_ROOT = Path(r"<EVAL_ROOT>\fusion_idx")
SRCL_IDX_ROOT = Path(r"<EVAL_ROOT>\srclight_idx")
MAXQ = 6000          # same query-char cap retrieval_recall.py used (both arms)
BOOT = 10_000


def worktree(repo: str) -> str | None:
    con = sqlite3.connect(f"file:{REGISTRY}?mode=ro", uri=True)
    row = con.execute("SELECT worktree FROM refs WHERE repo=? AND status='ready' "
                      "ORDER BY (ref='eval') DESC LIMIT 1", (repo,)).fetchone()
    con.close()
    return row[0] if row else None


def queries_for(bench):
    if bench == "homunc":
        from private_repo_flood import QUERIES
        return [("[anonymized-org]/private-repo", n, q, g) for (n, q, g) in QUERIES]
    subset = {"swe": r"<EVAL_ROOT>\swebench-verified\subset.json",
              "ml": r"<EVAL_ROOT>\swebench-ml\subset.json"}[bench]
    cells = json.loads(Path(subset).read_text(encoding="utf-8"))
    return [(c["repo"], c["instance_id"], c["problem_statement"], c["gold_files"]) for c in cells]


def norm(p: str) -> str:
    return (p or "").replace("\\", "/").lstrip("./").lower()


def metrics(files: list[str], gold: list[str], k: int) -> dict:
    g = {norm(x) for x in gold}
    fs = [norm(f) for f in files][:k]
    hits_at = lambda kk: len(g & set(fs[:kk])) / len(g) if g else 0.0
    mrr = 0.0
    for i, f in enumerate(fs):
        if f in g:
            mrr = 1.0 / (i + 1)
            break
    rec = hits_at(k)
    prec = (len(g & set(fs)) / len(fs)) if fs else 0.0
    f1 = (2 * prec * rec / (prec + rec)) if (prec + rec) > 0 else 0.0
    return {"r1": hits_at(1), "r3": hits_at(3), "r5": hits_at(5), f"r{k}": hits_at(k),
            "mrr": mrr, f"p{k}": prec, "f1": f1}


def backends():
    from ragfusion.srclight_backend import SrclightBackend, DEFAULT_QUERY_INSTRUCT
    from ragfusion.fusion.fusion_backend import FusionBackend
    srcl = SrclightBackend(embed_model=EMBED_MODEL, dims=DIMS,
                           query_instruct=DEFAULT_QUERY_INSTRUCT, dedup_file=True)
    fus = FusionBackend(embed_model=EMBED_MODEL, dims=DIMS,
                        query_instruct=DEFAULT_QUERY_INSTRUCT, dedup_file=True)
    return srcl, fus


def slug(repo: str) -> str:
    return repo.replace("/", "__")


def config_digest(kwargs: dict) -> str:
    clean = {k: v for k, v in sorted(kwargs.items()) if k != "provider_factory"}
    return hashlib.sha1(json.dumps(clean, default=str).encode("utf-8")).hexdigest()[:8]


def ensure_index(be, arm: str, root: Path, repo: str, wt: str, done_marker: str) -> Path:
    d = root / slug(repo)
    if (d / done_marker).exists():
        return d
    print(f"[build] {arm} index for {repo} -> {d}", flush=True)
    t0 = time.time()
    res = be.index(wt, str(d))
    print(f"[build] {arm} {repo}: {res.symbols} symbols, {res.files_indexed} files "
          f"in {time.time()-t0:.0f}s", flush=True)
    return d


def paired_bootstrap(deltas: list[float]) -> tuple[float, float, float]:
    """mean delta, 95% CI low/high via percentile bootstrap."""
    rng = random.Random(13)
    n = len(deltas)
    means = []
    for _ in range(BOOT):
        s = [deltas[rng.randrange(n)] for _ in range(n)]
        means.append(sum(s) / n)
    means.sort()
    return sum(deltas) / n, means[int(0.025 * BOOT)], means[int(0.975 * BOOT)]


def run_pairs(arm_specs, qs, k: int) -> list[dict]:
    """arm_specs: [(label, backend, {repo: index_dir})] x2. Paired rows; a query
    is skipped unless BOTH arms have an index for its repo."""
    (la, be_a, idx_a), (lb, be_b, idx_b) = arm_specs
    rows = []
    for repo, name, text, gold in qs:
        if repo not in idx_a or repo not in idx_b:
            continue
        text = text[:MAXQ]
        row = {"repo": repo, "name": name, "gold": gold}
        for arm, be, idx in ((la, be_a, idx_a[repo]), (lb, be_b, idx_b[repo])):
            t0 = time.time()
            try:
                hits = be.query(idx, repo, "eval", text, mode="hybrid", limit=k)
                files = [h.file for h in hits]
                row[arm] = metrics(files, gold, k)
                row[arm]["ms"] = int((time.time() - t0) * 1000)
                row[arm]["files"] = [norm(f) for f in files]
            except Exception as e:
                row[arm] = {"error": f"{type(e).__name__}: {e}"}
                print(f"[err] {arm} {name}: {e}", flush=True)
        rows.append(row)
        a, b = row.get(la, {}), row.get(lb, {})
        if "error" not in a and "error" not in b:
            print(f"[{len(rows)}/{len(qs)}] {name[:40]:40s} "
                  f"r@{k} a={a[f'r{k}']:.2f} b={b[f'r{k}']:.2f}  "
                  f"mrr a={a['mrr']:.2f} b={b['mrr']:.2f}", flush=True)
    return rows


def summarize(rows, label_a: str, label_b: str, k: int) -> dict:
    ok = [r for r in rows
          if "error" not in r.get(label_a, {}) and "error" not in r.get(label_b, {})]
    if not ok:
        print("no successful paired queries")
        return {}
    print(f"\n=== A={label_a}  B={label_b}  (n={len(ok)} paired queries, k={k}) ===")
    out = {}
    kk = f"r{k}"
    for m in ("r1", "r3", "r5", kk, "mrr", f"p{k}", "f1"):
        av = sum(r[label_a][m] for r in ok) / len(ok)
        bv = sum(r[label_b][m] for r in ok) / len(ok)
        deltas = [r[label_b][m] - r[label_a][m] for r in ok]
        mean, lo, hi = paired_bootstrap(deltas)
        sig = "*" if (lo > 0 or hi < 0) else " "
        print(f"{m:>5}: A {av:.3f}  B {bv:.3f}  delta {mean:+.3f} "
              f"[{lo:+.3f},{hi:+.3f}] {sig}")
        out[m] = (av, bv, mean, lo, hi)
    ams = sorted(r[label_a]["ms"] for r in ok)[len(ok) // 2]
    bms = sorted(r[label_b]["ms"] for r in ok)[len(ok) // 2]
    print(f"median query ms: A {ams}  B {bms}")
    return out


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    ap = argparse.ArgumentParser()
    ap.add_argument("--bench", choices=["homunc", "swe", "ml"], required=True)
    ap.add_argument("--k", type=int, default=10)
    ap.add_argument("--build", action="store_true")
    ap.add_argument("--repos", nargs="*", default=None)
    ap.add_argument("--limit-queries", type=int, default=None)
    ap.add_argument("--out", default=None)
    ap.add_argument("--w-lex", type=float, default=1.0,
                    help="fusion lexical arm weight (const mode / unanchored)")
    ap.add_argument("--lex-mode", choices=["ids", "full", "off"], default="full",
                    help="fusion lexical mode (P1 parity default: full)")
    ap.add_argument("--lex-ids", action="store_true",
                    help="alias for --lex-mode ids (locked-protocol continuity)")
    ap.add_argument("--w-graph", type=float, default=0.0)
    ap.add_argument("--w-trigram", type=float, default=0.0)
    ap.add_argument("--w-prior", type=float, default=0.0)
    ap.add_argument("--vs-idx-root", default=None,
                    help="fusion-vs-fusion: arm B reads <root>/<slug> instead of "
                         "<EVAL_ROOT>/fusion_idx (same backend config unless --vs-config)")
    ap.add_argument("--vs-backend", default="fusion", choices=["fusion", "summary"],
                    help="arm-B backend class: 'summary' = SummaryViewBackend overlay "
                         "(dense_sum arm over fusion_emb_sum.npy; pass w_sum via --vs-config)")
    ap.add_argument("--vs-config", default=None,
                    help="JSON dict of FusionBackend kwarg overrides for arm B "
                         "(activates vs mode even without --vs-idx-root)")
    args = ap.parse_args()

    vs_mode = bool(args.vs_idx_root or args.vs_config)
    if vs_mode and args.build:
        sys.exit("--build is not supported in vs mode; build variant indexes with "
                 "their own build script (e.g. scripts/eval/build_hdr_variant.py)")

    qs = queries_for(args.bench)
    if args.repos:
        qs = [q for q in qs if q[0] in set(args.repos)]
    if args.limit_queries:
        qs = qs[: args.limit_queries]

    repos = sorted({q[0] for q in qs})
    if not vs_mode:
        srcl, fus = backends()
        src_idx: dict[str, str] = {}
        fus_idx: dict[str, str] = {}
        for repo in repos:
            wt = worktree(repo)
            if not wt:
                print(f"[skip] no ready worktree for {repo}")
                continue
            if args.build:
                src_idx[repo] = str(ensure_index(srcl, "srclight", SRCL_IDX_ROOT, repo, wt,
                                                 "index.db"))
                fus_idx[repo] = str(ensure_index(fus, "fusion", FUSION_IDX_ROOT, repo, wt,
                                                 "fusion_emb.npy"))
            else:
                sd = SRCL_IDX_ROOT / slug(repo)
                fd = FUSION_IDX_ROOT / slug(repo)
                if (sd / "index.db").exists() and (fd / "fusion.db").exists():
                    src_idx[repo] = str(sd)
                    fus_idx[repo] = str(fd)
                else:
                    print(f"[skip] missing built indexes for {repo} (run with --build)")

    if vs_mode:
        from ragfusion.fusion.fusion_backend import FusionBackend
        from ragfusion.srclight_backend import DEFAULT_QUERY_INSTRUCT
        lex_mode = "ids" if args.lex_ids else args.lex_mode
        base_kwargs = dict(embed_model=EMBED_MODEL, dims=DIMS,
                           query_instruct=DEFAULT_QUERY_INSTRUCT, dedup_file=True,
                           lex_mode=lex_mode, w_lex=args.w_lex, w_graph=args.w_graph,
                           w_trigram=args.w_trigram, w_prior=args.w_prior)
        overrides = json.loads(args.vs_config) if args.vs_config else {}
        root_a = FUSION_IDX_ROOT
        root_b = Path(args.vs_idx_root) if args.vs_idx_root else FUSION_IDX_ROOT
        if root_a == root_b and not overrides:
            sys.exit("vs mode: identical index root AND identical config — nothing to compare")
        be_a = FusionBackend(**base_kwargs)
        if args.vs_backend == "summary":
            from summary_view_backend import SummaryViewBackend
            be_b = SummaryViewBackend(**{**base_kwargs, **overrides})
        else:
            be_b = FusionBackend(**{**base_kwargs, **overrides})
        label_a = f"fusion@{root_a.name}#{config_digest(base_kwargs)}"
        label_b = f"fusion@{root_b.name}#{config_digest({**base_kwargs, **overrides})}"
        idx_a, idx_b = {}, {}
        for repo in repos:
            da, db_ = root_a / slug(repo), root_b / slug(repo)
            if (da / "fusion.db").exists() and (db_ / "fusion.db").exists():
                idx_a[repo], idx_b[repo] = str(da), str(db_)
            else:
                print(f"[skip] {repo}: missing fusion.db (A={da} exists={ (da/'fusion.db').exists() }, "
                      f"B={db_} exists={ (db_/'fusion.db').exists() })")
        arm_specs = [(label_a, be_a, idx_a), (label_b, be_b, idx_b)]
    else:
        # fusion backend: constructed once, directly from the CLI flags (P2 — the
        # backend owns lex_mode/w_graph pipeline; the harness no longer duplicates it).
        from ragfusion.fusion.fusion_backend import FusionBackend
        from ragfusion.srclight_backend import DEFAULT_QUERY_INSTRUCT
        lex_mode = "ids" if args.lex_ids else args.lex_mode
        fus_q = FusionBackend(embed_model=EMBED_MODEL, dims=DIMS,
                              query_instruct=DEFAULT_QUERY_INSTRUCT, dedup_file=True,
                              lex_mode=lex_mode, w_lex=args.w_lex, w_graph=args.w_graph,
                              w_trigram=args.w_trigram, w_prior=args.w_prior)
        arm_specs = [("srclight", srcl, src_idx), ("fusion", fus_q, fus_idx)]

    rows = run_pairs(arm_specs, qs, args.k)
    summary = summarize(rows, arm_specs[0][0], arm_specs[1][0], args.k)
    if not summary:
        return 1
    out = args.out or str(Path(r"<EVAL_ROOT>") /
                          (f"fusion_ab_vs_{args.bench}.json" if vs_mode
                           else f"fusion_ab_{args.bench}.json"))
    Path(out).write_text(json.dumps(rows, indent=1), encoding="utf-8")
    print(f"rows -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
