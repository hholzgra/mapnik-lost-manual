#! /usr/bin/env python3
# Compare the attribute tables in the book against what the installed
# Mapnik actually accepts.
#
# Every candidate attribute name is probed by loading a tiny style in
# strict mode: Mapnik reports attributes it did not consume as
# "Unable to process some data ... attribute 'x'", so any other
# outcome (success, or a complaint about the value) means the
# attribute is known for that element.
#
# Candidate names come from the book's own tables and, when a Mapnik
# source tree is given (--mapnik-src or $MAPNIK_SRC), also from the
# string literals in the XML parsing code, so that attributes the book
# does not mention yet can be found, too.  The source tree is also
# used to look up default values for comparison with the book; it
# should match the installed Mapnik version.
#
# Known false positives (accepted, but meaningless or deliberately left
# out) go into tools/attributes-ignore.txt.

import argparse
import glob
import os
import re
import sys

import mapnik

TOP = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
EXAMPLES = os.path.join(TOP, "examples") + "/"
IGNORE_FILE = os.path.join(TOP, "tools", "attributes-ignore.txt")


# ---------------------------------------------------------------------
# probing

def pick_font():
    faces = list(mapnik.FontEngine.face_names())
    for face in ("DejaVu Sans Book", "Noto Sans Regular"):
        if face in faces:
            return face
    return faces[0]


FONT = pick_font()


def in_rule(sym, attrs="", body=""):
    return ('<Map><Style name="s"><Rule><%s %s{attrs}>%s</%s></Rule></Style></Map>'
            % (sym, attrs, body, sym))


# element -> XML template with a {attrs} placeholder; attributes already
# present in the template are required ones and count as known
ELEMENTS = {
    "Map":        '<Map {attrs}/>',
    "Layer":      '<Map><Style name="s"/><Layer name="l" {attrs}><StyleName>s</StyleName></Layer></Map>',
    "Style":      '<Map><Style name="s" {attrs}/></Map>',
    "Rule":       '<Map><Style name="s"><Rule {attrs}/></Style></Map>',
    "FontSet":    '<Map><FontSet name="f" {attrs}><Font face-name="%s"/></FontSet></Map>' % FONT,
    "Font":       '<Map><FontSet name="f"><Font face-name="%s" {attrs}/></FontSet></Map>' % FONT,
    "FileSource": '<Map><FileSource name="f" {attrs}>symbols</FileSource></Map>',
}
for _s in ("Point", "Markers", "Line", "Polygon", "Raster", "Building",
           "Dot", "Debug", "Group", "Arc"):
    ELEMENTS[_s + "Symbolizer"] = in_rule(_s + "Symbolizer")
for _s in ("LinePattern", "PolygonPattern"):
    ELEMENTS[_s + "Symbolizer"] = in_rule(_s + "Symbolizer", 'file="symbols/dot.svg" ')
ELEMENTS["TextSymbolizer"] = in_rule("TextSymbolizer", 'face-name="%s" ' % FONT, "[name]")
ELEMENTS["ShieldSymbolizer"] = in_rule("ShieldSymbolizer",
                                       'face-name="%s" file="symbols/dot.svg" ' % FONT, "[name]")

# attributes that are only read when another attribute is set as well
COMPANIONS = {
    ("TextSymbolizer", "placements"): 'placement-type="simple"',
    ("ShieldSymbolizer", "placements"): 'placement-type="simple"',
    ("ArcSymbolizer", "text-face-name"): 'text="[name]"',
}


def companions(element, attr):
    if (element, attr) in COMPANIONS:
        return COMPANIONS[(element, attr)]
    if element == "ArcSymbolizer" and attr.startswith("text-"):
        # the arc label attributes are only read along with a label
        return 'text="[name]" text-face-name="%s"' % FONT
    return ""

# a ShieldSymbolizer takes all TextSymbolizer attributes, and the book
# documents only the additional ones in the shield table
INHERITS = {"ShieldSymbolizer": "TextSymbolizer"}


def load(xml):
    m = mapnik.Map(10, 10)
    mapnik.load_map_from_string(m, xml, True, EXAMPLES)
    return m


def required_attrs(element):
    tag = re.search(r"<%s ([^>{]*)" % element, ELEMENTS[element])
    return set(re.findall(r'([\w-]+)=', tag.group(1))) if tag else set()


class QuietLog:
    """send Mapnik's log to a temp file while probing (deprecation
    warnings are read back from it), and PROJ's stderr chatter about
    invalid test values to /dev/null"""

    def __init__(self):
        import tempfile
        self.log = tempfile.NamedTemporaryFile(prefix="check-attributes", suffix=".log")

    def __enter__(self):
        mapnik.logger.use_file(self.log.name)
        mapnik.logger.set_severity(mapnik.severity_type.Warn)
        sys.stderr.flush()
        self.saved = os.dup(2)
        null = os.open(os.devnull, os.O_WRONLY)
        os.dup2(null, 2)
        os.close(null)
        return self

    def __exit__(self, *exc):
        os.dup2(self.saved, 2)
        os.close(self.saved)
        mapnik.logger.use_console()
        self.log.close()

    def new_messages(self):
        with open(self.log.name) as f:
            f.seek(getattr(self, "pos", 0))
            text = f.read()
            self.pos = f.tell()
        return text


def probe(element, attr, log):
    """'known', 'deprecated' or 'unknown'"""
    if attr in required_attrs(element):
        return "known"
    extra = companions(element, attr)
    xml = ELEMENTS[element].format(attrs='%s="1" %s' % (attr, extra))
    log.new_messages()
    try:
        load(xml)
        status = "known"
    except RuntimeError as e:
        msg = str(e)
        if "attribute '%s'" % attr in msg and "Unable to process" in msg:
            return "unknown"
        status = "known"  # it was parsed, but "1" is not a valid value
    if "'%s' is deprecated" % attr in log.new_messages():
        status = "deprecated"
    return status


def available_elements():
    """the elements whose bare template loads with this Mapnik build"""
    found = []
    for element, template in ELEMENTS.items():
        try:
            load(template.format(attrs=""))
            found.append(element)
        except RuntimeError:
            pass
    return found


# ---------------------------------------------------------------------
# the book's attribute tables

TITLE = re.compile(r"^\.(\w+)\b")
XREF = re.compile(r"<<[^,>]*,(.*?)>>")


def clean_name(cell):
    cell = XREF.sub(r"\1", cell)
    cell = re.sub(r"\[[\w-]+\]#(.*?)#", r"\1", cell)  # [line-through]#x#
    return cell.replace("((", "").replace("))", "").replace("`", "").strip()


def split_row(line):
    return [c.strip() for c in re.split(r"(?<!\\)\|", line)[1:]]


def parse_docs():
    """element -> {attribute: (default, file, line)}"""
    docs = {}
    files = sorted(glob.glob(os.path.join(TOP, "chapters", "**", "*.adoc"), recursive=True))
    for path in files:
        rel = os.path.relpath(path, TOP)
        with open(path) as f:
            lines = f.read().split("\n")
        element = None
        in_table = header_seen = False
        for no, line in enumerate(lines, 1):
            m = TITLE.match(line)
            if m and not in_table:
                element = m.group(1) if m.group(1) in ELEMENTS else None
                continue
            if re.match(r"^\|===+\s*$", line):
                if in_table:
                    in_table = False
                    element = None
                elif element:
                    in_table, header_seen = True, False
                    docs.setdefault(element, {})
                continue
            if not in_table or not line.startswith("|"):
                continue
            if not header_seen:
                header_seen = True
                continue
            cells = split_row(line)
            if not cells or re.match(r"^\d+\+", line[1:].lstrip()) or not cells[0]:
                continue  # section rows like '4+^d|*Text attributes*'
            name = clean_name(cells[0])
            default = cells[2] if len(cells) > 2 else ""
            docs[element][name] = (default, rel, no)
    return docs


# ---------------------------------------------------------------------
# Mapnik source tree: candidate names and default values

LITERAL = re.compile(r'"([a-z][a-z0-9]*(?:-[a-z0-9]+)*)"')

CANDIDATE_SOURCES = [
    "src/load_map.cpp",
    "src/symbolizer_keys.cpp",
    "src/text/*.cpp",
    "src/text/formatting/*.cpp",
    "src/text/placements/*.cpp",
    "src/group/*.cpp",
]


def read(src, rel):
    with open(os.path.join(src, rel)) as f:
        return f.read()


def source_candidates(src):
    names = set()
    for pattern in CANDIDATE_SOURCES:
        for path in glob.glob(os.path.join(src, pattern)):
            with open(path) as f:
                names.update(LITERAL.findall(f.read()))
    return names


def key_names(src):
    """keys::xxx enum identifier -> XML attribute name"""
    hpp = read(src, "include/mapnik/symbolizer_keys.hpp")
    body = hpp[hpp.index("enum class keys"):]
    body = re.sub(r"//.*", "", body[body.index("{") + 1:body.index("}")])
    keys = [k.split("=")[0].strip() for k in body.split(",") if k.strip()]
    names = re.findall(r'property_meta_type\{\s*"([^"]+)"',
                       read(src, "src/symbolizer_keys.cpp"))
    if len(names) != len([k for k in keys if k != "MAX_SYMBOLIZER_KEY"]):
        print("warning: symbolizer_keys.hpp and .cpp differ in length, "
              "guessing names for default values", file=sys.stderr)
        return {k: k.replace("_", "-") for k in keys}
    return dict(zip(keys, names))


def enum_strings(src):
    """C++ enumerator -> XML string, e.g. GAMMA_POWER -> power"""
    table = {}
    text = read(src, "src/symbolizer_enumerations.cpp")
    for enumerator, string in re.findall(r'(?:\w+::)?(\w+)\s*,\s*"([^"]+)"\s*\}', text):
        table[enumerator] = string
    for rel in ("src/simplify.cpp", "src/image_compositing.cpp"):
        for enumerator, string in re.findall(r'\((\w+),\s*"([^"]+)"\)', read(src, rel)):
            table.setdefault(enumerator, string)
    return table


def cpp_value(expr, enums):
    """translate a C++ default value expression into XML notation"""
    expr = expr.strip()
    m = re.match(r"color\((\d+),\s*(\d+),\s*(\d+)\)$", expr)
    if m:
        return "rgb(%s,%s,%s)" % m.groups()
    if re.match(r"^-?\d+(\.\d*)?$", expr) or expr in ("true", "false"):
        return expr
    m = re.match(r"^(?:[\w:]+::)?(\w+)$", expr)
    if m and m.group(1) in enums:
        return enums[m.group(1)]
    return None


# XML names shared by several keys, and which key each element uses
SHARED_NAMES = {
    ("PointSymbolizer", "placement"): "point_placement_type",
    ("MarkersSymbolizer", "placement"): "markers_placement_type",
}

DEFAULTS_HPP = "symbolizer_default_values.hpp"


def symbolizer_defaults(src):
    """{key name: (default, origin)} plus {(symbolizer, name): (default,
    origin)}, the latter from symbolizer-specific key choices and from
    fallback values given where the AGG renderer reads the property"""
    names = key_names(src)
    enums = enum_strings(src)
    by_key = {}
    hpp = read(src, "include/mapnik/" + DEFAULTS_HPP)
    for key, expr in re.findall(
            r"symbolizer_default<[^,]+,\s*keys::(\w+)>\s*\{[^}]*?return\s+([^;]+);", hpp):
        value = cpp_value(expr, enums)
        if value is not None and key in names:
            by_key[key] = value
    generic, shared = {}, set()
    for key, value in by_key.items():
        name = names[key]
        if name in generic and generic[name][0] != value:
            shared.add(name)
        generic[name] = (value, DEFAULTS_HPP)
    for name in shared:
        del generic[name]
    specific = {}
    for (element, name), key in SHARED_NAMES.items():
        if key in by_key:
            specific[(element, name)] = (by_key[key], DEFAULTS_HPP)
    for path in glob.glob(os.path.join(src, "src/agg/process_*_symbolizer.cpp")):
        sym = os.path.basename(path)[len("process_"):-len("_symbolizer.cpp")]
        sym = "".join(p.capitalize() for p in sym.split("_")) + "Symbolizer"
        with open(path) as f:
            text = f.read()
        for key, expr in re.findall(
                r"get<[^>]*>\(\s*sym\s*,\s*keys::(\w+)\s*,[^,]+,[^,]+,\s*([^)]+?)\s*\)", text):
            value = cpp_value(expr, enums)
            if value is not None and key in names:
                specific[(sym, names[key])] = (value, os.path.basename(path))
    return generic, specific


def runtime_defaults(element):
    """defaults Mapnik writes out itself when saving with explicit
    defaults (Map, Style and text properties only)"""
    xml = mapnik.save_map_to_string(load(ELEMENTS[element].format(attrs="")), True)
    tag = re.search(r"<%s\b([^>]*)>" % element, xml)
    if not tag:
        return {}
    required = required_attrs(element)
    return {name: (value, "save_map")
            for name, value in re.findall(r'([\w-]+)="([^"]*)"', tag.group(1))
            if name not in required}


# ---------------------------------------------------------------------
# comparing default values

NO_CLAIM = {"", "none", "?", "-", "n/a", "auto detected"}


def normalize(value):
    value = value.strip().strip("`'\"").strip()
    low = value.lower()
    if low in NO_CLAIM or "todo" in low:
        return None
    try:
        return ("num", float(value))
    except ValueError:
        pass
    if low in ("true", "false"):
        return ("bool", low)
    try:
        c = mapnik.Color(value)
        return ("color", (c.r, c.g, c.b, c.a))
    except (RuntimeError, ValueError, TypeError):
        pass
    return ("str", low)


def defaults_differ(doc_value, src_value):
    a, b = normalize(doc_value), normalize(src_value)
    if a is None or b is None or a[0] != b[0]:
        return False  # nothing to compare, or e.g. "false" for "unset"
    return a != b


# ---------------------------------------------------------------------

def read_ignores():
    ignores = set()
    if os.path.exists(IGNORE_FILE):
        with open(IGNORE_FILE) as f:
            for line in f:
                line = line.split("#")[0].split()
                if len(line) == 2:
                    ignores.add(tuple(line))
    return ignores


def ignored(ignores, element, attr):
    return (element, attr) in ignores or ("*", attr) in ignores or (element, "*") in ignores


def main():
    parser = argparse.ArgumentParser(
        description="Compare the book's attribute tables against the installed Mapnik")
    parser.add_argument("--mapnik-src", default=os.environ.get("MAPNIK_SRC"),
                        help="Mapnik source tree matching the installed version")
    parser.add_argument("--strict", action="store_true",
                        help="also fail on undocumented attributes and default mismatches")
    args = parser.parse_args()

    docs = parse_docs()
    ignores = read_ignores()
    with QuietLog():
        elements = available_elements()

    candidates = set()
    for attrs in docs.values():
        candidates.update(attrs)
    generic = specific = {}
    if args.mapnik_src:
        candidates.update(source_candidates(args.mapnik_src))
        generic, specific = symbolizer_defaults(args.mapnik_src)
    else:
        print("note: no Mapnik source tree given (--mapnik-src or MAPNIK_SRC),\n"
              "      only checking names the book already mentions\n")

    accepted, deprecated = {}, {}
    with QuietLog() as log:
        for e in elements:
            status = {a: probe(e, a, log) for a in sorted(candidates)}
            accepted[e] = {a for a, s in status.items() if s != "unknown"}
            deprecated[e] = {a for a, s in status.items() if s == "deprecated"}
        src_defaults = {e: runtime_defaults(e) for e in elements}

    def documented(element):
        names = set(docs.get(element, {}))
        if element in INHERITS:
            names |= set(docs.get(INHERITS[element], {}))
        return names

    # attributes (nearly) every symbolizer takes (symbolizer_base), reported
    # once instead of for each symbolizer
    symbolizers = [e for e in elements if e.endswith("Symbolizer")]
    common = {a for a in candidates
              if sum(a in accepted[s] for s in symbolizers) >= 0.8 * len(symbolizers)}

    rejected = undocumented = mismatched = 0

    print("Mapnik %s, %d candidate attribute names, %d elements\n"
          % (mapnik.version_string(), len(candidates), len(elements)))

    for element in sorted(set(elements) | set(docs)):
        lines = []
        doc = docs.get(element, {})
        if element not in elements:
            lines.append("  not available in this Mapnik build, table not checked")
        else:
            for attr, (default, path, no) in sorted(doc.items()):
                if ignored(ignores, element, attr):
                    continue
                if attr not in accepted[element]:
                    lines.append("  ERROR  %s:%d: '%s' is not accepted by Mapnik" % (path, no, attr))
                    rejected += 1
                elif attr in deprecated[element]:
                    lines.append("  note   %s:%d: '%s' is deprecated" % (path, no, attr))
            extra = accepted[element] - documented(element)
            if element in symbolizers:
                extra -= common
                for attr in sorted(common - accepted[element]):
                    if not ignored(ignores, element, attr):
                        lines.append("  does not take the common symbolizer attribute: %s" % attr)
            for attr in sorted(extra):
                if ignored(ignores, element, attr):
                    continue
                if attr in deprecated[element]:
                    lines.append("  undocumented, but deprecated: %s" % attr)
                else:
                    lines.append("  undocumented: %s" % attr)
                    undocumented += 1
            for attr, (default, path, no) in sorted(doc.items()):
                src = src_defaults[element].get(attr, specific.get((element, attr), generic.get(attr)))
                if src is not None and defaults_differ(default, src[0]) \
                        and not ignored(ignores, element, "default:" + attr):
                    lines.append("  default? %s:%d: '%s' documented as %s, %s says %s"
                                 % (path, no, attr, default.strip(), src[1], src[0]))
                    mismatched += 1
            if not doc:
                lines.insert(0, "  no attribute table in the book")
        if lines:
            print(element)
            print("\n".join(lines))
            print()

    if symbolizers:
        print("Common symbolizer attributes (taken by most symbolizers):")
        for attr in sorted(common):
            if ignored(ignores, "*Symbolizer", attr):
                continue
            where = [s[:-len("Symbolizer")] for s in symbolizers if attr in documented(s)]
            print("  %-20s documented for: %s" % (attr, ", ".join(where) or "none"))
        print()

    print("%d documented attribute(s) not accepted, %d undocumented, "
          "%d possible default mismatch(es)" % (rejected, undocumented, mismatched))
    if mismatched:
        print("(defaults derived from the source are a hint only, some are computed\n"
              " at render time; confirmed false alarms go into %s as\n"
              " 'Element default:attribute')" % os.path.relpath(IGNORE_FILE, TOP))
    failed = rejected or (args.strict and (undocumented or mismatched))
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
