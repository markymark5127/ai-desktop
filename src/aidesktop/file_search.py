"""Bounded local filename search for Mutsu Spotlight.

This indexes filenames/metadata only in user-facing home folders. It never
reads file content, follows symlinks, requests model inference, or runs Exec
lines. Call on a background thread when constructing the launcher; refresh
when the launcher is reopened rather than rescanning on every keystroke.
"""
from __future__ import annotations

import os
from collections import deque
from dataclasses import dataclass
from pathlib import Path

FOLDERS = ("Documents", "Downloads", "Desktop", "Pictures", "Videos", "Music")
MAX_VISITED = 1800
MAX_DEPTH = 2


@dataclass(frozen=True)
class FileResult:
    path: Path
    name: str
    subtitle: str
    is_dir: bool


def _subtitle(path: Path, home: Path, is_dir: bool) -> str:
    try:
        parent = "~/" + str(path.parent.relative_to(home))
        if parent == "~/.":
            parent = "~"
    except ValueError:
        parent = str(path.parent)
    return (parent + (" · Folder" if is_dir else ""))


def list_local_files(
    *, home: Path | None = None, max_visited: int = MAX_VISITED,
    max_depth: int = MAX_DEPTH,
) -> list[FileResult]:
    """Return only a small bounded set of real user-visible filesystem entries.

    Existing home folders are searched, not system locations, hidden config,
    mounted media, symlinks, or unbounded recursive trees. Even if a directory
    is huge, the overall visited-entry budget is enforced.
    """
    home = Path.home() if home is None else Path(home)
    queue: deque[tuple[Path, int]] = deque(
        (home / name, 0) for name in FOLDERS if (home / name).is_dir()
    )
    results: list[FileResult] = []
    visited = 0
    seen: set[Path] = set()
    while queue and visited < max_visited:
        root, depth = queue.popleft()
        try:
            if root.is_symlink():
                continue
            with os.scandir(root) as entries:
                for entry in entries:
                    visited += 1
                    if visited > max_visited:
                        break
                    if entry.name.startswith("."):
                        continue
                    try:
                        if entry.is_symlink():
                            continue
                        is_dir = entry.is_dir(follow_symlinks=False)
                        is_file = entry.is_file(follow_symlinks=False)
                    except OSError:
                        continue
                    if not (is_dir or is_file):
                        continue
                    path = Path(entry.path)
                    if path in seen:
                        continue
                    seen.add(path)
                    results.append(FileResult(
                        path, entry.name, _subtitle(path, home, is_dir), is_dir
                    ))
                    if is_dir and depth < max_depth:
                        queue.append((path, depth + 1))
        except OSError:
            continue
    return results


def search_local_files(
    query: str, catalog: list[FileResult], *, limit: int = 4,
) -> list[FileResult]:
    """Rank by file/folder name; never match file contents or hidden entries."""
    query = query.strip().casefold()
    if len(query) < 2 or limit <= 0:
        return []
    scored: list[tuple[int, FileResult]] = []
    for item in catalog:
        name = item.name.casefold()
        score = (90 if name == query else
                 75 if name.startswith(query) else
                 45 if query in name else 0)
        if score:
            scored.append((score + int(item.is_dir), item))
    scored.sort(key=lambda pair: (-pair[0], pair[1].name.casefold()))
    return [item for _score, item in scored[:min(20, limit)]]
