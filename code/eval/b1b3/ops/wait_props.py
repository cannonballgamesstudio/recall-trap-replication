import json, sys, time, urllib.request as u
D = r"work/p5/b1b3"
for i in range(240):
    try:
        p = json.load(u.urlopen("http://127.0.0.1:8090/props", timeout=5)); break
    except Exception:
        time.sleep(5)
else:
    print("TIMEOUT"); sys.exit(2)
open(D + r"\props_8090.json", "w").write(json.dumps(p, indent=1))
try:
    s = json.load(u.urlopen("http://127.0.0.1:8090/slots", timeout=10))
    open(D + r"\slots_8090.json", "w").write(json.dumps(s, indent=1))
except Exception as e:
    print("slots:", e)
g = p.get("default_generation_settings", {})
print("n_ctx", g.get("n_ctx"), "top_p", g.get("params", {}).get("top_p"), "total_slots", p.get("total_slots"))
