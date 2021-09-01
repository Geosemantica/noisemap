import geopandas as gp
import shapefile as shp
import os, math

path = os.path.dirname(os.path.realpath(__file__))


def make_fishnet(bbox, dx=1000, dy=1000, file='grid.shp'):
    minx,miny,maxx,maxy = bbox

    nx = int(math.ceil(abs(maxx - minx)/dx))
    ny = int(math.ceil(abs(maxy - miny)/dy))

    with shp.Writer(file, shapeType=shp.POLYGON) as w:
        w.autoBalance = 1
        w.field("ID")
        id=0

        for i in range(ny):
            for j in range(nx):
                id+=1
                vertices = []
                parts = []
                vertices.append([min(minx+dx*j,maxx),max(maxy-dy*i,miny)])
                vertices.append([min(minx+dx*(j+1),maxx),max(maxy-dy*i,miny)])
                vertices.append([min(minx+dx*(j+1),maxx),max(maxy-dy*(i+1),miny)])
                vertices.append([min(minx+dx*j,maxx),max(maxy-dy*(i+1),miny)])
                parts.append(vertices)
                w.poly(parts)
                w.record(id)


def generate_grids(noise_makers='./noise_makers.geojson', houses='./houses.geojson', cell_size=400, proj=32636):
    print("Generating grids...")
    houses = gp.read_file(houses)
    houses = houses.to_crs(epsg=proj)
    houses = houses[['geometry']]
    print('houses ready')

    houses['area'] = houses.area

    bounds = gp.read_file(noise_makers).to_crs(epsg=proj).total_bounds
    # построить сетку для разрезания полигонов шума на меньшие куски
    make_fishnet(bounds, cell_size, cell_size, file=f"./super_grid.shp")
    # построить сетку для расчета плотности зданий
    make_fishnet(bounds, file=f"./grid.shp")
    grid = gp.read_file(f"{path}/grid.shp")
    grid.crs = f"EPSG:{proj}"
    print('grid ready')
    print(grid.crs, houses.crs)
    data = gp.sjoin(grid, houses)
    data = data.groupby('ID').sum().reset_index(0)
    print('sjoin ready')

    grid = grid.merge(data, how='outer', on='ID')
    grid = grid.to_crs(epsg=4326)
    grid['area']= grid['area'].fillna(0)
    grid['density'] = grid['area']/(1000*1000)
    grid = grid[['ID','density','geometry']]
    print(grid)
    print('merge ready')

    with open('./density_grid.geojson','w') as f:
        f.write(grid.to_json())
