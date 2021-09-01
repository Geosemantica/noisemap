import geopandas as gp
import pandas as pd
import os
from support_functions import grid_intersection, iron_dissolver
from overpass_data_processing import preprocess
from make_density_grid import generate_grids


def make_map(noise_makers='./noise_makers.geojson', tags="./tags.csv", density_grid="./density_grid.geojson",
             super_grid='./super_grid.shp', use_height=False, proj=32636):
    print("Starting mapping")
    path = os.path.dirname(os.path.realpath(__file__))

    noise_makers = gp.read_file(noise_makers)
    tags_ref = pd.read_csv(tags,sep=';')
    density_grid = gp.read_file(density_grid)

    noise_makers = gp.sjoin(noise_makers, density_grid, how='left').merge(tags_ref,on=['tag','key'])
    fields = ['geometry','sound_level','density']
    if use_height:
        fields.append('height')
    noise_makers = noise_makers[fields]

    noise_makers['sound_level'].fillna(0, inplace=True)
    noise_makers['density'].fillna(0, inplace=True)
    noise_makers['geometry'].fillna(inplace=True)

    noise_makers['buffer45'] = 10 ** ((noise_makers['sound_level'] - 45) / 20) / (1 - noise_makers['density'])
    noise_makers['buffer55'] = 10 ** ((noise_makers['sound_level'] - 55) / 20) / (1 - noise_makers['density'])
    noise_makers['buffer65'] = 10 ** ((noise_makers['sound_level'] - 65) / 20) / (1 - noise_makers['density'])
    # учесть высоту дороги
    if use_height:
        noise_makers['buffer45'] = noise_makers['buffer45'] - noise_makers['height']
        noise_makers['buffer55'] = noise_makers['buffer55'] - noise_makers['height']
        noise_makers['buffer65'] = noise_makers['buffer65'] - noise_makers['height']

    noise_makers = noise_makers.to_crs(epsg=proj)

    values = []
    geoms = []

    for x in range(len(noise_makers)):

        geom = noise_makers['geometry'].values[x]

        size65 = noise_makers['buffer65'].values[x]
        # исключить отрицательные и нулевые значения буфера
        if size65 > 0:
            buff65 = geom.buffer(size65)
            values.append(65)
            geoms.append(buff65)

        size55 = noise_makers['buffer55'].values[x]
        if size55 > 0:
            buff55 = geom.buffer(size55)
            values.append(55)
            geoms.append(buff55)

        size45 = noise_makers['buffer45'].values[x]
        if size45 > 0:
            buff45 = geom.buffer(size45)
            values.append(45)
            geoms.append(buff45)

    result = gp.GeoDataFrame()
    result.geometry = geoms
    result['value'] = values

    result.crs = f"EPSG:{proj}"
    result.geometry = result.buffer(0.00000001)

    # смерджить полигоны по группам value
    gdf = iron_dissolver(result)
    gdf.crs = f"EPSG:{proj}"

    buffer45 = gdf[gdf['value']==45]
    buffer55 = gdf[gdf['value']==55]
    buffer65 = gdf[gdf['value']==65]

    # использовать плотную сетку для разрезания полигонов на более простые
    grid = gp.read_file(super_grid)
    grid.crs = f"EPSG:{proj}"

    values = []
    geoms = []

    # острожно: функция имеет побочный эффект (список geoms)
    buffer45 = grid_intersection(buffer45, grid, values, geoms)
    buffer55 = grid_intersection(buffer55, grid, values, geoms)
    gdf = grid_intersection(buffer65, grid, values, geoms)

    gdf[gdf['value']==45] = gp.overlay(gdf[gdf['value']==45], gdf[gdf['value']==55], how='difference')
    gdf[gdf['value']==55] = gp.overlay(gdf[gdf['value']==55], gdf[gdf['value']==65], how='difference')
    gdf.crs = f"EPSG:{proj}"
    gdf.drop(gdf[gdf['value'].isnull() == True].index, inplace=True)
    gdf = gdf.to_crs(epsg=4326)
    gdf = gdf.sort_values('value')[['geometry', 'value']]

    with open('./dissolved.geojson', 'w') as f:
        f.write(gdf.to_json())


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description="Generate noise map based on osm data (QuickOSM can be also used)\
                                    and buildings geometry")
    parser.add_argument("-e", "--export" , default='./export.geojson', help="path to file with osm data")
    parser.add_argument("-p", "--projection", default=32626, type=int, help="projection that will be used for calculations"
                                                                            "(data on input and output is always in 4326)")
    parser.add_argument('-b', '--buildings', default='./houses.geojson', help='path to file with buildings geometry')
    parser.add_argument('-t', '--tags', default='./tags.csv', help='path to csv file with noise level of every type of object')
    parser.add_argument('-c', '--cell-size', default=400, type=int, help="size of cells in grid for cutting"
                                                                        "(simplification) of resulting polygons")
    parser.add_argument('--with-height', action='store_true', help="use height of osm objects in calculations")
    args = parser.parse_args()
    preprocess(file=args.export, use_height=args.with_height)
    generate_grids(houses=args.buildings, cell_size=args.cell_size, proj=args.projection)
    make_map(tags=args.tags, proj=args.projection, use_height=args.with_height)
