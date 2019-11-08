import copy
import json
import os
from typing import Dict, List

from gcrmnbc.utils import data_bucket, gdal_command_line


GRID_SIZE = 100

SAMPLE_LOCATIONS = [
    '0000E-0900N',  # Pacific islands
    '0100E-1100N',
    '0100E-0900N',
    '0500E-1100N',  # Caribbean
    '1300E-0900N',  # East Africa
    '1500E-1000N',  # Asia
    '1600E-0900N',
    '1700E-1100N',
    '1700E-1000N',
    '1800E-0900N',  # GBR
    '1800E-0800N',
    '1900E-1000N',
]

MANIFEST_MOSAIC = {
    'name': 'projects/earthengine-legacy/assets/users/nfabina/planet_mosaic/',
    'tilesets': [{'sources': []}],
    'bands': [
        {'id': 'red', 'tileset_band_index': 0, 'pyramiding_policy': 'MEAN'},
        {'id': 'green', 'tileset_band_index': 1, 'pyramiding_policy': 'MEAN'},
        {'id': 'blue', 'tileset_band_index': 2, 'pyramiding_policy': 'MEAN'}
    ]
}

MANIFEST_HEAT = {
    'name': 'projects/earthengine-legacy/assets/users/nfabina/reef_probs/',
    'tilesets': [{'sources': []}],
    'bands': [{'id': 'reef_probabilities', 'pyramiding_policy': 'MEAN'}]
}

MANIFEST_OUTLINE = {
    'name': 'projects/earthengine-legacy/assets/users/nfabina/reef_preds/',
    'tilesets': [{'sources': []}],
    'bands': [{'id': 'reef_predictions', 'pyramiding_policy': 'MODE'}]
}


def upload_reef_products_to_earth_engine(model_version: str) -> None:
    # Get quads
    blobs_mosaic = data_bucket.get_imagery_quad_blobs()
    blobs_heat, blobs_outline = data_bucket.get_reef_heat_and_outline_quad_blobs(model_version)
    # Upload outlines
    _create_asset_folders(model_version)
    asset_chunks = _create_asset_chunks(blobs_outline)
    manifests = _create_manifests(asset_chunks, MANIFEST_OUTLINE, model_version)
    _submit_uploads(manifests)
    # Upload heatmaps
    asset_chunks = _create_asset_chunks(blobs_heat)
    manifests = _create_manifests(asset_chunks, MANIFEST_HEAT, model_version)
    _submit_uploads(manifests)
    # Upload planet
    asset_chunks = _create_asset_chunks(blobs_mosaic)
    manifests = _create_manifests(asset_chunks, MANIFEST_MOSAIC)
    _submit_uploads(manifests)


def _create_asset_chunks(raw_blobs:  List[data_bucket.QuadBlob]) -> Dict[str, Dict[str, data_bucket.QuadBlob]]:
    asset_chunks = dict()
    for blob in raw_blobs:
        x_id = blob.x - blob.x % GRID_SIZE
        y_id = blob.y - blob.y % GRID_SIZE
        asset_id = '{:04d}E-{:04d}N'.format(x_id, y_id)
        if asset_id not in SAMPLE_LOCATIONS:
            continue
        asset_chunks.setdefault(asset_id, dict())[blob.quad_focal] = blob
    return asset_chunks


def _create_manifests(
        asset_chunks: Dict[str, Dict[str, data_bucket.QuadBlob]],
        manifest_template: dict,
        model_version: str = None
) -> List[dict]:
    manifests = list()
    for asset_id, asset_blobs in asset_chunks.items():
        manifest = copy.deepcopy(manifest_template)
        name_suffix = asset_id
        if model_version:
            name_suffix = model_version + '/' + name_suffix
        manifest['name'] = manifest['name'] + name_suffix
        uris = [{'uris': ['gs://coral-atlas-data-share/{}'.format(blob.blob.name)]} for blob in asset_blobs.values()]
        manifest['tilesets'] = [{'sources': uris}]
        manifests.append(manifest)
    return manifests


def _create_asset_folders(model_version: str) -> None:
    base_command = 'earthengine create folder -p users/nfabina/{}'
    for folder in ('planet_mosaic', 'reef_preds/{}'.format(model_version), 'reef_probs/{}'.format(model_version)):
        command = base_command.format(folder, model_version)
        gdal_command_line.run_gdal_command(command)


def _submit_uploads(manifests: List[dict]) -> None:
    tmp_filename = 'tmp_manifest.json'
    for manifest in manifests:
        with open(tmp_filename, 'w') as file_:
            json.dump(manifest, file_)
        command = 'earthengine upload image --manifest {}'.format(tmp_filename)
        gdal_command_line.run_gdal_command(command)
        os.remove(tmp_filename)


if __name__ == '__main__':
    upload_reef_products_to_earth_engine('20191105')
