import argparse
import re
import shlex
import subprocess
from typing import Set

from gcrmnbc.utils import data_bucket


_REGEX_QUAD = r'L15-\d{4}E-\d{4}N'


def calculate_application_progress(config_name: str, response_mapping: str, model_version: str) -> None:
    command = 'gsutil ls -r gs://coral-atlas-data-share/gcrmn-global-map/**/{}/{}/{}/'.format(
        response_mapping, config_name, model_version)
    quads_complete = _parse_quads_from_gsutil(command)
    num_complete = len(quads_complete)

    command = 'gsutil ls -r gs://coral-atlas-data-share/gcrmn-global-map/**/' + data_bucket.FILENAME_NO_APPLY
    quads_noapply = _parse_quads_from_gsutil(command)
    num_noapply = len(quads_noapply)

    command = 'gsutil ls -r gs://coral-atlas-data-share/gcrmn-global-map/**/' + data_bucket.FILENAME_CORRUPT
    quads_corrupt = _parse_quads_from_gsutil(command)
    num_corrupt = len(quads_corrupt)

    command = 'gsutil ls -r gs://coral-atlas-data-share/coral_reefs_2018_visual_v1_mosaic/**/L*.tif'
    quads_total = _parse_quads_from_gsutil(command)
    num_total = len(quads_total) - num_noapply - num_corrupt
    num_remaining = num_total - num_complete

    print('Quads')
    print('{:5d}   processed'.format(num_complete))
    print('{:5d}   remaining'.format(num_remaining))
    print('{:5d}   total'.format(num_total))
    print('{:5d}%  completed'.format(round(100 * num_complete / num_total)))
    print()
    print('{:5d}  no application needed'.format(num_noapply))
    print('{:5d}  corrupt'.format(num_corrupt))
    print()
    print('Corrupt quads:  {}'.format(', '.join(quads_corrupt)))


def _parse_quads_from_gsutil(command: str) -> Set[str]:
    quads = set()
    result = subprocess.run(shlex.split(command), capture_output=True)
    for line in result.stdout.decode('utf-8').split('\n'):
        match = re.search(_REGEX_QUAD, line)
        if match:
            quads.add(match.group())
    return quads


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--config_name', type=str, required=True)
    parser.add_argument('--response_mapping', type=str, required=True)
    parser.add_argument('--model_version', type=str, required=True)
    args = parser.parse_args()
    calculate_application_progress(args.config_name, args.response_mapping, args.model_version)
