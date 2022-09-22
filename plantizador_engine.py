import pandas as pd
import geopandas as gpd
import numpy as np
from scipy.spatial import cKDTree
import geopy.distance


def plantizar(data_json, distancia_max=25):
    keys = data_json.keys()
    labor_id = data_json['labor_id']
    if 'laborsPlansPlantas' in keys:
        labors_plans_plantas = data_json['laborsPlansPlantas']
        plantas = data_json['plantas']
        labores = data_json['labores']
        json_final = {'labor_id': labor_id, 'laborsPlansPlantas': {}}
        lotes = {}
        for lote in labores.keys():
            result = plantizador(plantas[lote], labores[lote], distancia_max)
            df_labors_plans_plantas = pd.DataFrame(labors_plans_plantas[lote])
            df_plantizado = result.join(df_labors_plans_plantas.set_index('planta_id'), on='planta_id')
            labores_id = df_plantizado.labors_plans_planta_id.dropna().unique().astype('int')
            for labor in labores_id:
                cantidad_labores = len(df_plantizado.loc[df_plantizado['labors_plans_planta_id'] == labor])
                if cantidad_labores > 1:
                    tabla_labor_id = \
                        df_plantizado.loc[df_plantizado['labors_plans_planta_id'] == labor].tabla_labor_id
                    for i in range(1, cantidad_labores):
                        df_plantizado.loc[df_plantizado['tabla_labor_id'] == tabla_labor_id.iloc[i],
                                          'labors_plans_planta_id'] = np.nan
            json_plantizado = df_plantizado
            json_plantizado.drop(['distancia', 'planta_location', 'lng_planta', 'lat_planta', 'dist', 'geometry'],
                                 axis=1, inplace=True)
            json_plantizado = json_plantizado.fillna('')
            dict_plantizado = json_plantizado.to_dict('records')
            lotes[lote] = dict_plantizado
        json_final['laborsPlansPlantas'] = lotes
    else:
        plantas = data_json['plantas']
        labores = data_json['labores']
        json_final = {'labor_id': labor_id,
                      'laborsPlansPlantas': {}}
        lotes = {}
        for lote in labores.keys():
            result = plantizador(plantas[lote], labores[lote], distancia_max)
            json_plantizado = result
            json_plantizado.drop(['distancia', 'planta_location', 'lng_planta', 'lat_planta', 'dist', 'geometry'],
                                 axis=1, inplace=True)
            json_plantizado = json_plantizado.fillna('')
            dict_plantizado = json_plantizado.to_dict('records')
            lotes[lote] = dict_plantizado
        json_final['laborsPlansPlantas'] = lotes
    return json_final


def plantizador(plantas, labores, distancia_max):
    df_plantas = pd.DataFrame(plantas)
    df_labores = pd.DataFrame(labores)
    gdf_plantas = gpd.GeoDataFrame(df_plantas, geometry=gpd.points_from_xy(df_plantas.lng, df_plantas.lat))
    gdf_plantas.rename(columns={'lat': 'lat_planta', 'lng': 'lng_planta'}, inplace=True)
    gdf_labores = gpd.GeoDataFrame(df_labores, geometry=gpd.points_from_xy(df_labores.lng,
                                                                           df_labores.lat)).drop(["lng", "lat"], axis=1)
    result = ckd_nearest(gdf_labores, gdf_plantas)
    result = result.sort_values(by='planta_id')
    result['planta_location'] = gpd.points_from_xy(result.lng_planta, result.lat_planta)
    result['distancia'] = result.apply(distance, axis=1)
    result = result.drop(result[result['distancia'] > distancia_max].index)
    return result


def ckd_nearest(gda, gdb):
    nA = np.array(list(gda.geometry.apply(lambda x: (x.x, x.y))))
    nB = np.array(list(gdb.geometry.apply(lambda x: (x.x, x.y))))
    btree = cKDTree(nB)
    dist, idx = btree.query(nA, k=1)
    gdb_nearest = gdb.iloc[idx].drop(columns="geometry").reset_index(drop=True)
    gdf = pd.concat(
        [
            gda.reset_index(drop=True),
            gdb_nearest,
            pd.Series(dist, name='dist')
        ],
        axis=1)

    return gdf


def distance(row):
    distancia = geopy.distance.geodesic([row.geometry.y, row.geometry.x],
                                        [row.planta_location.y, row.planta_location.x]).meters
    return distancia
