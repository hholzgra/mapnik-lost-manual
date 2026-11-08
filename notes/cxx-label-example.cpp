// Test program for notes/cxx-examples.md: builds a map with markers
// and labels through the Mapnik C++ API and renders it to label.png.
//
// g++ -std=c++17 -O1 cxx-label-example.cpp -o label \
//     $(pkg-config --cflags --libs libmapnik)

#include <mapnik/map.hpp>
#include <mapnik/layer.hpp>
#include <mapnik/rule.hpp>
#include <mapnik/feature_type_style.hpp>
#include <mapnik/symbolizer.hpp>
#include <mapnik/datasource_cache.hpp>
#include <mapnik/font_engine_freetype.hpp>
#include <mapnik/agg_renderer.hpp>
#include <mapnik/image.hpp>
#include <mapnik/image_util.hpp>
#include <mapnik/expression.hpp>
#include <mapnik/text/placements/dummy.hpp>
#include <mapnik/text/formatting/text.hpp>

int main()
{
    using namespace mapnik;
    datasource_cache::instance().register_datasources(
        "/usr/lib/x86_64-linux-gnu/mapnik/4.0/input");
    freetype_engine::register_fonts("/usr/share/fonts", true);

    Map m(600, 300, "epsg:4326");
    m.set_background(color("white"));

    feature_type_style style;
    rule r;
    markers_symbolizer marker;
    put(marker, keys::fill, color("red"));
    put(marker, keys::width, 10.0);     // must be a double, see below
    r.append(std::move(marker));

    text_symbolizer text;
    auto placements = std::make_shared<text_placements_dummy>();
    auto& defaults = placements->defaults;
    defaults.format_defaults.face_name = "DejaVu Sans Book";
    defaults.format_defaults.text_size = 12.0;
    defaults.layout_defaults.dy = 10.0;
    defaults.set_format_tree(std::make_shared<formatting::text_node>(
        parse_expression("[name]")));
    put<text_placements_ptr>(text, keys::text_placements_, placements);
    put(text, keys::allow_overlap, true);
    r.append(std::move(text));
    style.add_rule(std::move(r));
    m.insert_style("points", std::move(style));

    parameters p;
    p["type"] = "csv";
    p["inline"] = "x,y,name\n0,0,Origin\n10,5,East\n";
    layer lyr("points", "epsg:4326");
    lyr.set_datasource(datasource_cache::instance().create(p));
    lyr.add_style("points");
    m.add_layer(lyr);

    m.zoom_all();
    image_rgba8 img(m.width(), m.height());
    agg_renderer<image_rgba8> ren(m, img);
    ren.apply();
    save_to_file(img, "label.png", "png");
}
