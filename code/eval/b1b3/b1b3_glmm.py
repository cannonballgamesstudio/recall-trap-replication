#!/usr/bin/env python3
"""LOCAL-B1B3-ADDENDUM-PREREG §7.2 secondary mixed logit (engine: statsmodels BinomialBayesMixedGLM, VB).

Per contrast pair A-B (3 seeds each): resolved ~ armA + VC(instance) + VC(seed) + VC(seed:armA)
-- the seed:arm variance component is the random-slope (between-seed variance of the arm effect).
Rows = pairwise-attempted (instance, seed, arm). Writes results/b1b3-replication/glmm.json. Does not enter any verdict.
"""
import json, math, os, sys
from pathlib import Path
import pandas as pd
from statsmodels.genmod.bayes_mixed_glm import BinomialBayesMixedGLM

sys.path.insert(0, str(Path(__file__).resolve().parent))
import b1b3_analyze as an  # noqa: E402

PAIRS = [("OFF", "ON"), ("OFF", "T"), ("T", "ON"), ("TM", "T"), ("OFF", "TM")]


def main():
    t_ids = set((an.P / "b1b3_ids_T.txt").read_text(encoding="utf-8").split())
    t_ids -= an.CLASS_P_INSTANCES   # PRIMARY (owner, §12 D-8475): Class-P instance excluded from every arm/seed
    arms = {a: an.load_arm(a) for a in ("ON", "OFF", "T", "TM")}
    out = {"engine": "statsmodels BinomialBayesMixedGLM.fit_vb", "fits": {}}
    for A, B in PAIRS:
        if arms[A] is None or arms[B] is None:
            continue
        rows = []
        for j in (0, 1, 2):
            ids = [i for i in sorted(t_ids) if i in arms[A][j][0] and i in arms[B][j][0]]
            for i in ids:
                rows.append({"inst": i, "seed": j, "armA": 1, "y": int(i in arms[A][j][1])})
                rows.append({"inst": i, "seed": j, "armA": 0, "y": int(i in arms[B][j][1])})
        df = pd.DataFrame(rows)
        vc = {"inst": "0 + C(inst)", "seed": "0 + C(seed)", "seed_arm": "0 + C(seed):armA"}
        m = BinomialBayesMixedGLM.from_formula("y ~ armA", vc, df)
        r = m.fit_vb()
        names = list(m.vcp_names)
        sd = {n: math.exp(float(v)) for n, v in zip(names, r.vcp_mean)}
        out["fits"][f"{A}-{B}"] = {
            "n_rows": len(df),
            "armA_logodds_mean": float(r.fe_mean[1]), "armA_logodds_sd": float(r.fe_sd[1]),
            "vc_sd_posterior_mean": sd,
            "between_seed_var_of_arm_effect_logodds2": sd.get("seed_arm", float("nan")) ** 2,
        }
        print(A, B, json.dumps(out["fits"][f"{A}-{B}"]))
    (an.OUTD / "glmm.json").write_text(json.dumps(out, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
