"""Served-pack coverage accounting, anchor-dose strata, pack-content failure classes, and the
gold-file-presence stratification (paper Sec. 5.3 BM25 corollary, Sec. 5.4, Table 'fail').

Gold lines = pre-image line ranges of the gold patch hunks (parse_gold_hunks; new files skipped).
A packed chunk spans [line, line + number of snippet lines) as rendered in the served pack text
("### path:line - symbol [kind]" followed by a fenced snippet).

Outputs results/coverage_per_instance.csv and results/coverage_anchor.md.
Run from the package root after build_inclusion_table.py.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from common import SV, RESULTS, ALL_IDS, load_inclusion, write_csv

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "eval"))
from oracle_pack import parse_gold_hunks  # noqa: E402

HDR = re.compile(r"^### (.+?):(\d+|\?) ")
GOLD = json.loads((SV / "inputs" / "gold_patches.json").read_text(encoding="utf-8"))


def norm(p):
    return p.replace("\\", "/").lower().lstrip("./")


def parse_pack(text: str):
    """-> list of (file, start, n_lines) chunks in served order."""
    chunks, cur, in_code, n = [], None, False, 0
    for line in text.splitlines():
        if not in_code:
            m = HDR.match(line)
            if m:
                cur = (norm(m.group(1)), int(m.group(2)) if m.group(2).isdigit() else 0)
                continue
            if line.startswith("```") and cur is not None:
                in_code, n = True, 0
                continue
        else:
            if line.startswith("```"):
                chunks.append((cur[0], cur[1], max(1, n)))
                in_code, cur = False, None
            else:
                n += 1
    return chunks


def pack_text(packs, iid, key):
    e = packs.get(iid)
    if e is None:
        return None
    if isinstance(e, str):
        return e
    if key in e:
        return e[key]["pack"] if isinstance(e[key], dict) else e[key]
    return e.get("pack")


def measure(text, iid):
    gold: dict[str, set[int]] = {}
    for path, start, length in parse_gold_hunks(GOLD[iid]):
        gold.setdefault(norm(path), set()).update(range(start, start + length))
    if not gold:
        return None
    chunks = parse_pack(text)
    files = {f for f, _, _ in chunks}
    covered_lines = set()
    file_cov = {g: False for g in gold}
    for f, s, n in chunks:
        if f in gold:
            hit = set(range(s, s + n)) & gold[f]
            if hit:
                file_cov[f] = True
                covered_lines |= {(f, x) for x in hit}
    n_gold_lines = sum(len(v) for v in gold.values())
    present = [g for g in gold if g in files]
    if not present:
        cls = "A_gold_absent"
    elif sum(file_cov.values()) < len(gold):
        cls = "B_present_lines_absent"
    else:
        cls = "C_lines_covered"
    return dict(any_gold_file=int(bool(present)), all_gold_files=int(len(present) == len(gold)),
                line_cov=len(covered_lines) / n_gold_lines, anchor_visible=int(bool(covered_lines)),
                pack_class=cls, distinct_files=len(files), n_chunks=len(chunks))


PACKSETS = {"fusion": "local_packs.json", "dense": "dense_packs.json", "bm25": "bm25_packs.json"}
ARMS_BY_PACK = {"fusion": ["P1_gpt_fusion", "P2_deepseek_fusion", "P3_qwen36_fusion_K12", "M1_qwen3coder30b_AC"],
                "dense": ["P4_DENSE1_gpt_dense"], "bm25": ["R1_gpt_bm25"]}


def main():
    tab = load_inclusion()
    rows, lines = [], ["# Served-pack coverage and anchor dose (recomputed)", ""]
    meas = {}
    for name, f in PACKSETS.items():
        packs = json.loads((SV / "packs" / f).read_text(encoding="utf-8"))
        for side in ("ON", "OFF"):
            for iid in ALL_IDS:
                t = pack_text(packs, iid, "dedup" + side)
                if t is None:
                    continue
                m = measure(t, iid)
                if m is None:
                    continue
                meas[(name, side, iid)] = m
                rows.append(dict(packs=name, side=side, instance_id=iid, **m))
    write_csv(RESULTS / "coverage_per_instance.csv", rows)

    lines += ["| packs | side | n | any-gold-file present | mean gold-line coverage | anchor-visible share | mean distinct files |",
              "|---|---|---|---|---|---|---|"]
    for name in PACKSETS:
        for side in ("ON", "OFF"):
            ms = [m for (p, s, _), m in meas.items() if p == name and s == side]
            if not ms:
                continue
            n = len(ms)
            lines.append(f"| {name} | {side} | {n} | {sum(m['any_gold_file'] for m in ms)/n:.3f} | "
                         f"{sum(m['line_cov'] for m in ms)/n:.3f} | {sum(m['anchor_visible'] for m in ms)/n:.3f} | "
                         f"{sum(m['distinct_files'] for m in ms)/n:.2f} |")

    lines += ["", "## Resolve rate by anchor stratum (oracle diagnostic)", "",
              "| arm | ON anchor-visible | ON anchor-absent | OFF anchor-visible | OFF anchor-absent | within-visible residual (OFF-ON) |",
              "|---|---|---|---|---|---|"]
    for name, arms in ARMS_BY_PACK.items():
        for arm in arms:
            out = []
            rates = {}
            for side in ("ON", "OFF"):
                st = tab.get((arm, side), {})
                for vis in (1, 0):
                    ids = [i for i in ALL_IDS if (name, side, i) in meas and meas[(name, side, i)]["anchor_visible"] == vis
                           and st.get(i, "never_predicted") != "never_predicted"]
                    r = sum(1 for i in ids if st[i] == "resolved") / max(1, len(ids))
                    rates[(side, vis)] = r
                    out.append(f"{100*r:.1f}% (n={len(ids)})")
            lines.append(f"| {arm} | " + " | ".join(out) + f" | {100*(rates[('OFF',1)]-rates[('ON',1)]):+.1f}pp |")

    # Table 'fail': gpt dedup-ON pack-content classes over graded instances (empties included, harness errors excluded)
    lines += ["", "## Pack-content failure classes, gpt-5.6-sol dedup-ON (Table 'fail')", ""]
    st = tab[("P1_gpt_fusion", "ON")]
    graded = [i for i in ALL_IDS if st[i] in ("resolved", "unresolved", "empty") and ("fusion", "ON", i) in meas]
    fails = [i for i in graded if st[i] != "resolved"]
    lines += [f"graded n={len(graded)}, failures={len(fails)}", "",
              "| class | n | resolve | share of failures | prevalence |", "|---|---|---|---|---|"]
    for cls in ("A_gold_absent", "B_present_lines_absent", "C_lines_covered"):
        ids = [i for i in graded if meas[("fusion", "ON", i)]["pack_class"] == cls]
        r = sum(1 for i in ids if st[i] == "resolved")
        fsh = sum(1 for i in fails if meas[("fusion", "ON", i)]["pack_class"] == cls)
        lines.append(f"| {cls} | {len(ids)} | {100*r/max(1,len(ids)):.1f}% | {100*fsh/max(1,len(fails)):.1f}% | {100*len(ids)/len(graded):.1f}% |")

    # Gold-file-presence stratification of gpt discordant pairs
    lines += ["", "## Gold-file presence among gpt-5.6-sol discordant pairs (fusion)", ""]
    on, off = tab[("P1_gpt_fusion", "ON")], tab[("P1_gpt_fusion", "OFF")]
    cats = {}
    for i in ALL_IDS:
        if ("fusion", "ON", i) not in meas or ("fusion", "OFF", i) not in meas:
            continue
        a, b = on[i] == "resolved", off[i] == "resolved"
        if a == b:
            continue
        pon, poff = meas[("fusion", "ON", i)]["any_gold_file"], meas[("fusion", "OFF", i)]["any_gold_file"]
        key = ("OFF-win" if b else "ON-win", {(1, 1): "both", (0, 0): "neither", (1, 0): "ON only", (0, 1): "OFF only"}[(pon, poff)])
        cats[key] = cats.get(key, 0) + 1
    for k in sorted(cats):
        lines.append(f"- {k[0]}, gold file present in {k[1]}: {cats[k]}")
    (RESULTS / "coverage_anchor.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
