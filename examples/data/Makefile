ifeq ($(notdir $(CURDIR)),data)

# invoked from within examples/data/ -- this file is only a fragment of
# the top level Makefile, so hand all goals over to that one, with file
# names made relative to the top level directory
goals := $(or $(MAKECMDGOALS),shapefiles)

.PHONY: delegate $(goals)
$(goals): delegate ;

delegate:
	@$(MAKE) -C ../.. $(foreach g,$(goals),$(if $(findstring .,$g)$(findstring /,$g),examples/data/$g,$g))

else

PHONY += shapefiles countries graticules
D = examples/data

%.shp : %.zip
	@unzip -q -u -o -DD -d $(D) $<

shapefiles: countries graticules

countries: $(D)/ne_110m_admin_0_countries_lakes.shp

graticules: $(D)/ne_50m_graticules_30.shp

$(D)/ne_110m_admin_0_countries_lakes.zip:
	@wget --quiet https://naturalearth.s3.amazonaws.com/110m_cultural/ne_110m_admin_0_countries_lakes.zip -O $@

$(D)/ne_50m_graticules_30.zip:
	@wget --quiet https://naturalearth.s3.amazonaws.com/50m_physical/ne_50m_graticules_30.zip -O $@

endif
