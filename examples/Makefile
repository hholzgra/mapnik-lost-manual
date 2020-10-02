all: all-png all-svg

all-svg: $(addsuffix .svg, $(basename $(wildcard *.xml)))

all-png: $(addsuffix .png, $(basename $(wildcard *.xml)))

%.svg : %.xml
	@echo $@
	@rm -f $@
	@./render.sh $<

%.png : %.xml
	@echo $@
	@rm -f $@
	@./render.sh $<

DataSource-OGR-OSM.svg: ways.osm

DataSource-OGR-OSM.png: ways.osm

.PHONY: all,clean,show-latest,all-png,all-svg

clean:
	@rm -f *.png *.svg
	@rm -f *~ \#* .\#*

show-latest: all
	@ls -t *.svg | head -1 | xargs display &
