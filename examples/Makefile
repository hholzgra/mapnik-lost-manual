.PHONY: all,clean,show-latest,all-png,all-svg,experimental

rwildcard=$(foreach d,$(wildcard $1*),$(call rwildcard,$d/,$2) $(filter-out disabled/%,$(filter $(subst *,%,$2),$d)))

all: all-png all-svg 

all-svg: $(addsuffix .svg, $(basename $(call rwildcard,,*.xml)))

all-png: $(addsuffix .png, $(basename $(call rwildcard,,*.xml)))

%.svg : %.xml
	@echo $@
	@rm -f $@
	@./render.sh $<

%.png : %.xml
	@echo $@
	@rm -f $@
	@./render.sh $<

DataSource-OGR-OSM.svg: data/ways.osm

DataSource-OGR-OSM.png: data/ways.osm

cairo-and-mapnik.svg: cairo-and-mapnik.py
	@echo cairo-and-mapnik
	@./cairo-and-mapnik.py


clean:
	@git clean -fX

show-latest: all
	@ls -t *.svg | head -1 | xargs display &

experimental: cairo-and-mapnik.svg
