import re

_UNSAFE = re.compile(r"[^A-Za-z0-9_.:-]")


def slug(s: str) -> str:
    """Make a repo/ref name safe for a single ZFS dataset/snapshot component."""
    return _UNSAFE.sub("_", s)


def main_dataset(pool: str, repo: str) -> str:
    return f"{pool}/ragfusion/{slug(repo)}/main"


def refs_parent(pool: str, repo: str) -> str:
    return f"{pool}/ragfusion/{slug(repo)}/refs"


def ref_dataset(pool: str, repo: str, ref: str, sha: str, token) -> str:
    return f"{refs_parent(pool, repo)}/{slug(ref)}-{sha[:12]}-{token}"


def snap_name(ref: str, sha: str, token) -> str:
    return f"r-{slug(ref)}-{sha[:12]}-{token}"
