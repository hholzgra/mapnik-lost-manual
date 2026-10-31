#! /usr/bin/env python3
# Emit make dependencies for the rendered example images: each
# .png/.svg pair depends on its .xml style plus any files the style
# references (datasource files, background images, marker and pattern
# symbols).
#
# Relative paths inside the styles resolve against examples/, because
# that is where render.sh runs mapnik; references to files that do not
# exist (or that contain [expressions]) are silently dropped.

import os
import sys
import xml.etree.ElementTree as ET

BASE = "examples"
FILE_SYMBOLIZERS = ("Point", "Markers", "Shield",
                    "LinePattern", "PolygonPattern")


def normalize(path):
    basename = os.path.basename(path)
    if "[" in basename:
        return None
    dirname = os.path.realpath(os.path.dirname(path))
    if not os.path.isdir(dirname):
        return None
    cwd = os.getcwd()
    if dirname == cwd:
        return basename
    if dirname.startswith(cwd + os.sep):
        dirname = dirname[len(cwd) + 1:]
    return os.path.join(dirname, basename)


def style_deps(style):
    deps = [style]

    def add(path):
        dep = normalize(os.path.join(BASE, path))
        if dep and dep not in deps:
            deps.append(dep)

    root = ET.parse(style).getroot()

    sources = {}
    for fs in root.iter("FileSource"):
        sources[fs.get("name")] = (fs.text or "").strip()

    for param in root.iter("Parameter"):
        if param.get("name") == "file":
            add((param.text or "").strip())

    for m in root.iter("Map"):
        background = m.get("background-image")
        if background:
            add(background)

    for kind in FILE_SYMBOLIZERS:
        for sym in root.iter(kind + "Symbolizer"):
            file = sym.get("file")
            if not file:
                continue
            base = sym.get("base")
            if base in sources:
                file = sources[base] + "/" + file
            add(file)

    return deps


def main():
    styles = sys.argv[1:]
    if not styles:
        styles = sorted(
            os.path.join(top, name)
            for top, dirs, names in os.walk(BASE)
            if "disabled" not in top.split(os.sep)
            for name in names
            if name.endswith(".xml")
        )

    status = 0
    for style in styles:
        try:
            deps = style_deps(style)
        except ET.ParseError as e:
            print(f"{style}: {e}", file=sys.stderr)
            status = 1
            continue
        base = style[: -len(".xml")]
        print(f"{base}.png {base}.svg: {' '.join(deps)}")
    sys.exit(status)


if __name__ == "__main__":
    main()
