import os
import shutil
import subprocess
from typing import Protocol


class StorageBackend(Protocol):
    def snapshot(self, dataset: str, snap: str) -> None: ...
    def clone(self, dataset: str, snap: str, target: str) -> str: ...
    def destroy(self, dataset: str, recursive: bool = False) -> None: ...
    def destroy_snapshot(self, dataset: str, snap: str) -> None: ...
    def mountpoint(self, dataset: str) -> str: ...
    def list_snapshots(self, dataset: str) -> list[str]: ...
    def list_child_datasets(self, parent: str) -> list[str]: ...


class FakeStorage:
    """Temp-dir emulation of ZFS for tests/dev on non-ZFS hosts."""

    def __init__(self, root: str):
        self.root = root

    def mountpoint(self, dataset: str) -> str:
        return os.path.join(self.root, dataset)

    def _snap_path(self, dataset: str, snap: str) -> str:
        return os.path.join(self.root, ".snaps", f"{dataset.replace('/', '_')}@{snap}")

    def snapshot(self, dataset: str, snap: str) -> None:
        src = self.mountpoint(dataset)
        dst = self._snap_path(dataset, snap)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copytree(src, dst)

    def clone(self, dataset: str, snap: str, target: str) -> str:
        dst = self.mountpoint(target)
        shutil.copytree(self._snap_path(dataset, snap), dst)
        return dst

    def destroy(self, dataset: str, recursive: bool = False) -> None:
        # NOTE: FakeStorage does not model ZFS dependent-dataset semantics.
        # It always removes the dataset's directory and its own snapshots;
        # `recursive` is accepted only for signature compatibility with the
        # StorageBackend protocol. Real ZFS recursive=False/True dependency
        # errors are enforced by ZfsStorage (Task 7) via `zfs destroy [-r]`,
        # not here. Do not rely on FakeStorage to catch recursive=False misuse.
        shutil.rmtree(self.mountpoint(dataset), ignore_errors=True)
        snaps_root = os.path.join(self.root, ".snaps")
        prefix = dataset.replace("/", "_") + "@"
        if os.path.isdir(snaps_root):
            for name in os.listdir(snaps_root):
                if name.startswith(prefix):
                    shutil.rmtree(os.path.join(snaps_root, name), ignore_errors=True)

    def destroy_snapshot(self, dataset: str, snap: str) -> None:
        shutil.rmtree(self._snap_path(dataset, snap), ignore_errors=True)

    def list_snapshots(self, dataset: str) -> list[str]:
        snaps_root = os.path.join(self.root, ".snaps")
        prefix = dataset.replace("/", "_") + "@"
        if not os.path.isdir(snaps_root):
            return []
        return sorted(name[len(prefix):] for name in os.listdir(snaps_root)
                      if name.startswith(prefix))

    def list_child_datasets(self, parent: str) -> list[str]:
        parent_mp = self.mountpoint(parent)
        if not os.path.isdir(parent_mp):
            return []
        return sorted(f"{parent}/{child}" for child in os.listdir(parent_mp)
                      if os.path.isdir(os.path.join(parent_mp, child)))


class ZfsStorage:
    """Real ZFS adapter. `runner` is injectable for testing (defaults to subprocess.run)."""

    def __init__(self, runner=subprocess.run):
        self._run = runner

    def _zfs(self, *args: str) -> str:
        result = self._run(["zfs", *args], capture_output=True, text=True, check=True)
        return getattr(result, "stdout", "") or ""

    def snapshot(self, dataset: str, snap: str) -> None:
        self._zfs("snapshot", f"{dataset}@{snap}")

    def mountpoint(self, dataset: str) -> str:
        return self._zfs("get", "-H", "-o", "value", "mountpoint", dataset).strip()

    def clone(self, dataset: str, snap: str, target: str) -> str:
        self._zfs("clone", f"{dataset}@{snap}", target)
        return self.mountpoint(target)

    def destroy(self, dataset: str, recursive: bool = False) -> None:
        args = ["destroy"]
        if recursive:
            args.append("-r")
        args.append(dataset)
        self._zfs(*args)

    def destroy_snapshot(self, dataset: str, snap: str) -> None:
        self._zfs("destroy", f"{dataset}@{snap}")

    def list_snapshots(self, dataset: str) -> list[str]:
        out = self._zfs("list", "-t", "snapshot", "-H", "-o", "name", "-d", "1", dataset)
        prefix = f"{dataset}@"
        return [line[len(prefix):] for line in out.splitlines() if line.startswith(prefix)]

    def list_child_datasets(self, parent: str) -> list[str]:
        out = self._zfs("list", "-H", "-o", "name", "-d", "1", parent)
        return [line for line in out.splitlines() if line and line != parent]
