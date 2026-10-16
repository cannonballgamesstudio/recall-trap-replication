import subprocess


def fetch_and_checkout(worktree: str, ref: str, sha: str, runner=subprocess.run) -> None:
    """Bring `worktree`'s working tree to `sha`.

    `git fetch origin <ref>` is best-effort (the sha is often already present in the
    cloned-off-main objects, and tests run without a remote); the checkout must succeed.
    """
    runner(["git", "-C", worktree, "fetch", "--quiet", "origin", ref],
           capture_output=True, text=True, check=False)
    runner(["git", "-C", worktree, "checkout", "--quiet", "--detach", sha],
           capture_output=True, text=True, check=True)
