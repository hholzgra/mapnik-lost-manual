# Python examples and missing python-mapnik features

Could the book's XML examples also be shown as Python code? This
note answers that and lists everything the Python bindings cannot
express.

Tested on 2026-11-07 against:

- Mapnik 4.3.3, built from master, with `XML_PARSE_NOBASEFIX`
  added locally;
- python-mapnik 4.3.1, from `~/for-git-pull/python-mapnik` at
  v4.3.1-4-gcc2e8f606. That checkout has local changes in
  `src/mapnik_map.cpp`, but none to symbolizers.

## Summary

- 41 of the 107 non-disabled examples can be expressed with the
  current Python API. The other 66 need properties that have no
  setter, or child elements that have no Python class.
- `make check-python-bindings MAPNIK_SRC=~/for-git-pull/mapnik`
  (`tools/check-python-bindings.py --examples`) produces the lists
  below and the list of expressible examples.
- The biggest gaps are labels (`TextSymbolizer`,
  `ShieldSymbolizer`), `MarkersSymbolizer` and `GroupSymbolizer`.
- 52 examples use `dy` or `allow-overlap` on a `TextSymbolizer`,
  mostly for the standard point label. For 30 of them, these two are
  the only gaps.
- There is no generic way to set a property. The generic
  `mapnik.Symbolizer` wrapper (what `rule.symbolizers` contains)
  can read any property by its XML name (`sym['stroke-width']`,
  `getattr(sym, 'stroke-width')`), but has no `__setitem__` or
  `__setattr__`. The typed classes (`mapnik.LineSymbolizer`, ...)
  only have the properties each wrapper defines one by one.
  Unknown names raise `AttributeError`.

## Effort estimate

1. **Generator for the 41 expressible examples: about a day.** A
   script would walk the XML and write Python. It would:
   - map attribute names to property names (`stroke-width` →
     `stroke_width`; see the aliases below);
   - convert values to `mapnik.Color`, `mapnik.Expression` and the
     enums;
   - resolve `FileSource` names into plain paths;
   - turn `<Datasource>` parameters into
     `mapnik.Datasource(**params)`.

   Each generated script would be checked by rendering it and
   comparing pixels with the XML render.
2. **The rest needs python-mapnik changes.** The quick route is a
   generic `__setattr__`/`__setitem__` on symbolizers. It would
   look up the name in Mapnik's property table (`get_meta()`/
   `get_key()`) and convert the value according to the property's
   type. That would close most attribute gaps below at once. Text
   placements, `GroupSymbolizer` and layouts need separate
   wrappers. Rough guess: a few days of C++ work plus an upstream
   pull request.
3. **Writing them by hand** costs about the same per example as the
   generator, without the systematic coverage.

Suggestion for the book: a short chapter or appendix on how XML
maps to the Python API. It would use a few generated and checked
examples from the 41 and list the gaps below. Converting all
examples only makes sense once the bindings can set properties
generically.

## Method

1. The XML attributes each element accepts were collected with the
   probing code from `tools/check-attributes.py`. Candidates are the
   names from the book's tables plus string literals from the
   Mapnik source, and each one is probed in strict mode.
2. Each accepted name is looked up as a settable property (or a
   method) on the Python class of the same name. Before the lookup,
   `-` becomes `_`, and the aliases below are applied. Label
   attributes are also looked up on `mapnik.PlacementFinder`.
3. Deprecated attributes (those Mapnik logs a deprecation warning
   for) and XML-only features (see the end) are left out.
4. This is all done by `tools/check-python-bindings.py`. Its alias,
   XML-only and child element tables are at the top of the
   script.

Aliases, where the Python name differs from the XML name:

| XML | Python |
|-----|--------|
| `simplify` | `simplify_tolerance` |
| `rasterizer` (LineSymbolizer) | `line_rasterizer` |
| `transform` (ShieldSymbolizer) | `image_transform` |
| `face-name`, `size`, `fill`, `halo-fill`, `halo-radius`, label text (Text/ShieldSymbolizer) | `placement_finder.face_name`, `.text_size`, `.fill`, `.halo_fill`, `.halo_radius`, `.format_expression` |
| `text`, `text-face-name`, `text-size`, `text-fill`, `text-halo-fill`, `text-halo-radius` (ArcSymbolizer) | same via `placement_finder` (default `None`; assign a `mapnik.PlacementFinder()` first) |
| `<Font face-name>` in `<FontSet>` | `FontSet.add_face_name()` |
| `<Filter>`, `<ElseFilter>`, `<AlsoFilter>` | `Rule.filter`, `Rule.set_else()`, `Rule.set_also()` |
| `<MinScaleDenominator>`, `<MaxScaleDenominator>` | `Rule.min_scale`, `Rule.max_scale` |
| `<Parameters>` on `<Map>` | `Map.parameters` |
| `<RasterColorizer>`, `<stop>` | `RasterSymbolizer.colorizer`, `mapnik.RasterColorizer`, `add_stop()` |
| `default-color`, `default-mode`, `epsilon` on `RasterSymbolizer` | the same on `mapnik.RasterColorizer` |

## Missing attribute setters

These attributes are accepted in XML but have no Python setter.
Values can still be read through the generic `mapnik.Symbolizer`
wrapper, with the exception of text placements, see below.

### Map, Layer, Style

- **`Map`**: complete, apart from the special case
  `font-directory`. Python only has the global
  `mapnik.register_fonts(dir)`, not a per-map font directory.
- **`Layer`**: `comp-op`, `opacity`, `sort-by`.
- **`Style`**: `direct-image-filters`.
- `Rule`, `FontSet`: complete.

### Generic symbolizer attributes

These are missing on (almost) every symbolizer class:

- `extend`
- `simplify-algorithm`
- `smooth-algorithm`

### Per symbolizer

Missing in addition to the generic ones:

- **`PointSymbolizer`**: `transform`.
- **`LineSymbolizer`**: `offset`.
- **`PolygonSymbolizer`**, **`BuildingSymbolizer`**,
  **`DebugSymbolizer`**: none.
- **`DotSymbolizer`**: complete.
- **`RasterSymbolizer`**: `filter-factor`, `mode`.
- **`PolygonPatternSymbolizer`**: `gamma`, `gamma-method`,
  `opacity`, `transform`.
- **`LinePatternSymbolizer`**:
  - `alignment`, `line-pattern`, `offset`, `opacity`,
    `transform`;
  - the stroke attributes used with `line-pattern="repeat"`:
    `stroke-dasharray`, `stroke-linecap`, `stroke-linejoin`,
    `stroke-miterlimit`, `stroke-width`.
- **`MarkersSymbolizer`**: only `file`, `width`, `height` and
  `allow_overlap` exist. Missing:
  - styling: `fill`, `fill-opacity`, `opacity`, `stroke`,
    `stroke-dasharray`, `stroke-dashoffset`, `stroke-gamma`,
    `stroke-gamma-method`, `stroke-linecap`, `stroke-linejoin`,
    `stroke-miterlimit`, `stroke-opacity`, `stroke-width`;
  - geometry: `offset`, `transform`;
  - placement: `placement`, `multi-policy`, `spacing`,
    `spacing-offset`, `max-error`, `direction`, `avoid-edges`,
    `ignore-placement`.
- **`ArcSymbolizer`**:
  - `comp-op`;
  - the label attributes `text-allow-overlap`,
    `text-character-spacing`, `text-font-feature-settings`,
    `text-fontset-name`, `text-halo-opacity`, `text-opacity`,
    `text-transform`.
- **`TextSymbolizer`**: only `halo_comp_op` and the five font
  properties of `PlacementFinder` exist. Missing:
  - placement: `placement`, `placement-type`, `placements`,
    `spacing`, `repeat-distance`, `minimum-distance`,
    `minimum-padding`, `minimum-path-length`, `margin`,
    `label-position-tolerance`, `max-char-angle-delta`,
    `avoid-edges`, `allow-overlap`, `largest-bbox-only`, `upright`,
    `grid-cell-width`, `grid-cell-height`;
  - position: `dx`, `dy`, `offset`, `orientation`,
    `rotate-displacement`, `horizontal-alignment`,
    `vertical-alignment`, `justify-alignment`;
  - wrapping: `wrap-width`, `wrap-before`, `wrap-character`,
    `repeat-wrap-character`, `line-spacing`, `text-ratio`;
  - font and text: `fontset-name`, `character-spacing`,
    `font-feature-settings`, `lang`, `text-transform`, `opacity`;
  - halo: `halo-opacity`, `halo-rasterizer`, `halo-transform`.

  Note that `fontset-name` is missing, so `FontSet`s can be defined
  in Python but not used for labels.
- **`ShieldSymbolizer`**: the same gaps as `TextSymbolizer` (with
  `text-opacity` instead of `opacity` and no `halo-transform`).
  `file`, `shield_dx`, `shield_dy`, `unlock_image`, `offset` and
  `image_transform` exist.
- **`GroupSymbolizer`**: only the generic attributes exist. All
  placement attributes are missing: `placement`, `spacing`,
  `repeat-distance`, `repeat-key`, `minimum-distance`,
  `minimum-padding`, `minimum-path-length`, `margin`,
  `label-position-tolerance`, `max-char-angle-delta`,
  `avoid-edges`, `allow-overlap`, `largest-bbox-only`, `upright`,
  `grid-cell-width`, `grid-cell-height`, `num-columns`,
  `start-column`.

## Missing structures

These go beyond single attributes. Each needs a new wrapper class:

- **Text placements**:
  - Python only has `PlacementFinder`, which wraps a "dummy"
    (single) placement and has six properties.
  - Missing are `placement-type="simple"` and `"list"`, the
    `<Placement>` children of a list placement, and all
    placement-level properties listed above.
  - Reading the placements of a symbolizer loaded from XML through
    the generic wrapper fails: `getattr(sym, 'text-placements')`
    prints `Can't convert to Python object
    [St10shared_ptrIN6mapnik15text_placementsEE]` and returns
    `None`.
- **Formatting tree**: `<Format>` and `<Layout>` children of text
  and shield symbolizers. Python only has the plain
  `format_expression`.
- **GroupSymbolizer contents**: `<GroupRule>`, `<SimpleLayout>`,
  `<PairLayout>` and the group properties. A `GroupSymbolizer`
  can be created in Python, but it can't be filled.

## XML-only, no Python equivalent needed

These are loader conveniences rather than map features. Python code
does the same with plain variables:

- `<FileSource>` and the symbolizers' `base` attribute: build the
  path in Python.
- `<Datasource name="...">` templates and `base` on a datasource:
  reuse a dict of parameters.
- `<Include>`, XInclude and entities: Python modules and functions.
- `<Map minimum-version>`: compare `mapnik.version()` or `mapnik.version_string()`.

## Deprecated, left out

- `Layer` `minzoom`/`maxzoom`: aliases for the scale denominators,
  deprecated.
- `ShieldSymbolizer` `no-text`: deprecated.
- `MarkersSymbolizer` `marker-type`: Mapnik 2.0 compatibility;
  `file="shape://ellipse"` replaces it.
