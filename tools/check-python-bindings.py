#! /usr/bin/env python3
# List the parts of Mapnik's XML style format that the Python bindings
# (python-mapnik) cannot express.
#
# The attributes each XML element accepts are found with the probing
# code of check-attributes.py (candidate names from the book's tables
# and, with --mapnik-src or $MAPNIK_SRC, from the Mapnik source).  Each
# accepted attribute is then looked up as a settable property on the
# Python class of the same name, after applying the name mappings
# below.  With --examples, the example styles that only use features
# Python can express are listed, too.
#
# See notes/python-bindings.md for the background.

import argparse
import glob
import importlib.util
import os
import sys
import xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location(
    "check_attributes", os.path.join(HERE, "check-attributes.py"))
ca = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ca)
mapnik = ca.mapnik

# (element, XML attribute) -> Python property name, where it is not
# simply the XML name with "-" replaced by "_"
ALIASES = {
    ("*", "simplify"): "simplify_tolerance",
    ("LineSymbolizer", "rasterizer"): "line_rasterizer",
    ("ShieldSymbolizer", "transform"): "image_transform",
    ("TextSymbolizer", "size"): "text_size",
    ("ShieldSymbolizer", "size"): "text_size",
    ("ArcSymbolizer", "text"): "format_expression",
    ("Font", "face-name"): "add_face_name",
}

# label attributes live on the PlacementFinder (a single "dummy" text
# placement) instead of the symbolizer itself
LABELS = {"TextSymbolizer", "ShieldSymbolizer", "ArcSymbolizer"}

# attributes that RasterSymbolizer passes on to its RasterColorizer
COLORIZER = {"default-color", "default-mode", "epsilon"}

# Python class for elements whose attributes are set elsewhere
PY_CLASS = {"Font": "FontSet"}

# XML-only conveniences, nothing to do in Python
NOT_NEEDED = {
    ("*", "base"): "FileSource reference, build the path in Python",
    ("FileSource", "*"): "build paths in Python",
    ("Map", "minimum-version"): "compare mapnik.version() instead",
    ("Style", "name"): "given to Map.append_style()",
    ("MarkersSymbolizer", "marker-type"):
        "Mapnik 2.0 compatibility, use file=\"shape://...\"",
}

# accepted, but only partially available in Python
PARTIAL = {
    ("Map", "font-directory"):
        "only the global mapnik.register_fonts(), not per map",
}

# child elements that need a Python class of their own; element ->
# class names that would provide it
STRUCTURES = {
    "Placement": ["TextPlacementList", "PlacementList"],
    "Format": ["FormatNode", "Format"],
    "Layout": ["LayoutNode", "Layout"],
    "GroupRule": ["GroupRule"],
    "SimpleLayout": ["SimpleLayout"],
    "PairLayout": ["PairLayout"],
}


def lookup(table, element, attr):
    for key in ((element, attr), ("*", attr), (element, "*")):
        if key in table:
            return table[key]
    return None


def settable(cls, name):
    """cls has a writable property or a method of that name"""
    if cls is None:
        return False
    member = getattr(cls, name, None)
    if member is None:
        return False
    if isinstance(member, property):
        return member.fset is not None
    return callable(member)


def label_names(element, attr):
    """candidate PlacementFinder property names for a label attr"""
    names = [attr.replace("-", "_")]
    if element == "ArcSymbolizer" and attr.startswith("text-"):
        names.insert(0, attr[len("text-"):].replace("-", "_"))
    if attr == "size" or attr == "text-size":
        names.append("text_size")
    return names


def available(element, attr):
    """True, or False, or a string explaining a partial mapping"""
    if lookup(NOT_NEEDED, element, attr):
        return True
    partial = lookup(PARTIAL, element, attr)
    if partial:
        return partial
    cls = getattr(mapnik, PY_CLASS.get(element, element), None)
    name = lookup(ALIASES, element, attr) or attr.replace("-", "_")
    if settable(cls, name):
        return True
    if element in LABELS:
        if settable(mapnik.PlacementFinder, name):
            return True
        if any(settable(mapnik.PlacementFinder, n)
               for n in label_names(element, attr)):
            return True
    if element == "RasterSymbolizer" and attr in COLORIZER:
        return settable(mapnik.RasterColorizer, name)
    return False


def generic_setter():
    """can mapnik.Symbolizer set arbitrary properties by name?"""
    sym = mapnik.Symbolizer
    return any(n in sym.__dict__ for n in ("__setattr__",
                                           "__setitem__"))


def missing_structures():
    return {e: names for e, names in STRUCTURES.items()
            if not any(hasattr(mapnik, n) for n in names)}


def check_examples(gaps, structures):
    """example -> sorted list of what Python cannot express"""
    result = {}
    for path in sorted(glob.glob(os.path.join(ca.EXAMPLES, "**",
                                              "*.xml"),
                                 recursive=True)):
        rel = os.path.relpath(path, ca.EXAMPLES)
        if rel.split(os.sep)[0] in ("disabled", "tmp", "data",
                                    "symbols"):
            continue
        try:
            root = ET.parse(path).getroot()
        except ET.ParseError as e:
            result[rel] = ["XML error: %s" % e]
            continue
        missing = set()
        for el in root.iter():
            if el.tag in structures:
                missing.add("<%s>" % el.tag)
            for attr in el.attrib:
                if (el.tag, attr) in gaps:
                    missing.add("%s %s" % (el.tag, attr))
        result[rel] = sorted(missing)
    return result


def main():
    parser = argparse.ArgumentParser(
        description="List XML style features the Python bindings "
                    "cannot express")
    parser.add_argument("--mapnik-src",
                        default=os.environ.get("MAPNIK_SRC"),
                        help="Mapnik source tree matching the "
                             "installed version")
    parser.add_argument("--examples", action="store_true",
                        help="also list which examples Python "
                             "could express")
    args = parser.parse_args()

    docs, _ = ca.parse_docs()
    candidates = set()
    for attrs in docs.values():
        candidates.update(attrs)
    if args.mapnik_src:
        candidates.update(ca.source_candidates(args.mapnik_src))
    else:
        print("note: no Mapnik source tree given "
              "(--mapnik-src or MAPNIK_SRC),\n"
              "      only checking names the book already mentions\n")

    with ca.QuietLog():
        elements = ca.available_elements()
    accepted, deprecated = {}, {}
    with ca.QuietLog() as log:
        for e in elements:
            status = {a: ca.probe(e, a, log) for a in candidates}
            accepted[e] = {a for a, s in status.items()
                           if s == "known"}
            deprecated[e] = {a for a, s in status.items()
                             if s == "deprecated"}

    try:
        from importlib.metadata import version
        py_version = version("mapnik")
    except Exception:
        py_version = "?"
    print("Mapnik %s, python-mapnik %s\n"
          % (mapnik.version_string(), py_version))

    gaps = set()
    total = 0
    for element in sorted(elements):
        missing, partial = [], []
        for attr in sorted(accepted[element]):
            state = available(element, attr)
            if state is True:
                continue
            if state is False:
                missing.append(attr)
                gaps.add((element, attr))
            else:
                partial.append("%s (%s)" % (attr, state))
        total += len(missing)
        if not (missing or partial):
            continue
        cls = PY_CLASS.get(element, element)
        print("%s%s" % (element, "" if hasattr(mapnik, cls)
                        else " (no Python class)"))
        if missing:
            print("  no setter: %s" % ", ".join(missing))
        for p in partial:
            print("  partial: %s" % p)
        dep = sorted(deprecated[element])
        if dep:
            print("  (deprecated, not counted: %s)" % ", ".join(dep))
        print()

    structures = missing_structures()
    if structures:
        print("Child elements without a Python class:")
        for e, names in sorted(structures.items()):
            print("  <%s> (looked for: %s)" % (e, ", ".join(names)))
        print()
    print("Generic property setter on mapnik.Symbolizer: %s\n"
          % ("yes" if generic_setter() else "no"))

    print("%d attribute(s) without a Python setter, "
          "%d child element(s) without a class"
          % (total, len(structures)))

    if args.examples:
        result = check_examples(gaps, structures)
        ok = [e for e, m in result.items() if not m]
        print("\n%d of %d examples can be expressed in Python:"
              % (len(ok), len(result)))
        for e in ok:
            print("  %s" % e)
        print("\nthe others need:")
        for e, m in result.items():
            if m:
                print("  %s: %s" % (e, ", ".join(m)))


if __name__ == "__main__":
    sys.exit(main())
