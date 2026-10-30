#!/usr/bin/env python3
"""Validate a visual-explain model, render offline HTML, and optionally open it."""

import argparse
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
from urllib.parse import urlparse

EVIDENCE = {"observed", "documented", "inferred", "unknown"}
STATES = {"flowing", "waiting", "idle", "uncertain"}
ID = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*\Z")


def require(condition, message):
    if not condition:
        raise ValueError(message)


def text_fields(item, *names):
    require(isinstance(item, dict), "Each item must be an object")
    for name in names:
        require(isinstance(item.get(name), str) and item[name].strip(),
                f"Missing or empty text field: {name}")


def validate(model):
    require(isinstance(model, dict), "Model must be an object")
    require(type(model.get("version")) is int and model["version"] == 1, "Expected version 1")
    text_fields(model, "title")
    require(isinstance(model.get("summary", ""), str), "summary must be text")
    ids = set()
    for group in ("sources", "entities", "interfaces", "steps"):
        require(isinstance(model.get(group), list), f"{group} must be an array")
        for item in model[group]:
            text_fields(item, "id")
            require(ID.fullmatch(item["id"]) is not None, f"Invalid ID: {item['id']}")
            require(item["id"] not in ids, f"Duplicate ID: {item['id']}")
            ids.add(item["id"])
    require(model["entities"] and model["steps"], "Need at least one entity and step")
    sources = {s["id"] for s in model["sources"]}
    for source in model["sources"]:
        text_fields(source, "label")
        if "url" in source:
            require(isinstance(source["url"], str), "Source URL must be text")
            parsed = urlparse(source["url"])
            require(parsed.scheme in {"http", "https"} and bool(parsed.netloc),
                    "Source URLs must be HTTP(S)")
    for group in ("entities", "interfaces", "steps"):
        for item in model[group]:
            text_fields(item, "label", "details", "evidence")
            require(item["evidence"] in EVIDENCE, "Invalid evidence status")
            refs = item.get("sources")
            require(isinstance(refs, list) and all(isinstance(s, str) and s in sources for s in refs),
                    f"Unknown source reference on {item['id']}")
            require(item["evidence"] not in {"observed", "documented"} or refs,
                    f"{item['id']}: observed/documented claims need a source")
    cells = set()
    for entity in model["entities"]:
        text_fields(entity, "technical", "kind", "summary")
        row, col = entity.get("row"), entity.get("column")
        require(type(row) is int and 0 <= row <= 12, "row must be an integer from 0 to 12")
        require(type(col) is int and 0 <= col <= 2, "column must be an integer from 0 to 2")
        require((row, col) not in cells, "Entities must occupy unique grid cells")
        cells.add((row, col))
    entities = {e["id"] for e in model["entities"]}
    interfaces = {e["id"] for e in model["interfaces"]}
    for edge in model["interfaces"]:
        text_fields(edge, "technical", "from", "to")
        require(edge["from"] in entities and edge["to"] in entities, "Unknown interface endpoint")
        require(edge["from"] != edge["to"], "Use separate internal entities instead of self-links")
        require(type(edge.get("feedback", False)) is bool, "feedback must be boolean")
    for step in model["steps"]:
        for key, valid in (("entities", entities), ("interfaces", interfaces)):
            values = step.get(key)
            require(isinstance(values, dict), f"Step {key} must be an object")
            require(all(k in valid and isinstance(v, str) and v.strip() for k, v in values.items()),
                    f"Unknown/invalid step {key}")
        require(all(s in STATES for s in step["interfaces"].values()), "Invalid interface state")
    return model


def open_browser(path):
    uri = path.as_uri()
    if sys.platform == "darwin":
        command = ["open", uri]
    elif sys.platform.startswith("linux"):
        if not (os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY")):
            return "No graphical session detected; open the file URI on your desktop."
        if shutil.which("xdg-open"):
            command = ["xdg-open", uri]
        elif shutil.which("gio"):
            command = ["gio", "open", uri]
        else:
            return "No xdg-open or gio found; open the file URI manually."
    else:
        return "Automatic opening is supported on Linux/macOS; open the file URI manually."
    try:
        child = subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                                 stderr=subprocess.DEVNULL, start_new_session=True, close_fds=True)
        try:
            status = child.wait(timeout=0.3)
            if status:
                return f"Browser opener exited with status {status}; use the file URI."
        except subprocess.TimeoutExpired:
            pass
    except OSError as exc:
        return f"Could not launch browser opener: {exc}. Use the file URI."
    return "Browser opener launched (display is not verified)."


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("model", type=Path)
    parser.add_argument("--output", type=Path, help="Default: index.html beside the model")
    parser.add_argument("--check", action="store_true", help="Only validate; write/open nothing")
    parser.add_argument("--open", action="store_true", help="Detach the desktop browser opener")
    args = parser.parse_args()
    try:
        model_path = args.model.expanduser().resolve(strict=True)
        model = validate(json.loads(model_path.read_text(encoding="utf-8")))
        if args.check:
            print(f"Valid model: {model_path}")
            return 0
        output = (args.output or model_path.with_name("index.html")).expanduser().resolve()
        require(output != model_path, "Output must not overwrite the model")
        template = Path(__file__).resolve().parents[1] / "assets" / "page.html"
        payload = json.dumps({"model": model, "modelPath": str(model_path)}, ensure_ascii=False)
        # JSON lives inside a script element; never allow a closing tag to escape it.
        payload = payload.replace("&", "\\u0026").replace("<", "\\u003c").replace(">", "\\u003e")
        payload = payload.replace("\u2028", "\\u2028").replace("\u2029", "\\u2029")
        page = template.read_text(encoding="utf-8").replace("__EXPLANATION_DATA__", payload)
        output.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=output.parent, delete=False) as handle:
            handle.write(page)
            temporary = Path(handle.name)
        try:
            temporary.replace(output)
        finally:
            temporary.unlink(missing_ok=True)
        print(f"Rendered: {output}")
        print(output.as_uri())
        if args.open:
            print(open_browser(output))
        return 0
    except (OSError, ValueError, TypeError) as exc:
        print(f"visual-explain: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
