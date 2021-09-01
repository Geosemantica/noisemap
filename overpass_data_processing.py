import geopandas as gp
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
    fields = ['tag', 'key', 'geometry']
    if use_height:
        export['height'] = export['height'].fillna(0)
        fields.append('height')
    export = export[fields]

    with open(f"./noise_makers.geojson",'w') as f:
        f.write(export.to_json())