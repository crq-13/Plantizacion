import geopandas as gpd
from shapely.geometry import Point, Polygon
import pandas as pd
from fiona.drvsupport import supported_drivers
import folium
import json
from IPython.display import display

fig = folium.Map(width=900, height=600)


def run():
    supported_drivers['LIBKML'] = 'rw'
    my_map = gpd.read_file('Antazales.kml', driver='LIBKML')
    print(type(my_map))

    geo_json_map = json.load(open('Antazales.geojson'))
    folium.Choropleth(
        geo_data=geo_json_map,
        fill_color="steelblue",
        fill_opacity=0.4,
        line_color="steelblue",
        line_opacity=0.9
    ).add_to(fig)

    fig.save("fig.html")


if __name__ == "__main__":
    run()

