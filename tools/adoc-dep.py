#! /usr/bin/env python3
"""
Generate a make dependency rule for an AsciiDoc file

Collects all files pulled in via include:: and image:: macros,
recursively descending into included .adoc files
"""

import os
import re
import sys


def normalize(arg, dir=None):
    m = re.search(r'\{sourcedir\}/(.*)', arg)
    if m:
        return m.group(1)
    if dir:
        return f"{dir}/{arg}"
    return arg


def parse_file(file, dir=None):
    includes = set()

    path = f"{dir}/{file}" if dir else file

    with open(path) as f:
        for line in f:
            line = line.strip()

            if not line:
                continue
            if line.startswith('//'):
                continue

            m = re.search(r'include::([^\[]+)', line)
            if m:
                new_file = normalize(m.group(1), dir)
                includes.add(new_file)
                if new_file.endswith('.adoc'):
                    includes |= parse_file(os.path.basename(new_file),
                                           os.path.dirname(new_file))

            m = re.search(r'image::([^\[]+)', line)
            if m:
                includes.add(normalize(m.group(1)))

    return includes


file = sys.argv[1]

includes = sorted(parse_file(file))

print(f"{file}: " + " ".join(includes))
