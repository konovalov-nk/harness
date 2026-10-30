#!/usr/bin/env python3
"""Install only visual-explain assets; leave the existing OpenCode config intact."""

import argparse
from datetime import datetime, timezone
from pathlib import Path
import shutil


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config-dir", type=Path, default=Path.home() / ".config/opencode")
    args = parser.parse_args()
    source = Path(__file__).resolve().parents[1] / "config"
    destination = args.config_dir.expanduser().resolve()
    files = [source / "commands/visual-explain.md"]
    files += sorted(p for p in (source / "skills/visual-explain").rglob("*")
                    if p.is_file() and "__pycache__" not in p.parts and p.suffix != ".pyc")
    backups = destination / "backups" / ("visual-explain-" + datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S-%f"))
    for path in files:
        relative = path.relative_to(source)
        target = destination / relative
        if target.exists():
            backup = backups / relative
            backup.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(target, backup)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, target)
    print(f"Installed {len(files)} files into {destination}")
    if backups.exists():
        print(f"Previous visual-explain files: {backups}")
    print("Use /visual-explain in a build-capable OpenCode 2 TUI session.")


if __name__ == "__main__":
    main()
