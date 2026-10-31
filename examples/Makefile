ifeq ($(notdir $(CURDIR)),examples)

# invoked from within examples/ -- this file is only a fragment of the
# top level Makefile, so hand all goals over to that one, with file
# names made relative to the top level directory
goals := $(or $(MAKECMDGOALS),all-png all-svg)

.PHONY: delegate $(goals)
$(goals): delegate ;

delegate:
	@$(MAKE) -C .. $(foreach g,$(goals),$(if $(findstring .,$g)$(findstring /,$g),examples/$g,$g))

else

PHONY += show-latest all-png all-svg experimental data

rwildcard=$(foreach d,$(wildcard $1*),$(call rwildcard,$d/,$2) $(filter $(subst *,%,$2),$d))

example_bases := $(basename $(filter-out examples/disabled/%,$(call rwildcard,examples/,*.xml)))
ifeq ($(ARC_SUPPORT),)
example_bases := $(filter-out examples/Symbolizer/Arc/%,$(example_bases))
endif

all-svg: $(addsuffix .svg, $(example_bases))

all-png: $(addsuffix .png, $(example_bases))

%.svg %.png: %.xml | shapefiles
	@echo $@
	@rm -f $@
	@examples/render.sh $<

examples/DataSource-OGR-OSM.svg: examples/data/ways.osm

examples/DataSource-OGR-OSM.png: examples/data/ways.osm

experimental: examples/cairo-and-mapnik.svg

examples/cairo-and-mapnik.svg: examples/cairo-and-mapnik.py
	@echo cairo-and-mapnik
	@examples/cairo-and-mapnik.py
endif
