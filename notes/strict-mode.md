# Validating styles: strict mode

Mapnik has no XML schema (XSD, DTD or RelaxNG) for its style
format. The closest thing to validation is the loader's *strict
mode*. Everything below comes from reading `src/load_map.cpp` in
`~/for-git-pull/mapnik` (v4.3.2-62-g8d105d24c) and testing against
the installed Mapnik 4.3.3.

## No schema

- A draft DTD, `utils/xml/mapnik.dtd`, was added in December 2010
  ([mapnik#684](https://github.com/mapnik/mapnik/issues/684)).
  It covered only the 2.0-era format.
- It was removed as unmaintained in August 2012 (commit
  `cbd45941b`, refs
  [mapnik#1402](https://github.com/mapnik/mapnik/issues/1402)).
  Nothing has replaced it.
- `src/libxml2_loader.cpp` parses with `XML_PARSE_DTDLOAD`, which
  loads a DTD only so that entities (`<!ENTITY>` includes) can be
  resolved. It does not set `XML_PARSE_DTDVALID`, so documents are
  never checked against a DTD.

## Turning it on

- C++: `mapnik::load_map(map, filename, strict, base_path)` and
  `load_map_string(...)`. `strict` defaults to `false`.
- Python: `mapnik.load_map(m, filename, strict=False, base_path="")`
  and `mapnik.load_map_from_string(m, xml, strict=False,
  base_path="")`.
- The `mapnik-render` utility always loads in strict mode
  (`utils/mapnik-render/mapnik-render.cpp`), and has no option to
  turn it off.

In strict mode, the first problem found raises a `config_error`
(`RuntimeError` in Python), and the map is not usable. Without
strict mode, the same problems are either logged or silently
ignored, and loading carries on.

A minimal checker:

```python
import sys
import mapnik

m = mapnik.Map(10, 10)
try:
    mapnik.load_map(m, sys.argv[1], True)
except RuntimeError as e:
    sys.exit(str(e))
```

## How unknown elements and attributes are found

There is no list of allowed names. Instead, the parser marks every
element, attribute and text node it reads as *processed*
(`xml_node::set_processed()`, `get_attr()`/`get_opt_attr()` mark
attributes). After the whole map has been parsed,
`map_parser::find_unused_nodes()` walks the tree and reports
everything that is left over:

```
Unable to process some data while parsing 'style.xml':
* attribute 'strok' with value 'red' at line 7
* node 'Stile' at line 12
* text 'hello' at line 15
```

Things to know about this check:

- It collects **all** leftovers into one message. Every other
  strict-mode error stops at the first problem.
- When an element is left over, its attributes and children are not
  listed separately.
- Comments are not reported.
- Without strict mode, the same message is logged at error level,
  which is the default log severity, so it is visible by default.
- A `<Layer status="off">` is skipped entirely (`set_ignore(true)`),
  so typos inside a disabled layer are never reported, not even in
  strict mode.
- `<Parameter>` elements of a `<Datasource>` are all consumed, so
  misspelled parameter names (`<Parameter name="bogus">`) are not
  reported. Whether the datasource plugin complains is up to the
  plugin. The CSV plugin does not complain about unknown
  parameters.
- `tools/check-attributes.py` relies on this check: it probes
  candidate attribute names by loading tiny styles in strict mode and
  checking for the "attribute 'x'" message.

## What strict mode adds

Each of these makes loading fail in strict mode. The second column
says what happens without strict mode.

| Check | Without strict mode |
|-------|---------------------|
| Unknown element, attribute or text node (see above) | error logged |
| `<Layer>` refers to a `<StyleName>` that has no `<Style>` (`check_styles()`) | silently ignored |
| Empty `<StyleName/>` | warning (not shown at default severity) |
| Two `<Style>` elements with the same name | error logged, second style dropped |
| `face-name` of a `TextSymbolizer`/`ShieldSymbolizer` that is not a registered font | silently accepted (render-time behaviour not tested) |
| Any `<Font face-name>` in a `<FontSet>` not found | missing fonts silently dropped from the fontset; loading fails only if none of its fonts can be found |
| `<Map font-directory>` that registers no fonts | silently ignored |
| `<Map maximum-extent>` / `<Layer maximum-extent>` that does not parse | error logged, ignored |
| `<Layer sort-by>` that does not parse | error logged, ignored |

Font names given through `fontset-name` are not checked again on
the symbolizer: the fontset was checked when it was defined.

## Errors in both modes

These always make loading fail, strict or not:

- Malformed XML.
- `<Map minimum-version>` newer than the running Mapnik.
- Values that cannot be parsed, for example `stroke="nocolor"`,
  `stroke-linecap="pointy"`, `<MinScaleDenominator>x`, or a broken
  `<Filter>` expression.
- An unknown `fontset-name`.
- A symbol `file` that does not exist (unless the path is an
  expression).
- Datasource errors raised by the plugin while the layer is
  created.

## What strict mode does not catch

- **Bare words in numeric attributes.** Numeric attributes accept
  expressions, and a bare word is accepted as one, whatever it
  means. `stroke-width="abc"` (or `opacity="abc"`, `offset="abc"`,
  `smooth="abc"`) loads without an error even in strict mode, and
  `save_map` writes it back as `0`. `stroke-width="true"` becomes
  `1`. Only input that fails to parse, such as `"1.5x"` or `"2+"`,
  is rejected.
- **Values out of range**, such as a negative `stroke-width`.
- **Unused styles**: a `<Style>` that no layer refers to.
- **Misspelled datasource parameters**, see above.
- **Anything inside a disabled layer**, see above.
- **Render-time problems**, such as labels that are never placed or
  a field name that does not exist in the data.

## Status of the book's own examples

Since 2026-11-06, `examples/render.py` loads the examples in strict
mode, so `make check` and the pre-commit hook fail on typos in an
example instead of rendering it with the misspelled attribute
ignored. When the switch was made, all examples outside `disabled/`
loaded fine in strict mode. The only failure was
`examples/disabled/PointSymbolizer-base.xml`, which refers to the
missing `bug.svg` and fails in non-strict mode, too.
## Ideas for the book

- A short "Validating styles" section, probably in the chapter on
  the `<Map>` element or in an appendix. It would cover:
  - that there is no schema;
  - how to load in strict mode from C++, Python and
    `mapnik-render`;
  - the table of what strict mode checks;
  - the list of what it does not catch, especially the bare-word
    case.
- Possibly an example script under `tools/` or `examples/` that
  validates a style file.
