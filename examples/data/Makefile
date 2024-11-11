PHONY += shapefiles countries graticules
D = examples/data

%.shp : %.zip
	@unzip -q -u -o -d $(D) $<

shapefiles: countries graticules

countries: $(D)/ne_110m_admin_0_countries.shp
countries: $(D)/ne_110m_admin_0_countries_lakes.shp

graticules: $(D)/ne_50m_graticules_10.shp
graticules: $(D)/ne_50m_graticules_30.shp

$(D)/ne_110m_admin_0_countries.zip:
	@wget --quiet https://naturalearth.s3.amazonaws.com/110m_cultural/ne_110m_admin_0_countries.zip -O $@

$(D)/ne_110m_admin_0_countries_lakes.zip:
	@wget --quiet https://naturalearth.s3.amazonaws.com/110m_cultural/ne_110m_admin_0_countries_lakes.zip -O $@

$(D)/ne_50m_graticules_10.zip:
	@wget --quiet https://naturalearth.s3.amazonaws.com/50m_physical/ne_50m_graticules_10.zip -O $@

$(D)/ne_50m_graticules_30.zip:
	@wget --quiet https://naturalearth.s3.amazonaws.com/50m_physical/ne_50m_graticules_30.zip -O $@

