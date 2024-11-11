PHONY += show-latest all-png all-svg experimental data

rwildcard=$(foreach d,$(wildcard $1*),$(call rwildcard,$d/,$2) $(filter-out disabled/%,$(filter $(subst *,%,$2),$d)))

all-svg: $(addsuffix .svg, $(basename $(call rwildcard,,*.xml)))

all-png: $(addsuffix .png, $(basename $(call rwildcard,,*.xml)))

%.svg : %.xml | shapefiles
	@echo $@
	@rm -f $@
	@examples/render.sh $<

%.png : %.xml | shapefiles
	@echo $@
	@rm -f $@
	@examples/render.sh $<

examples/DataSource-OGR-OSM.svg: examples/data/ways.osm

examples/DataSource-OGR-OSM.png: examples/data/ways.osm

experimental: examples/cairo-and-mapnik.svg

examples/cairo-and-mapnik.svg: examples/cairo-and-mapnik.py
	@echo cairo-and-mapnik
	@examples/cairo-and-mapnik.py

depend::
	@tools/mapnik-deps.sh > .deps/examples.d
