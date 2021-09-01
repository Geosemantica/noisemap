## Использование

1. Извлечь необходимые данные OSM из `overpass-turbo`, сохранить в файле `export.geojson` и
положить его в папку проекта. Если необходимо производить расчеты с учетом высоты OSM объектов,
то необходимо иметь целочисленное поле `height` в данных.


2. Положить туда же файл `houses.geojson` с геометрией зданий.


3. Запустить главный скрипт с необходимыми параметрами:
    ```bash
   $ python noise_mapping.py <параметры командной строки>
    ```
   ```bash
   usage: noise_mapping.py [-h] [-e EXPORT] [-p PROJECTION] [-b BUILDINGS] [-t TAGS] [-c CELL_SIZE] [--with-height]

   Generate noise map based on osm data (QuickOSM can be also used) and buildings geometry
   
   optional arguments:
     -h, --help            show this help message and exit
     -e EXPORT, --export EXPORT
                           path to file with osm data
     -p PROJECTION, --projection PROJECTION
                           projection that will be used for calculations(data on input and output is always in 4326)
     -b BUILDINGS, --buildings BUILDINGS
                           path to file with buildings geometry
     -t TAGS, --tags TAGS  path to csv file with noise level of every type of object
     -c CELL_SIZE, --cell-size CELL_SIZE
                           size of cells in grid for cutting(simplification) of resulting polygons
     --with-height         use height of osm objects in calculations
   ```
    Итоговый файл с полигонами шума - `dissolved.geojson`

