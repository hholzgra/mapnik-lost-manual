# `<Layer sort-by="...">`

Not documented in the Mapnik wiki or on mapnik.org. Everything
below comes from reading the source in `~/for-git-pull/mapnik` and
testing against Mapnik 4.3.3.

## Origin

- Added by Artem Pavlenko in
  [mapnik#4532](https://github.com/mapnik/mapnik/pull/4532),
  merged 2025-10-28.
- The first release containing it is v4.1.4, so examples need
  `minimum-version="4.1.4"`.
- Code:
  - `include/mapnik/util/sort_by.hpp` (parser)
  - `src/load_map.cpp`, `src/save_map.cpp`
  - `include/mapnik/feature_style_processor_impl.hpp` (rendering)
  - `include/mapnik/util/featureset_buffer.hpp` (the sort itself)

## What it does

Normally, a layer's features are drawn in the order the datasource
returns them. With `sort-by`, Mapnik instead reads all of the
layer's features into memory and sorts them by one attribute. It
then runs every active style of the layer over that sorted list.

This affects two things:

- **Stacking order:** later features are drawn on top of earlier
  ones.
- **Label priority:** placement is first come, first served, so
  features that come first win collisions. For example,
  `sort-by="population DESC"` gives big cities' labels priority.

PostGIS users would normally use `ORDER BY` in the query instead.
`sort-by` brings the same thing to datasources that can't sort
themselves: Shapefile, CSV, GeoJSON, OGR, and so on.

## Syntax

    sort-by="column"         ascending (default)
    sort-by="column ASC"
    sort-by="column DESC"    ASC/DESC are case-insensitive

- The value is one bare column name made of the characters
  `[a-zA-Z0-9_-]`. It is not an `[expression]`.
- There is no second sort key and no comma.
- These all fail to load: `"h, DESC"` (the form in the commit
  message), `"[h]"`, and `"h DESC extra"`.
- In strict mode, a parse error is a config error. Otherwise it is
  only logged, and the layer still sorts by whatever part was
  parsed.
- `save_map` writes the value back as `column` or `column DESC`.

## Verified behaviour

The test used three overlapping polygons, with `k` = 2/red,
3/green and 1/blue:

| sort-by   | colour on top             |
|-----------|---------------------------|
| (none)    | blue (last in data order) |
| `k`       | green (highest k)         |
| `k DESC`  | blue (lowest k)           |

Strings sort the same way: `b`, `c`, `a` with `k` gives `c` on top.

## Things to watch for

- **It turns off `group-by`.** The renderer checks `sort-by`
  first, so a layer that sets both silently ignores `group-by`.
- **Memory:** every feature of the layer within the query extent
  is held in memory at once, as with `cache-features="true"`.
- **Ties:** sorting uses `std::sort`, which is not stable. Features
  with equal values come out in no particular order.
- **String comparison:** strings are compared by code unit, with no
  locale collation. Verified: `B, a, C` sorts as `B, C, a`.
- **Mixed or missing values:** comparing a number with a string, or
  anything with a null, is false in both directions (see
  `src/value.cpp`, `comparison<>`).
  - This breaks the strict weak ordering that `std::sort` relies
    on, so the order of such a column is undefined.
  - Int, double and bool mix fine, because they are compared
    numerically.
  - Empty CSV cells in a numeric column are a likely trigger.
    Not tested.
- **Not available from Python:** `mapnik.Layer` has `group_by` but
  no `sort_by`, so `sort-by` only works from XML.

## Possible bug (read in the code, not tested)

`src/save_map.cpp:613`:

    if (lyr.sort_by() || explicit_defaults)
    {
        auto sort_by = *lyr.sort_by();

With `explicit_defaults` set and no `sort-by` on the layer, this
dereferences an empty `std::optional`. That is undefined behaviour
and may crash.

## For the book

- **Layer attribute table:** add `sort-by`, type string, no
  default, linking to an example.
- **Example idea:** overlapping circles or competing labels,
  rendered three ways: unsorted, `ASC`, and `DESC`. The example
  needs `minimum-version="4.1.4"`.
