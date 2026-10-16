# src/ragfusion/fusion/dense.py
from __future__ import annotations

from pathlib import Path

import numpy as np

# Same validated wording as the srclight adapter (recall 0.573->0.686 on the
# private-repo flood A/B; exact phrasing beat 7 alternatives). Duplicated on purpose:
# adapters stay decoupled (srclight_backend is LOCKED-untouched).
DEFAULT_QUERY_INSTRUCT = "Given a code-search intent, retrieve the most relevant source code."


def build_dense(texts: list[str], provider, out_path: Path, batch_size: int = 32,
                max_failure_rate: float = 0.10) -> int:
    """Embed texts -> L2-normalized float16 npy at out_path. Returns dims.

    A failed batch is retried once per-item; items that still fail become zero
    vectors. If failures/total exceeds max_failure_rate, raise — a mostly-empty
    'dense' arm masquerading as hybrid is the silent degradation the spec forbids.
    """
    dims = int(provider.dimensions)
    n = len(texts)
    out = np.zeros((n, dims), dtype=np.float32)
    failures = 0
    for start in range(0, n, batch_size):
        batch = texts[start:start + batch_size]
        try:
            vecs = provider.embed_batch(batch)
            for j, v in enumerate(vecs):
                out[start + j] = np.asarray(v, dtype=np.float32)
        except Exception:
            for j, t in enumerate(batch):          # per-item retry isolates the bad text
                try:
                    out[start + j] = np.asarray(provider.embed_one(t), dtype=np.float32)
                except Exception:
                    failures += 1
    if n and failures / n > max_failure_rate:
        raise RuntimeError(
            f"embed failure rate {failures}/{n} exceeds {max_failure_rate:.0%}: "
            "embedding provider likely down — refusing to ship a crippled dense arm. "
            "Check the embedding server, then re-index.")
    norms = np.linalg.norm(out, axis=1, keepdims=True)
    np.divide(out, norms, out=out, where=norms > 0)
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = out_path.with_suffix(out_path.suffix + ".tmp")
    np.save(tmp, out.astype(np.float16))
    # np.save appends ".npy" when the target's suffix isn't literally ".npy" --
    # tmp here is "fusion_emb.npy.tmp" (suffix ".tmp"), so np.save actually
    # writes "fusion_emb.npy.tmp.npy". Verified empirically; handle both so
    # this doesn't silently break if numpy's suffix behavior ever changes.
    saved = tmp if tmp.exists() else tmp.with_suffix(tmp.suffix + ".npy")
    import os
    os.replace(saved, out_path)
    return dims


def embed_query(provider, text: str, instruct: str | None) -> np.ndarray:
    q = f"Instruct: {instruct}\nQuery: {text}" if instruct else text
    v = np.asarray(provider.embed_one(q), dtype=np.float32)
    n = np.linalg.norm(v)
    return v / n if n > 0 else v


class DenseIndex:
    def __init__(self, arr: np.ndarray):
        self._arr = arr
        # Materialize float32 ONCE: per-search astype copied the whole matrix per
        # query (measured 600-950ms median on 20k+ chunk repos). ~800MB worst-case
        # on the eval corpora; switch to chunked f16 dot if RAM-pressured.
        self._arr32 = arr.astype(np.float32)

    @classmethod
    def load(cls, out_path: Path) -> "DenseIndex":
        return cls(np.load(Path(out_path), mmap_mode="r"))

    def search(self, qvec: np.ndarray, k: int) -> list[tuple[int, float]]:
        if self._arr32.shape[0] == 0:
            return []
        if k <= 0:
            return []
        scores = self._arr32 @ qvec.astype(np.float32)
        k = min(k, scores.shape[0])
        top = np.argpartition(-scores, k - 1)[:k]
        top = top[np.argsort(-scores[top])]
        return [(int(i), float(scores[i])) for i in top if scores[i] > 0.0]
