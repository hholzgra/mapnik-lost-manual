#! /usr/bin/env python3
# Emit the book's make dependencies as a BOOK_DEPS variable:
# every .adoc file pulled in via include::, recursively, plus every
# file referenced by include:: (example sources) or image::.
#
# include:: paths are relative to the including document (or to the
# book root when written with the {sourcedir} attribute); image::
# paths are always relative to the book root.

import os
import re
import sys

INCLUDE = re.compile(r"include::([^\[]+)\[")
IMAGE = re.compile(r"image::([^\[]+)\[")
SOURCEDIR = re.compile(r"\{sourcedir\}/(.*)")


def normalize(arg, dirname=""):
    m = SOURCEDIR.match(arg)
    if m:
        return m.group(1)
    if dirname:
        return os.path.normpath(os.path.join(dirname, arg))
    return arg


def parse(path, deps):
    dirname = os.path.dirname(path)
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line.startswith("//"):
                continue
            m = INCLUDE.search(line)
            if m and "://" not in m.group(1):
                dep = normalize(m.group(1), dirname)
                if dep not in deps:
                    deps.add(dep)
                    if dep.endswith(".adoc"):
                        parse(dep, deps)
            m = IMAGE.search(line)
            if m and "://" not in m.group(1):
                deps.add(normalize(m.group(1)))


def main():
    deps = set()
    parse(sys.argv[1], deps)
    print("BOOK_DEPS =", " ".join(sorted(deps)))


if __name__ == "__main__":
    main()
