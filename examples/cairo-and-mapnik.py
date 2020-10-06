#! /usr/bin/env /usr/bin/python3
import mapnik
import cairo

# set up Cairo PDF surface and context
surface = cairo.SVGSurface('cairo-and-mapnik.svg', 600 , 300)
context = cairo.Context(surface)

# set up Mapnik for drawing
map = mapnik.Map(600,300)
mapnik.load_map(map, 'DataSource-Shape.xml')
map.zoom_all()
map.zoom( -1.1)

# draw map into cairo surface
mapnik.render(map, surface)

# add a simple black rectangle on top
context.set_source_rgb (0, 0, 0)
context.set_line_width (5)
context.rectangle (100 ,100 ,300 ,75)
context.stroke ()

# generate output file
surface.finish ()
