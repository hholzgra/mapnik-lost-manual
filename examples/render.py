#! /usr/bin/env /usr/bin/python3

import sys
import mapnik

map = mapnik.Map(600,300)

mapnik.load_map(map, sys.argv[1])

map.zoom_all()
e = map.envelope()
d = 2
map.zoom_to_box(mapnik.Box2d(e.minx-d, e.miny-d, e.maxx+d, e.maxy+d))

mapnik.render_to_file(map, 'render.svg', 'svg')
