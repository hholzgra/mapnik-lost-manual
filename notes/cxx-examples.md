# C++ versions of the XML examples

Could the book's XML examples also be shown as C++ code that builds
the same map through the Mapnik API? This note covers how much of
the format C++ can express and what the effort would be. See
[python-bindings.md](python-bindings.md) for the same question about
Python.

Tested on 2026-11-07 against the installed Mapnik 4.3.3 (Debian
package built from master, with headers, `libmapnik.pc` and the
CMake config files).

## Summary

- **Coverage is complete.** The C++ API is what the XML loader
  (`src/load_map.cpp`) uses itself, so everything the XML format
  can express can be built in C++. This includes text placements,
  formatting trees, `GroupSymbolizer` and layouts. Only XML-only
  conveniences have no direct counterpart, and they don't need one
  (see below).
- **The code is long.** A label example with about 12 lines of XML
  becomes about 60 lines of C++.
- **A generator would need to know a lot about Mapnik's internals:**
  value types, enum names and the split of text properties over
  three structures. Estimated at 2 to 4 days, compared with about a
  day for the 41 examples Python can express.
- **Suggestion:** a few showcase examples in an appendix ("Building
  styles in C++"), not all of them.

## Test program

The test program builds a style using exactly the properties Python
cannot set:

- a `MarkersSymbolizer` with `fill`;
- a `TextSymbolizer` with `dy` and `allow-overlap`.

It reads an inline CSV datasource and renders to PNG. The XML
equivalent:

```xml
<Map srs="epsg:4326" background-color="white">
  <Style name="points">
    <Rule>
      <MarkersSymbolizer fill="red" width="10"/>
      <TextSymbolizer face-name="DejaVu Sans Book" size="12" dy="10"
                      allow-overlap="true">[name]</TextSymbolizer>
    </Rule>
  </Style>
  <Layer name="points" srs="epsg:4326">
    <StyleName>points</StyleName>
    <Datasource>
      <Parameter name="type">csv</Parameter>
      <Parameter name="inline">x,y,name
0,0,Origin
10,5,East</Parameter>
    </Datasource>
  </Layer>
</Map>
```

The C++ version (also in
[cxx-label-example.cpp](cxx-label-example.cpp)):

```cpp
#include <mapnik/map.hpp>
#include <mapnik/layer.hpp>
#include <mapnik/rule.hpp>
#include <mapnik/feature_type_style.hpp>
#include <mapnik/symbolizer.hpp>
#include <mapnik/datasource_cache.hpp>
#include <mapnik/font_engine_freetype.hpp>
#include <mapnik/agg_renderer.hpp>
#include <mapnik/image.hpp>
#include <mapnik/image_util.hpp>
#include <mapnik/expression.hpp>
#include <mapnik/text/placements/dummy.hpp>
#include <mapnik/text/formatting/text.hpp>

int main()
{
    using namespace mapnik;
    datasource_cache::instance().register_datasources(
        "/usr/lib/x86_64-linux-gnu/mapnik/4.0/input");
    freetype_engine::register_fonts("/usr/share/fonts", true);

    Map m(600, 300, "epsg:4326");
    m.set_background(color("white"));

    feature_type_style style;
    rule r;
    markers_symbolizer marker;
    put(marker, keys::fill, color("red"));
    put(marker, keys::width, 10.0);     // must be a double, see below
    r.append(std::move(marker));

    text_symbolizer text;
    auto placements = std::make_shared<text_placements_dummy>();
    auto& defaults = placements->defaults;
    defaults.format_defaults.face_name = "DejaVu Sans Book";
    defaults.format_defaults.text_size = 12.0;
    defaults.layout_defaults.dy = 10.0;
    defaults.set_format_tree(std::make_shared<formatting::text_node>(
        parse_expression("[name]")));
    put<text_placements_ptr>(text, keys::text_placements_, placements);
    put(text, keys::allow_overlap, true);
    r.append(std::move(text));
    style.add_rule(std::move(r));
    m.insert_style("points", std::move(style));

    parameters p;
    p["type"] = "csv";
    p["inline"] = "x,y,name\n0,0,Origin\n10,5,East\n";
    layer lyr("points", "epsg:4326");
    lyr.set_datasource(datasource_cache::instance().create(p));
    lyr.add_style("points");
    m.add_layer(lyr);

    m.zoom_all();
    image_rgba8 img(m.width(), m.height());
    agg_renderer<image_rgba8> ren(m, img);
    ren.apply();
    save_to_file(img, "label.png", "png");
}
```

Build and run:

```sh
g++ -std=c++17 -O1 cxx-label-example.cpp -o label \
    $(pkg-config --cflags --libs libmapnik)
./label
```

- Compiling takes about 7 seconds (`-O1`).
- The output shows the red markers with labels 10 pixels below
  them, as the XML version does.
- Instead of pkg-config, a CMake project can use
  `find_package(mapnik)`; the config files are in
  `/usr/lib/x86_64-linux-gnu/cmake/mapnik/`.

## What makes C++ harder than Python

- **Text properties are split over three structures.** In XML,
  they are flat attributes of `<TextSymbolizer>`. In C++:
  - font and colour settings (`face_name`, `text_size`, `fill`,
    `halo_*`, ...) are in `format_defaults`
    (`format_properties`);
  - positioning (`dx`, `dy`, `orientation`, `wrap_width`,
    alignments, ...) is in `layout_defaults`
    (`text_layout_properties`);
  - placement and collision settings are in `text_placements_*`
    (`dummy`, `simple`, `list`) and in the symbolizer's own keys
    (`allow_overlap`, `spacing`, ...).

  Which attribute goes where has to be looked up in
  `src/text/text_properties.cpp`.
- **The label text needs a formatting tree.** A plain label is one
  `formatting::text_node`. `<Format>` and `<Layout>` children
  become nested `format_node`/`layout_node`/`list_node` objects
  (`include/mapnik/text/formatting/`).
- **`GroupSymbolizer`** needs `group_symbolizer_properties`,
  `group_rule` objects and a layout (`simple_row_layout`,
  `pair_layout`) from `include/mapnik/group/`. It's doable, but
  verbose.
- **Value types are not checked.** `put(sym, keys::x, value)` stores
  whatever type it gets in the property variant (bool,
  `value_integer`, `value_double`, string, colour, expression,
  enum, ...). A wrong type compiles fine and fails silently at
  render time. In the test program,
  `put(marker, keys::width, 10)` with an `int` instead of `10.0`
  made the markers disappear completely, with no error or warning.
  A generator would have to take each property's type from
  Mapnik's property metadata (`get_meta()`, `property_types` in
  `symbolizer_keys.cpp`).
- **Enums use their C++ names**, e.g. `line_cap_enum::ROUND_CAP` for
  `stroke-linecap="round"` (`symbolizer_enumerations.hpp`).
- **Setup that XML gets for free:**
  - registering datasource plugins and fonts;
  - turning colours, expressions, transforms and dash arrays into
    their types (`parse_expression()`, `parse_transform()`, ...);
  - building `FileSource` paths.

## XML-only, no C++ equivalent needed

Same as for Python:

- `<FileSource>` and `base`: build the path in code.
- Datasource templates: reuse a `parameters` object.
- `<Include>`, XInclude and entities: code structure.
- `<Map minimum-version>`: compare `MAPNIK_VERSION` at compile time.

## Effort estimate

1. **Generator for all examples: about 2 to 4 days.**
   - It is harder than the Python one, because of the type and
     enum mapping and the three text structures.
   - As C++ has no gaps, it could cover all 107 examples.
   - Each generated program would be rendered and compared pixel by
     pixel with the XML render. That doubles as a test of the
     generator.
2. **Writing them by hand:**
   - about 15 minutes for a simple example;
   - about an hour for text, group or layout examples;
   - several days for all of them.
3. **Build integration**, needed either way:
   - a Makefile rule per example (pkg-config flags, about 7 seconds
     per compile, so about 12 minutes serially for all examples,
     less in parallel);
   - the pixel comparison against the XML render;
   - deciding whether `make check` should build them at all.

## Suggestion for the book

A short appendix "Building styles in C++" with three or four
showcase examples:

- a simple line/polygon style;
- a label with placement settings, like the test program;
- maybe a `GroupSymbolizer`.

It would show what the XML maps to internally without doubling the
size of the book. It should mention the silent type pitfall.
`demo/c++/rundemo.cpp` in the Mapnik source (387 lines) is an
existing reference for the basics: map setup, datasources, rendering
to different formats.
