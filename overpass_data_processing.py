import geopandas as gp
import pandas as pd
import os

path = os.path.dirname(os.path.realpath(__file__))


def preprocess(file='./export.geojson', use_height=False):
    print("Start preprocessing")
    export = gp.read_file(file)

    tags_dict = ['highway',
                'railway']
    keys = []
    tags = []

    # убрать строки, в которых все указанные тэги имеют пустое значение
    filter = 'export['
    for tag in tags_dict:
        if tag in export.columns:
            filter += f"(export['{tag}']=='') &"
    filter= filter[:-2] + '].index'
    export.drop(eval(filter), inplace=True)

    # преобразовать таблицу к виду tags | keys
    for x in range(export.shape[0]):
        for tag in tags_dict:
            if tag in export.columns:
                if export[tag].values[x]:
                    tags.append(tag)
                    keys.append(export[tag].values[x])
                    break
    export['tag']=tags
    export['key']=keys
    fields = ['tag', 'key', 'geometry', 'layer']
    if use_height:
        export['height'] = export['height'].fillna(0)
        fields.append('height')
    export = export[fields]
    # допущение, что чем выше дорога, тем лучше шумоизоляция
    export['layer'] = pd.to_numeric(export['layer'], errors='coerce').fillna(0)
    export[export['layer'] < 0]['layer'] = 0
    with open(f"./noise_makers.geojson",'w') as f:
        f.write(export.to_json())