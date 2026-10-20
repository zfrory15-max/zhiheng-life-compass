#!/usr/bin/env python3
"""Build a deterministic, allowlisted public skill ZIP with only stdlib."""
from pathlib import Path
import hashlib
import json
import re
import zipfile

ROOT = Path(__file__).resolve().parents[1]
NAME = "zhiheng-life-compass"
VERSION = "public-v1.0.0"
ROOT_FILES = ("SKILL.md", "README.md", "RIGHTS.md", ".gitignore", ".gitattributes")
PATTERNS = ("agents/*.yaml", "references/*.md", "references/topics/*.md",
            "data/cards.json", "scripts/*.py", "docs/*.md", "tests/*.py",
            ".github/workflows/*.yml")


def public_files():
    paths = {ROOT / name for name in ROOT_FILES}
    for pattern in PATTERNS:
        paths.update(ROOT.glob(pattern))
    for path in sorted(paths):
        if not path.is_file() or path.is_symlink():
            raise ValueError("发布文件缺失或为符号链接：" + str(path.relative_to(ROOT)))
        text = path.read_text(encoding="utf-8")
        # This is a targeted accidental-leak check, not a general secret scanner.
        if re.search(r"[A-Za-z]:[/\\](?:Users|Documents and Settings)[/\\]", text):
            raise ValueError("发布文件包含个人绝对路径：" + str(path.relative_to(ROOT)))
        if re.search(r"(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{40,})", text):
            raise ValueError("发布文件疑似包含凭据：" + str(path.relative_to(ROOT)))
        if path.stat().st_size > 250_000:
            raise ValueError("文件超出公开版大小预期：" + str(path.relative_to(ROOT)))
    cards = json.loads((ROOT / "data/cards.json").read_text(encoding="utf-8"))
    if len(cards) != 39:
        raise ValueError("公开版应有39张知识卡")
    allowed_source_keys = {"doc_id", "title", "paragraph", "start", "end", "reason", "path"}
    for card in cards:
        for source in card["sources"]:
            if set(source) != allowed_source_keys:
                raise ValueError("来源字段不符合公开白名单：" + card["id"])
    return sorted(paths)


def main():
    paths = public_files()
    output = ROOT / "dist"
    output.mkdir(exist_ok=True)
    archive = output / f"{NAME}-{VERSION}.zip"
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as package:
        for path in paths:
            relative = path.relative_to(ROOT).as_posix()
            info = zipfile.ZipInfo(f"{NAME}/{relative}", date_time=(2026, 10, 20, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            # Normalize line endings for reproducible ZIPs on Windows and Unix.
            payload = path.read_text(encoding="utf-8").replace("\r\n", "\n").encode("utf-8")
            package.writestr(info, payload)
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    (output / "SHA256SUMS.txt").write_text(f"{digest}  {archive.name}\n", encoding="utf-8")
    print(json.dumps({"archive": archive.relative_to(ROOT).as_posix(),
                      "files": len(paths), "bytes": archive.stat().st_size,
                      "sha256": digest}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
