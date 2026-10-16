#!/usr/bin/env python3
"""Build Arm T (trimmed breadth) per docs/paper/TRIMMED-BREADTH-PREREG.md §3, with §5 checks.

T = OFF pack's file set, in OFF rank order (first appearance), one chunk per file:
the chunk dedup-ON served for that file, copied byte-identically from the ON pack.
No filler. Header rendered exactly as g_plane_prompts.format_pack does (top-{n}).
"""
import json, re, sys
from pathlib import Path

P = Path("work/p5")
OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).parent

HDR = re.compile(r"^### (?P<file>.+):(?P<line>\d+) \u2014 (?P<sym>.*) \[(?P<kind>[^\]]*)\]$")
PACK_HDR = re.compile(r"^## Retrieved context \(top-(\d+), from the repository's retrieval index\)$")


def parse(pack: str):
    """Split a format_pack string into (header, [block dicts]). Round-trip verified by caller."""
    header, _, rest = pack.partition("\n")
    assert PACK_HDR.match(header), header[:100]
    # candidate split points: "\n\n### " where the ### line is a valid chunk header,
    # followed by a ``` fence line, and preceded by ``` (end of previous block) or the header.
    body = "\n" + rest  # so that the first block is preceded by "\n\n"
    starts = []
    for m in re.finditer(r"\n\n(### [^\n]*)\n```\n", body):
        if not HDR.match(m.group(1)):
            continue
        pre = body[:m.start()]
        if m.start() == 0 or pre.endswith("```"):
            starts.append(m.start())
    blocks = []
    for i, s in enumerate(starts):
        e = starts[i + 1] if i + 1 < len(starts) else len(body)
        text = body[s + 2:e]
        h = HDR.match(text.split("\n", 1)[0])
        blocks.append({"file": h["file"], "line": int(h["line"]), "text": text})
    return header, blocks


def render(blocks):
    n = len(blocks)
    return (f"## Retrieved context (top-{n}, from the repository's retrieval index)"
            + "".join("\n\n" + b["text"] for b in blocks))


def main():
    lp = json.loads((P / "local_packs.json").read_text(encoding="utf-8"))
    T, prov, viol, issues = {}, {}, [], []
    TP, provp = {}, {}
    gold = {c["instance_id"]: c["gold_files"] for c in json.loads((P / "instances_verified.json").read_text(encoding="utf-8"))}
    stats = {"on_slots": [], "off_slots": [], "t_slots": [], "on_chars": [], "off_chars": [],
             "t_chars": [], "off_files": [], "on_chunk_is_first_off_chunk": 0,
             "on_chunk_in_off_chunks": 0, "t_files_total": 0}
    for iid in sorted(lp):
        on, off = lp[iid]["dedupON"], lp[iid]["dedupOFF"]
        hon, bon = parse(on["pack"])
        hoff, boff = parse(off["pack"])
        # round-trip + count checks on the source packs
        for name, arm, h, b in (("ON", on, hon, bon), ("OFF", off, hoff, boff)):
            if h + "".join("\n\n" + x["text"] for x in b) != arm["pack"]:
                issues.append((iid, name, "roundtrip"))
            if len(b) != arm.get("n_hits", len(b)) or int(PACK_HDR.match(h).group(1)) != len(b):
                issues.append((iid, name, f"count {len(b)} vs n_hits {arm.get('n_hits')}"))
            if sorted({x["file"] for x in b}) != sorted(arm["files"]):
                issues.append((iid, name, "files-mismatch"))
        on_by_file = {}
        for x in bon:
            if x["file"] in on_by_file:
                issues.append((iid, "ON", f"duplicate file {x['file']}"))
            on_by_file.setdefault(x["file"], x)
        off_order = []
        for x in boff:
            if x["file"] not in off_order:
                off_order.append(x["file"])
        missing = [f for f in off_order if f not in on_by_file]
        stats["on_slots"].append(len(bon)); stats["off_slots"].append(len(boff))
        stats["on_chars"].append(len(on["pack"])); stats["off_chars"].append(len(off["pack"]))
        stats["off_files"].append(len(off_order))
        if missing:
            viol.append({"instance_id": iid, "off_files_not_in_on": missing})
            kept = [f for f in off_order if f in on_by_file]
            tb = [on_by_file[f] for f in kept]
            TP[iid] = {"Tprime": {"pack": render(tb), "files": sorted(kept), "n_hits": len(tb)}}
            provp[iid] = {"chunks": [{"file": b["file"], "line": b["line"]} for b in tb],
                          "dropped_off_files": missing,
                          "gold_file_dropped": sorted(set(missing) & set(gold[iid]))}
            continue
        tblocks = [on_by_file[f] for f in off_order]
        for f in off_order:
            offchunks = [(x["line"], x["text"]) for x in boff if x["file"] == f]
            onc = (on_by_file[f]["line"], on_by_file[f]["text"])
            stats["t_files_total"] += 1
            stats["on_chunk_in_off_chunks"] += onc in offchunks
            stats["on_chunk_is_first_off_chunk"] += offchunks[0] == onc
        pack = render(tblocks)
        T[iid] = {"T": {"pack": pack, "files": sorted(off_order), "n_hits": len(tblocks)}}
        prov[iid] = [{"file": b["file"], "line": b["line"]} for b in tblocks]
        stats["t_slots"].append(len(tblocks)); stats["t_chars"].append(len(pack))

    # ---- §5.2 chunk identity, checked independently by re-parsing the written T packs
    ident_ok = ident_tot = 0
    for iid, v in list(T.items()) + list(TP.items()):
        key = "T" if "T" in v else "Tprime"
        _, bt = parse(v[key]["pack"])
        _, bon = parse(lp[iid]["dedupON"]["pack"])
        onmap = {(x["file"], x["line"]): x["text"] for x in bon}
        offfiles = []
        for x in parse(lp[iid]["dedupOFF"]["pack"])[1]:
            if x["file"] not in offfiles:
                offfiles.append(x["file"])
        onfiles = {x["file"] for x in bon}
        assert [x["file"] for x in bt] == [f for f in offfiles if f in onfiles], iid
        for x in bt:
            ident_tot += 1
            ident_ok += onmap.get((x["file"], x["line"])) == x["text"]

    n = len(lp)
    mean = lambda a: sum(a) / len(a) if a else float("nan")
    report = {
        "n_instances": n,
        "subset_property_rate": (n - len(viol)) / n,
        "subset_satisfied": n - len(viol),
        "violations": viol,
        "source_parse_issues": issues,
        "chunk_identity": f"{ident_ok}/{ident_tot}",
        "chunk_identity_rate": ident_ok / ident_tot if ident_tot else None,
        "diag_on_chunk_is_first_off_chunk_of_file": f"{stats['on_chunk_is_first_off_chunk']}/{stats['t_files_total']}",
        "diag_on_chunk_present_among_off_chunks_of_file": f"{stats['on_chunk_in_off_chunks']}/{stats['t_files_total']}",
        "mean_slots": {"ON": mean(stats["on_slots"]), "OFF": mean(stats["off_slots"]), "T": mean(stats["t_slots"])},
        "mean_pack_chars": {"ON": mean(stats["on_chars"]), "OFF": mean(stats["off_chars"]), "T": mean(stats["t_chars"])},
        "mean_off_files": mean(stats["off_files"]),
        "tprime_n": len(TP),
        "tprime_mean_slots": mean([v["Tprime"]["n_hits"] for v in TP.values()]),
        "tprime_mean_chars": mean([len(v["Tprime"]["pack"]) for v in TP.values()]),
        "tprime_gold_file_dropped": {k: v["gold_file_dropped"] for k, v in provp.items() if v["gold_file_dropped"]},
        "t_slot_hist": {k: stats["t_slots"].count(k) for k in sorted(set(stats["t_slots"]))},
    }
    (OUT / "T_build_report.json").write_text(json.dumps(report, indent=1), encoding="utf-8")
    if ident_ok != ident_tot or issues or len(T) != 473 or len(TP) != 27:
        print(json.dumps(report, indent=1)[:4000])
        print("ABORT: construction check failed; packs NOT written"); return
    outs = {"packfile_T_qwen30b.json": T, "packfile_T_gpt56sol.json": T,
            "packfile_Tprime_qwen30b.json": TP, "packfile_Tprime_gpt56sol.json": TP,
            "packfile_T_provenance.json": prov, "packfile_Tprime_provenance.json": provp}
    for name in outs:
        assert not (P / name).exists(), f"refusing to overwrite {P / name}"
    for name, obj in outs.items():
        (P / name).write_text(json.dumps(obj), encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k != "violations"}, indent=1))
    print("violations:", viol)


if __name__ == "__main__":
    main()
