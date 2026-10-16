import json, sys
sys.path.insert(0, r"code/eval")
import swe_bench as sb
m = {x["instance_id"]: x for x in json.load(open(r"data/post-cutoff-branchA/instances_post.json", encoding="utf-8"))}
s = open(r"data/post-cutoff-branchA/gold_pass_ids_post.txt").read().split()
for r in sorted({(m[i]["repo"], m[i]["url"]) for i in s}):
    try:
        print(sb.cache_clone(*r), flush=True)
    except Exception as e:
        print("FAIL", r, e, flush=True)
