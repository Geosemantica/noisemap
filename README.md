## Использование

1. Извлечь необходимые данные OSM из `overpass-turbo`, сохранить в файле `export.geojson` и
положить его в папку проекта.


2. Положить туда же файл `houses.geojson` с геометрией зданий.


3. Запустить последовательно скрипты:
    ```bash
   $ python overpass_data_processing.py
   $ python make_density_grid.py
   $ python noise_mapping.py
    ```
    Итоговый файл с полигонами шума - `dissolved.geojson`

