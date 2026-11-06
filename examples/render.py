#! /usr/bin/env python3

# usage: render.py style.xml output-base
# writes output-base.png and output-base.svg

import sys
import mapnik

xml, out = sys.argv[1:3]

map = mapnik.Map(600, 300)

mapnik.load_map(map, xml, True, '.')

map.zoom_all()
e = map.envelope()
d = 2
map.zoom_to_box(mapnik.Box2d(e.minx-d, e.miny-d, e.maxx+d, e.maxy+d))

mapnik.render_to_file(map, out+'.png', 'png')
mapnik.render_to_file(map, out+'.svg', 'svg')
