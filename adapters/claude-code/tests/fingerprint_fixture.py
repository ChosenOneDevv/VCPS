#!/usr/bin/env python3
"""Print a stable fixture digest using descriptor-relative no-follow reads."""

import hashlib
import json
import os
import stat
import sys
from pathlib import Path


def fingerprint(root: Path):
    if os.name != "posix" or not hasattr(os, "O_DIRECTORY") or not hasattr(os, "O_NOFOLLOW"):
        raise OSError("secure fixture fingerprinting requires POSIX O_DIRECTORY/O_NOFOLLOW")
    if os.open not in os.supports_dir_fd or os.stat not in os.supports_dir_fd:
        raise OSError("secure fixture fingerprinting requires dir_fd open/stat support")
    root = Path(root).resolve(strict=True)
    root_fd = os.open(root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    entries = []

    def add(path, kind, mode, digest):
        entries.append({"path": path, "kind": kind, "mode": mode, "digest": digest})

    def visit(directory_fd, prefix=""):
        names = sorted(os.listdir(directory_fd), key=os.fsencode)
        for name in names:
            if name == ".git":
                continue
            relative = f"{prefix}/{name}" if prefix else name
            before = os.stat(name, dir_fd=directory_fd, follow_symlinks=False)
            mode = stat.S_IMODE(before.st_mode)
            if stat.S_ISLNK(before.st_mode):
                target = os.readlink(name, dir_fd=directory_fd)
                after = os.stat(name, dir_fd=directory_fd, follow_symlinks=False)
                if (before.st_dev, before.st_ino, mode) != (
                    after.st_dev, after.st_ino, stat.S_IMODE(after.st_mode)
                ):
                    raise OSError(f"fixture symlink changed during fingerprint: {relative}")
                add(relative, "symlink", mode, hashlib.sha256(os.fsencode(target)).hexdigest())
            elif stat.S_ISDIR(before.st_mode):
                add(relative, "directory", mode, None)
                child_fd = os.open(
                    name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=directory_fd
                )
                try:
                    actual = os.fstat(child_fd)
                    if (before.st_dev, before.st_ino, mode) != (
                        actual.st_dev, actual.st_ino, stat.S_IMODE(actual.st_mode)
                    ):
                        raise OSError(f"fixture directory changed during fingerprint: {relative}")
                    visit(child_fd, relative)
                    after = os.fstat(child_fd)
                    if (actual.st_size, actual.st_mtime_ns, actual.st_ctime_ns) != (
                        after.st_size, after.st_mtime_ns, after.st_ctime_ns
                    ):
                        raise OSError(f"fixture directory changed while fingerprinting: {relative}")
                finally:
                    os.close(child_fd)
            elif stat.S_ISREG(before.st_mode):
                file_fd = os.open(
                    name, os.O_RDONLY | os.O_NOFOLLOW | getattr(os, "O_NONBLOCK", 0),
                    dir_fd=directory_fd,
                )
                digest = hashlib.sha256()
                try:
                    actual = os.fstat(file_fd)
                    if (not stat.S_ISREG(actual.st_mode)
                            or (before.st_dev, before.st_ino, mode) != (
                                actual.st_dev, actual.st_ino, stat.S_IMODE(actual.st_mode)
                            )):
                        raise OSError(f"fixture file changed during fingerprint: {relative}")
                    with os.fdopen(file_fd, "rb", closefd=False) as stream:
                        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                            digest.update(chunk)
                    after = os.fstat(file_fd)
                    if (actual.st_size, actual.st_mtime_ns, actual.st_ctime_ns) != (
                        after.st_size, after.st_mtime_ns, after.st_ctime_ns
                    ):
                        raise OSError(f"fixture file changed while fingerprinting: {relative}")
                finally:
                    os.close(file_fd)
                add(relative, "file", mode, digest.hexdigest())
            else:
                add(relative, "special", mode, None)

    try:
        root_before = os.fstat(root_fd)
        visit(root_fd)
        root_after = os.fstat(root_fd)
        if (root_before.st_size, root_before.st_mtime_ns, root_before.st_ctime_ns) != (
            root_after.st_size, root_after.st_mtime_ns, root_after.st_ctime_ns
        ):
            raise OSError("fixture root changed while fingerprinting")
    finally:
        os.close(root_fd)

    entries.sort(key=lambda item: os.fsencode(item["path"]))
    canonical = json.dumps(entries, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(canonical.encode("ascii")).hexdigest()


if __name__ == "__main__":
    try:
        print(fingerprint(Path(sys.argv[1])))
    except (IndexError, OSError, ValueError) as exc:
        print(f"fixture fingerprint failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
