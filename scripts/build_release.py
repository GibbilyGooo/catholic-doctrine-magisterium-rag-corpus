#!/usr/bin/env python3
"""Create repository checksums and a deterministic public release archive."""
from __future__ import annotations

import argparse
import hashlib
import zipfile
from pathlib import Path


EXCLUDED_PARTS = {".git", "build", "__pycache__"}
EXCLUDED_NAMES = {"SHA256SUMS"}
FIXED_TIME = (2026, 8, 28, 0, 0, 0)


def included_files(root: Path) -> list[Path]:
    return sorted(
        path for path in root.rglob("*")
        if path.is_file()
        and not EXCLUDED_PARTS.intersection(path.relative_to(root).parts)
        and path.name not in EXCLUDED_NAMES
    )


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    root = args.root.resolve()
    output = (args.output or root.parent / "Catholic_Doctrine_Magisterium_RAG_Corpus_v1.0.0.zip").resolve()

    files = included_files(root)
    checksums = "".join(f"{sha256(path)}  {path.relative_to(root).as_posix()}\n" for path in files)
    (root / "SHA256SUMS").write_text(checksums, encoding="utf-8", newline="\n")
    files = included_files(root) + [root / "SHA256SUMS"]

    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in sorted(files):
            relative = Path(root.name) / path.relative_to(root)
            info = zipfile.ZipInfo(relative.as_posix(), FIXED_TIME)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = (0o100644 & 0xFFFF) << 16
            archive.writestr(info, path.read_bytes(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)

    print(f"archive={output}")
    print(f"files={len(files)}")
    print(f"bytes={output.stat().st_size}")
    print(f"sha256={sha256(output)}")


if __name__ == "__main__":
    main()
