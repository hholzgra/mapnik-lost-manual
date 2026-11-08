#! /usr/bin/env python3

# usage: render.py style.xml output-base
# writes output-base.png and output-base.svg

import re
import sys
import mapnik

xml, out = sys.argv[1:3]

# Cairo paints the map background with the SOURCE operator, which its
# SVG backend writes as an SVG filter (feComposite); renderers without
# filter support, like prawn-svg used by asciidoctor-pdf, show a black
# image instead. So the SVG is rendered from a copy of the style
# without background-color, and the background is added as a plain
# <rect> afterwards. As the surface starts out transparent, the
# result looks the same.
MAP_TAG = re.compile(r"<Map\b[^>]*>")
BG_ATTR = re.compile(r"""\s+background-color=("[^"]*"|'[^']*')""")


def zoomed(map):
    map.zoom_all()
    e = map.envelope()
    d = 2
    map.zoom_to_box(mapnik.Box2d(e.minx-d, e.miny-d, e.maxx+d, e.maxy+d))
    return map


map = mapnik.Map(600, 300)
mapnik.load_map(map, xml, True, '.')
zoomed(map)
mapnik.render_to_file(map, out+'.png', 'png')

with open(xml) as f:
    text = f.read()
tag = MAP_TAG.search(text)
if tag and BG_ATTR.search(tag.group(0)):
    bg = map.background
    text = (text[:tag.start()] + BG_ATTR.sub('', tag.group(0))
            + text[tag.end():])
    map = mapnik.Map(600, 300)
    mapnik.load_map_from_string(map, text, True, './')
    zoomed(map)
    mapnik.render_to_file(map, out+'.svg', 'svg')
    with open(out+'.svg') as f:
        svg = f.read()
    rect = ('<rect width="100%%" height="100%%" fill="rgb(%d,%d,%d)"'
            ' fill-opacity="%g"/>' % (bg.r, bg.g, bg.b, bg.a / 255))
    svg = re.sub(r"<svg\b[^>]*>", lambda m: m.group(0) + "\n" + rect,
                 svg, count=1)
    with open(out+'.svg', 'w') as f:
        f.write(svg)
else:
    mapnik.render_to_file(map, out+'.svg', 'svg')
