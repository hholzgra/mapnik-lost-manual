PHONY += shapefiles countries graticules
D = examples/data

# unzip restores the timestamps stored inside the archive, which are older
# than the downloaded .zip itself -- touch the .shp afterwards so make sees
# the target as up to date and does not unzip (and re-render) on every run
%.shp : %.zip
	@unzip -q -u -o -d $(D) $<
	@touch $@

shapefiles: countries graticules

countries: $(D)/ne_110m_admin_0_countries_lakes.shp

graticules: $(D)/ne_50m_graticules_30.shp

$(D)/ne_110m_admin_0_countries_lakes.zip:
	@wget --quiet https://naturalearth.s3.amazonaws.com/110m_cultural/ne_110m_admin_0_countries_lakes.zip -O $@

$(D)/ne_50m_graticules_30.zip:
	@wget --quiet https://naturalearth.s3.amazonaws.com/50m_physical/ne_50m_graticules_30.zip -O $@

