#! /usr/bin/env python3
"""
Extract dependencies like images and shapefiles from Mapnik XML files
"""

import os
import sys
import xml.etree.ElementTree as ET

style = sys.argv[1]
target = sys.argv[2]
base = sys.argv[3]

# collect dependencies here
# the style file itself is always a dependency
deps = [style]

# collect file sources
sources = {}

# where were we called from
basedir = os.getcwd()


def normalize_path(path):
    """normalize paths by removing e.g. /./ or /../"""

    # ignore paths that contain Mapnik expressions
    if '[' in path:
        return None

    dir = os.path.dirname(path)
    base = os.path.basename(path)

    # normalize dir path, directory path must exist
    realdir = os.path.realpath(dir or '.')
    if not os.path.isdir(realdir):
        return None

    if path.startswith('/'):
        # absolute path, nothing to remove
        return f"{realdir}/{base}"
    else:
        # relative path, remove basedir
        return realdir.replace(basedir + '/', '') + f"/{base}"


def add_dep(file):
    path = normalize_path(f"{base}/{file}")
    if path:
        deps.append(path)


# load the style file
root = ET.parse(style).getroot()

# collect all <FileSource> declarations
for param in root.iter('FileSource'):
    name = param.get('name', '').strip()
    sources[name] = ''.join(param.itertext()).strip()

# check whether the <Map> tag has a background image
for param in root.iter('Map'):
    file = param.get('background-image')
    if file:
        add_dep(file)

# collect all "file" parameter values from DataSources etc.
for param in root.iter('Parameter'):
    if param.get('name') == 'file':
        add_dep(''.join(param.itertext()).strip())

# collect all file attributes from symbolizers supporting these
for type in ['Point', 'Markers', 'Shield', 'LinePattern', 'PolygonPattern']:
    for param in root.iter(type + 'Symbolizer'):
        file = param.get('file')
        if file:
            source = param.get('base')
            if source in sources:
                file = sources[source] + '/' + file
            add_dep(file)

# generate dependency make rule
print(f"{target}: " + " ".join(deps))
