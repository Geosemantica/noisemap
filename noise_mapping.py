import geopandas as gp
import pandas as pd
import os
from support_functions import grid_intersection, iron_dissolver
from overpass_data_processing import preprocess
from make_density_grid import generate_grids


def make_map(noise_makers='./noise_makers.geojson', tags="./tags.csv", density_grid="./density_grid.geojson",
             super_grid='./super_grid.shp', levels=(45,55,65), use_height=False, proj=32636):
    print("Starting mapping")
    path = os.path.dirname(os.path.realpath(__file__))

    noise_makers = gp.read_file(noise_makers)
    tags_ref = pd.read_csv(tags,sep=';')
    density_grid = gp.read_file(density_grid)

    noise_makers = gp.sjoin(noise_makers, density_grid, how='left').merge(tags_ref,on=['tag','key'])
    noise_makers['sound_level'] = noise_makers['sound_level'] - (noise_makers['layer'] * 5)
    fields = ['geometry','sound_level','density']
    if use_height:
        fields.append('height')
    noise_makers = noise_makers[fields]

    noise_makers['sound_level'].fillna(0, inplace=True)
    noise_makers['density'].fillna(0, inplace=True)
    noise_makers['geometry'].fillna(inplace=True)

    for level in levels:
        noise_makers[f'buffer{level}'] = 10 ** ((noise_makers['sound_level'] - level) / 20) / (1 - noise_makers['density'])
    # учесть высоту дороги
    if use_height:
        for level in levels:
            noise_makers[f'buffer{level}'] = noise_makers[f'buffer{level}'] - noise_makers['height']

    noise_makers = noise_makers.to_crs(epsg=proj)

    values = []
    geoms = []
    print("Generating buffers...")
    for x in range(len(noise_makers)):

        geom = noise_makers['geometry'].values[x]

        for level in levels:
            size = noise_makers[f'buffer{level}'].values[x]
            # исключить отрицательные и нулевые значения буфера
            if size > 0:
                buff = geom.buffer(size)
                values.append(level)
                geoms.append(buff)

    result = gp.GeoDataFrame()
    result.geometry = geoms
    result['value'] = values

    result.crs = f"EPSG:{proj}"
    result.geometry = result.buffer(0.00000001)

    # смерджить полигоны по группам value
    gdf = iron_dissolver(result, levels)
    gdf.crs = f"EPSG:{proj}"

    # использовать плотную сетку для разрезания полигонов на более простые
    grid = gp.read_file(super_grid)
    grid.crs = f"EPSG:{proj}"

    # обрезать полигоны по сетке, все что вне сетки - оставить как есть
    gdf = grid_intersection(gdf, grid)

    # использовать георазность между полигонами
    print("Make geodifference...")
    for i in range(len(levels)-1):
        gdf[gdf['value']==levels[i]] = gp.overlay(gdf[gdf['value']==levels[i]], gdf[gdf['value']==levels[i+1]], how='difference')
    gdf.crs = f"EPSG:{proj}"
    gdf.drop(gdf[gdf['value'].isnull() == True].index, inplace=True)
    gdf.geometry = gdf.buffer(10**-8)
    #gdf = gdf.loc[gdf['geometry'].is_valid]
    # разбить мультигеометрию
    gdf = gdf.explode('geometry')
    gdf = gdf.to_crs(epsg=4326)
    gdf = gdf.sort_values('value')[['geometry', 'value']]

    with open('./dissolved.geojson', 'w') as f:
        f.write(gdf.to_json())


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description="Generate noise map based on osm data (QuickOSM can be also used)\
                                    and buildings geometry")
    parser.add_argument("-e", "--export", default='./export.geojson', help="path to file with osm data")
    parser.add_argument("-n", "--noise-levels", type=int, nargs="+", default=0, help="levels of noise in resulting polygons")
    parser.add_argument("-p", "--projection", default=32636, type=int, help="projection that will be used for calculations"
                                                                            "(data on input and output is always in 4326)")
    parser.add_argument('-b', '--buildings', default='./houses.geojson', help='path to file with buildings geometry')
    parser.add_argument('-t', '--tags', default='./tags.csv', help='path to csv file with noise level of every type of object')
    parser.add_argument('-c', '--cell-size', default=400, type=int, help="size of cells in grid for cutting"
                                                                        "(simplification) of resulting polygons")
    parser.add_argument("-g", "--grid-buffer", default=0, type=int, help="buffer of dense grid to seize all polygons")
    parser.add_argument('--with-height', action='store_true', help="use height of osm objects in calculations")
    args = parser.parse_args()
    levels = [45, 55, 65] if not args.noise_levels else args.noise_levels
    levels.sort()
    preprocess(file=args.export, use_height=args.with_height)
    generate_grids(houses=args.buildings, buffer=args.grid_buffer, cell_size=args.cell_size, proj=args.projection)
    make_map(tags=args.tags, proj=args.projection, levels=levels, use_height=args.with_height)
