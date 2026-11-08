# Draft: upstream bug report (mapnik/mapnik)

Not filed yet. Found because the example images in the book's PDF
version (asciidoctor-pdf, which uses prawn-svg) had black
backgrounds. `examples/render.py` works around it, see the comment
there.

---

**Title:** Cairo SVG output: map background is written as an SVG filter, many SVG renderers show it black

### Description

The Cairo renderer paints the map background with the `SOURCE`
operator (`cairo_renderer<T>::setup()` in
`src/cairo/cairo_renderer.cpp`):

```cpp
context_.set_color(*bg);
context_.set_operator(composite_mode_e::src);
context_.paint();
```

SVG has no equivalent of Cairo's `SOURCE` operator. Cairo's SVG
surface (tested with Cairo 1.18.4) emulates it with masks, `feImage`
references to other elements, and an `feComposite` arithmetic filter.
The filter is applied to a black `<rect>` covering the whole image:

```xml
<filter id="filter-0" x="0%" y="0%" width="100%" height="100%">
<feImage xlink:href="#compositing-group-1" result="source" .../>
<feImage xlink:href="#compositing-group-2" result="destination" .../>
<feComposite in="source" in2="destination" operator="arithmetic" k1="0" k2="1" k3="1" k4="0" .../>
</filter>
...
<g filter="url(#filter-0)" transform="translate(-60, -30)">
<rect x="0" y="0" width="720" height="360" fill="rgb(0%, 0%, 0%)" fill-opacity="1"/>
</g>
```

This is valid SVG, but renderers without full filter support
ignore the filter and draw that black rectangle instead. The whole
map then has a black background. Affected renderers include:

- prawn-svg 0.34.2, used by asciidoctor-pdf to embed SVG images in
  PDF documents;
- ImageMagick's internal SVG renderer (`magick file.svg file.png`,
  ImageMagick 7 on Debian 13).

Viewers that support filters display the image correctly. Even
then, a filter and three helper groups for a plain background
color make the files larger and slower to render.

Every map with a `background-color` is affected, so effectively all
SVG output of the Cairo renderer.

### Steps to reproduce

```python
import mapnik
m = mapnik.Map(200, 100)
mapnik.load_map_from_string(m, '<Map background-color="white"/>')
mapnik.render_to_file(m, 'bg.svg', 'svg')
```

`bg.svg` contains `feComposite`, and `magick bg.svg bg.png` gives
an all-black image.

The same happens with Cairo alone (pycairo 1.27.0, Cairo 1.18.4):
painting a surface with `OPERATOR_SOURCE` writes the filter
construct, both for opaque and translucent colors. With
`OPERATOR_OVER` the output is a plain `<rect>`.

### Expected behaviour

A map background color should be written as a plain filled
rectangle, as Cairo does for the `OVER` operator.

### Proposed fix

For an opaque color, `SOURCE` and `OVER` give the same result,
whatever was on the surface before (OVER: `src + dst * (1 - 1) =
src`). So `OVER` can be used whenever the background alpha is 255,
which covers nearly all real styles:

```cpp
context_.set_color(*bg);
context_.set_operator(bg->alpha() == 255 ? composite_mode_e::src_over
                                         : composite_mode_e::src);
context_.paint();
```

Translucent backgrounds keep `SOURCE`, so that existing content on
a caller-provided surface is still replaced rather than blended
with. For the usual case of a fresh, transparent surface, `OVER`
would give the same result there, too. So an alternative is to use
`OVER` always, if replacing existing content is not considered part
of the renderer's contract.

Compositing operators set in styles (`comp-op` on symbolizers and
styles) still need filters in SVG output. This report is only about
the background, which every map has and which needs no compositing.

### Workaround

Render the SVG from a copy of the style without
`background-color`, and insert a
`<rect width="100%" height="100%" fill="..."/>` as the first
element of the SVG.

### Environment

- Mapnik 4.3.3 (python-mapnik), current master (v4.3.2-167-g0f6ba9642)
  has the same code; it dates back to 2013/2014.
- Cairo 1.18.4, Debian GNU/Linux 13 (trixie), amd64
