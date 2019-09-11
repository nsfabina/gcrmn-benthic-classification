from collections import Counter
import json
import os
import re


DIR_EXPECTED = '/scratch/nfabina/gcrmn-benthic-classification/tmp_training_data/'
FILENAMES_EXPECTED = ['lwr_3857.geojson', 'lwr_4326.geojson', 'lwr.geojson']


def parse_responses() -> None:
    filepaths_expected = [os.path.join(DIR_EXPECTED, filename) for filename in FILENAMES_EXPECTED]
    filepaths_exist = [filepath for filepath in filepaths_expected if os.path.exists(filepath)]
    assert filepaths_exist, 'Data is not available in expected locations'
    filepath = filepaths_exist[0]

    properties = dict()
    with open(filepath) as file_:
        for idx, line in enumerate(file_):
            print('\r{}'.format(idx), end='')
            match = re.search('{ "class_name[^}]*}', line)
            if not match:
                continue
            props = json.loads(match.group())
            for key, value in props.items():
                properties.setdefault(key, Counter()).update([value])
    print(properties)


if __name__ == '__main__':
    parse_responses()
