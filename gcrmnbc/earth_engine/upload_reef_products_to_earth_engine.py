import copy
import json
import os
from typing import Dict, List

from gcrmnbc.utils import data_bucket, command_line


GRID_SIZE = 100

MANIFEST_MOSAIC = {
    'name': 'projects/earthengine-legacy/assets/users/nfabina/planet_samples/',
    'tilesets': [{'sources': []}],
    'bands': [
        {'id': 'red', 'tileset_band_index': 0, 'pyramiding_policy': 'MEAN'},
        {'id': 'green', 'tileset_band_index': 1, 'pyramiding_policy': 'MEAN'},
        {'id': 'blue', 'tileset_band_index': 2, 'pyramiding_policy': 'MEAN'}
    ],
    'uri_prefix': 'gs://coral-atlas-data-share/coral_reefs_2018_visual_v1_mosaic/',
}

MANIFEST_HEAT = {
    'name': 'projects/earthengine-legacy/assets/users/nfabina/reef_probs_v1/',
    'tilesets': [{'sources': []}],
    'bands': [{'id': 'reef_probs', 'pyramiding_policy': 'MEAN'}],
    'uri_prefix': 'gs://coral-atlas-data-share/gcrmn-global-map/',
}

MANIFEST_OUTLINE = {
    'name': 'projects/earthengine-legacy/assets/users/nfabina/reef_preds_v1/',
    'tilesets': [{'sources': []}],
    'bands': [{'id': 'reef_preds', 'pyramiding_policy': 'MODE'}],
    'uri_prefix': 'gs://coral-atlas-data-share/gcrmn-global-map/',
}


def upload_reef_products_to_earth_engine(model_version: str) -> None:
    # Get quads
    blobs_heat, blobs_outline = data_bucket.get_reef_heat_and_outline_quad_blobs(model_version)
    # Upload outlines
    asset_chunks = _create_asset_chunks(blobs_outline)
    manifests = _create_manifests(asset_chunks, MANIFEST_OUTLINE)
    _submit_uploads(manifests)
    # Upload heatmaps
    asset_chunks = _create_asset_chunks(blobs_heat)
    manifests = _create_manifests(asset_chunks, MANIFEST_HEAT)
    _submit_uploads(manifests)


def _create_asset_chunks(raw_blobs:  List[data_bucket.QuadBlob]) -> Dict[str, Dict[str, data_bucket.QuadBlob]]:
    asset_chunks = dict()
    for blob in raw_blobs:
        x_id = blob.x - blob.x % GRID_SIZE
        y_id = blob.y - blob.y % GRID_SIZE
        asset_id = '{:04d}E-{:04d}N'.format(x_id, y_id)
        asset_chunks.setdefault(asset_id, dict())[blob.quad_focal] = blob
    return asset_chunks


def _create_manifests(
        asset_chunks: Dict[str, Dict[str, data_bucket.QuadBlob]],
        manifest_template: dict,
) -> List[dict]:
    manifests = list()
    for asset_id, asset_blobs in asset_chunks.items():
        manifest = copy.deepcopy(manifest_template)
        name_suffix = asset_id
        manifest['name'] = manifest['name'] + name_suffix
        uris = list()
        for blob in asset_blobs.values():
            blob_name = blob.blob.name
            without_leading_path = '/'.join(blob_name.split('/')[1:])
            uris.append({'uris': [without_leading_path]})
        manifest['tilesets'] = [{'sources': uris}]
        manifests.append(manifest)
    return manifests


def _submit_uploads(manifests: List[dict]) -> None:
    tmp_filename = 'tmp_manifest.json'
    for manifest in manifests:
        with open(tmp_filename, 'w') as file_:
            json.dump(manifest, file_)
        command = 'earthengine upload image --manifest {}'.format(tmp_filename)
        command_line.run_command_line(command)
        os.remove(tmp_filename)


if __name__ == '__main__':
    upload_reef_products_to_earth_engine('20191121')
