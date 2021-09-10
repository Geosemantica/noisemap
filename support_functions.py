from shapely.ops import unary_union
from rtree import index
import geopandas as gp


def grid_intersection(data,grid):
    print('Apply grid intersections...')
    gdf = gp.GeoDataFrame()
    gdf = gdf.append(gp.overlay(data, grid, how="intersection"))
    gdf = gdf.append(gp.overlay(data, grid, how="difference"))
    return gdf[['geometry', 'value']].reset_index()


def geo_difference(gdf1, gdf2):
    coords={}
    for x in range(gdf2.shape[0]):
        coord = (gdf2.geometry.values[x].centroid.x,gdf2.geometry.values[x].centroid.y)
        id = x
        coords[id] = coord

    ind = set_spatial_index(coords)

    geoms = []
    for x in range(gdf1.shape[0]):
        if x%1000==0:
            print(round((x/float(gdf1.shape[0]))*100,2), 'percent done')
        geom1 = gdf1['geometry'].values[x]
        point = (geom1.centroid.x,geom1.centroid.y)
        list_of_nearest = ind.nearest(point, 50)
        print('nearest:', list(list_of_nearest))
        for y in list_of_nearest:
            geom2 = gdf2['geometry'].values[y]
            geom1 = geom1.difference(geom2)
        geoms.append(geom1)
    gdf1['geometry'] = geoms

    return gdf1[gdf1['geometry'].notnull()]


def set_spatial_index(coordinates):
    p = index.Property()
    p.dimension = 2
    ind= index.Index(properties=p)
    for x,y in zip(coordinates.keys(),coordinates.values()):
        ind.add(x,y)
    return ind


def iron_dissolver(data, levels):

    print('dissolver starts')
    
    data = data[['geometry','value']]

    gdf =gp.GeoDataFrame()

    geoms=[]
    values=[]

    for val in levels:
        print('loop, processing %i'%val)
        df = data[data['value']==val]
        df.geometry = df.buffer(0)
        geom = unary_union(df.geometry.values)
        geoms.append(geom)
        values.append(val)

    gdf.geometry = geoms
    gdf['value'] = values

    return gdf
