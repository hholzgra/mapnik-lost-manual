.PHONY: all countries graticules

%.shp : %.zip
	@unzip -q -u -o $<

all: countries graticules

countries: ne_110m_admin_0_countries.shp ne_110m_admin_0_countries_lakes.shp
graticules: ne_50m_graticules_10.shp ne_50m_graticules_30.shp

ne_110m_admin_0_countries.zip:
	@wget --quiet https://naturalearth.s3.amazonaws.com/110m_cultural/ne_110m_admin_0_countries.zip

ne_110m_admin_0_countries_lakes.zip:
	@wget --quiet https://naturalearth.s3.amazonaws.com/110m_cultural/ne_110m_admin_0_countries_lakes.zip

ne_50m_graticules_10.zip:
	@wget --quiet https://naturalearth.s3.amazonaws.com/50m_physical/ne_50m_graticules_10.zip

ne_50m_graticules_30.zip:
	@wget --quiet https://naturalearth.s3.amazonaws.com/50m_physical/ne_50m_graticules_30.zip

