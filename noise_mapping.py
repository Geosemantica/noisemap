import geopandas as gp
import pandas as pd
import os
from support_functions import grid_intersection, iron_dissolver

path = os.path.dirname(os.path.realpath(__file__))

noise_makers = gp.read_file(path+'/noise_makers.geojson')
tags_ref = pd.read_csv(path+'/tags.csv',sep=';')
density_grid = gp.read_file(path+'/density_grid.geojson')

noise_makers = gp.sjoin(noise_makers, density_grid, how='left').merge(tags_ref,on=['tag','key'])
noise_makers = noise_makers[['geometry','sound_level','density']]
print(noise_makers[noise_makers['geometry'].is_empty])

noise_makers['sound_level'].fillna(0, inplace=True)
noise_makers['density'].fillna(0, inplace=True)
noise_makers['geometry'].fillna(inplace=True)

noise_makers['buffer45'] = 10 ** ((noise_makers['sound_level'] - 45) / 20) / (1 - noise_makers['density'])
noise_makers['buffer55'] = 10 ** ((noise_makers['sound_level'] - 55) / 20) / (1 - noise_makers['density'])
noise_makers['buffer65'] = 10 ** ((noise_makers['sound_level'] - 65) / 20) / (1 - noise_makers['density'])


noise_makers = noise_makers.to_crs(epsg=32636)

values = [] 
geoms = [] 

for x in range(len(noise_makers)):
    
    geom = noise_makers['geometry'].values[x] 
    
    size65 = noise_makers['buffer65'].values[x]
    buff65 = geom.buffer(size65) 
    values.append(65) 
    geoms.append(buff65)

    size55 = noise_makers['buffer55'].values[x]
    
    buff55 = geom.buffer(size55)
    values.append(55)
    geoms.append(buff55)
    
    size45 = noise_makers['buffer45'].values[x]
    
    buff45 = geom.buffer(size45)
    values.append(45)
    geoms.append(buff45)

result = gp.GeoDataFrame()
result.geometry = geoms 
result['value'] = values

result.crs = "EPSG:32636"
result.geometry = result.buffer(0.00000001)

print('result', result)

# смерджить полигоны по группам value
gdf = iron_dissolver(result)
gdf.crs = "EPSG:32636"
print('dissolved', gdf)
buffer45 = gdf[gdf['value']==45]
buffer55 = gdf[gdf['value']==55]
buffer65 = gdf[gdf['value']==65]

grid = gp.read_file(path+'/super_grid.shp')
grid.crs = "EPSG:32636"

values = []
geoms = []
print(buffer45)
# острожно: функция имеет побочный эффект (список geoms)
buffer45 = grid_intersection(buffer45, grid, values, geoms)
buffer55 = grid_intersection(buffer55, grid, values, geoms)
gdf = grid_intersection(buffer65, grid, values, geoms)
print('gdf', gdf)
gdf[gdf['value']==45] = gp.overlay(gdf[gdf['value']==45], gdf[gdf['value']==55], how='difference')
gdf[gdf['value']==55] = gp.overlay(gdf[gdf['value']==55], gdf[gdf['value']==65], how='difference')
gdf.crs = "EPSG:32636"
gdf = gdf.to_crs(epsg=4326)
gdf = gdf.sort_values('value')[['geometry', 'value']]

with open(path+'/dissolved.geojson', 'w') as f:
    f.write(gdf.to_json())
