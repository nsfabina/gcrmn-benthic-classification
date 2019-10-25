from collections import Counter
import os
import random
import re
import shutil

import numpy as np
from tqdm import tqdm


#files_features = sorted([fn for fn in os.listdir() if fn.startswith('features')])
files_responses = sorted([fn for fn in os.listdir() if fn.startswith('responses')])
#files_weights = sorted([fn for fn in os.listdir() if fn.startswith('weights')])

#total_samples = 2849 * 10


dir_out = '/scratch/nfabina/gcrmn-benthic-classification/built_data/downsample_50/lwr_128_64/'


for filepath_response in files_responses:
    create_new_memmap_arrays_with_balanced_classes(filepath_response, dir_out)


def create_new_memmap_arrays_with_balanced_classes(filepath_responses: str, dir_out: str) -> None:
    idxs_remove = get_idxs_remove_oversampled_cloudslandwater_human(filepath_responses)
    for attr in ('features', 'responses', 'weights'):
        filepath_in = re.sub('responses', attr, filepath_responses)
        filepath_out = os.path.join(dir_out, os.path.basename(filepath_in))
        create_new_memmap_array(filepath_in, idxs_remove, filepath_out)


def create_new_memmap_arrays_without_waves_or_human(filepath_responses: str, dir_out: str) -> None:
    idxs_remove = get_idxs_remove_waves_change_human(filepath_responses)
    for attr in ('features', 'responses', 'weights'):
        filepath_in = re.sub('responses', attr, filepath_responses)
        filepath_out = os.path.join(dir_out, os.path.basename(filepath_in))
        create_new_memmap_array(filepath_in, idxs_remove, filepath_out)


def get_idxs_only_water_clouds(filepath_responses: str) -> set:
    responses = np.load(filepath_responses, mmap_mode='r')
    # Get homogenous samples
    idxs = {'water': set(), 'waterclouds': set()}
    for idx, sample in enumerate(tqdm(responses, desc='Get indices for water and clouds')):
        codes = np.argmax(sample, axis=-1)
        unique = np.unique(codes)
        if len(unique) == 1 and 1 in unique:
            idxs['water'].add(idx)
        elif len(unique) == 2 and 1 in unique and 7 in unique:
            idxs['waterclouds'].add(idx)
    return idxs


def get_idxs_remove_homogenous(filepath_responses: str) -> set:
    responses = np.load(filepath_responses, mmap_mode='r')
    # Get homogenous samples
    idxs_homogenous = {i: list() for i in range(10)}
    for idx, sample in enumerate(tqdm(responses, desc='Get indices for removal')):
        codes = np.argmax(sample, axis=-1)
        unique = np.unique(codes)
        if len(unique) == 1:
            idxs_homogenous[unique[0]].append(idx)
    # Get list of indices to remove
    idxs_remove = set()
    for code in (0, 1, 6):
        idxs = np.random.choice(idxs_homogenous[code], size=int(0.9 * len(idxs_homogenous[code])), replace=False)
        idxs_remove.update(idxs)
    return idxs_remove


def get_idxs_remove_waves_change_human(filepath_responses: str) -> set:
    responses = np.load(filepath_responses, mmap_mode='r')
    idxs_remove = set()
    for idx, sample in enumerate(tqdm(responses, desc='Get indices for removal')):
        codes = np.argmax(sample, axis=-1)
        if np.any(codes == 5):
            idxs_remove.add(idx)
    return idxs_remove


def get_idxs_remove_oversampled_cloudslandwater_human(filepath_responses: str) -> set:
    responses = np.load(filepath_responses, mmap_mode='r')
    idxs_remove = set()
    chance_remove = {
        '0': 0.60,
        '1': 0.40,
        '01': 0.55,
        '06': 0.50,
        '17': 0.70,
    }
    for idx, sample in enumerate(tqdm(responses, desc='Get indices for removal')):
        codes = np.argmax(sample, axis=-1)
        unique = np.unique(codes)
        label = ''.join([str(val) for val in sorted(unique)])
        if label not in chance_remove:
            continue
        if random.random() < chance_remove[label]:
            idxs_remove.add(idx)
    return idxs_remove



def create_new_memmap_array_removing_idxs(filepath_in: str, idxs_remove: set, filepath_out: str) -> None:
    data = np.load(filepath_in, mmap_mode='r')
    num_samples = data.shape[0] - len(idxs_remove)
    shape_new = tuple([num_samples] + list(data.shape[1:]))
    data_new = np.memmap('tmp.npy', dtype=np.float32, mode='w+', shape=shape_new)
    idx_insert = 0
    for idx_sample, sample in enumerate(tqdm(data, desc='Write new memmap array')):
        if idx_sample in idxs_remove:
            continue
        if 'responses' in filepath_in:
            idxs_human = np.logical_or(sample[..., -1] == 1, sample[..., -2] == 1)
            sample = sample.copy()
            sample[idxs_human, 0] = 1  # Land
            sample[idxs_human, -1] = 0  # Human 1
            sample[idxs_human, -2] = 0  # Human 2
        data_new[idx_insert] = sample
        idx_insert += 1
    np.save(filepath_out, data_new)
    del data_new
    os.remove('tmp.npy')



def create_new_memmap_array_keeping_idxs(filepath_in: str, idxs_keep: set, filepath_out: str) -> None:
    data = np.load(filepath_in, mmap_mode='r')
    shape_new = tuple([len(idxs_keep)] + list(data.shape[1:]))
    data_new = np.memmap('tmp.npy', dtype=np.float32, mode='w+', shape=shape_new)
    idx_insert = 0
    for idx_keep in tqdm(idxs_keep, desc='Write new memmap array'):
        if 'responses' in filepath_in:
            idxs_human = np.logical_or(sample[..., -1] == 1, sample[..., -2] == 1)
            sample = sample.copy()
            sample[idxs_human, 0] = 1  # Land
            sample[idxs_human, -1] = 0  # Human 1
            sample[idxs_human, -2] = 0  # Human 2
        data_new[idx_insert] = sample
        idx_insert += 1
    np.save(filepath_out, data_new)
    del data_new
    os.remove('tmp.npy')



tofix = [os.path.join(dir_out, fn) for fn in os.listdir(dir_out) if fn.startswith('response')]

def fix_codes_human_dev(filepath_responses: str) -> None:
    responses = np.load(filepath_responses, mmap_mode='r+')
    for idx, sample in enumerate(tqdm(responses, desc='Fix response codes')):
        idxs_invalid = np.where(sample[..., -1] == 1)
        sample[idxs_invalid, -1] = 0
        sample[idxs_invalid, -2] = 1
        raise AssertionError('Probably need to save explicitly')
    del responses



def get_response_counts(dir_responses: str) -> Counter:
    filepaths_responses = sorted(
        [os.path.join(dir_responses, fn) for fn in os.listdir(dir_responses) if fn.startswith('responses')]
    )
    counts = Counter()
    for idx_filepath, filepath_response in enumerate(filepaths_responses):
        print('Response file {} ({} total)'.format(idx_filepath, len(filepaths_responses)))
        data = np.load(filepath_response, mmap_mode='r')
        for sample in tqdm(data, desc='Get response counts'):
            counts.update(list(np.ravel(np.argmax(sample, axis=-1))))
    return counts


def update_weights(dir_data: str, response_counts: Counter) -> None:
    filepaths_responses = sorted(
        [os.path.join(dir_data, fn) for fn in os.listdir(dir_data) if fn.startswith('responses')]
    )
    filepaths_weights = [re.sub('responses', 'weights', fp) for fp in filepaths_responses]
    total_count = sum(response_counts.values())
    for idx_filepath, (filepath_response, filepath_weight) in enumerate(zip(filepaths_responses, filepaths_weights)):
        print('Updating weights file {} ({} total)'.format(idx_filepath, len(filepaths_weights)))
        file_responses = np.load(filepath_response, mmap_mode='r')
        file_weights = np.load(filepath_weight, mmap_mode='r+')
        for idx_sample in tqdm(range(file_responses.shape[0]), desc='Update sample weights'):
            sample_responses = file_responses[idx_sample, ...]
            response_indices = np.argmax(sample_responses, axis=-1)
            sample_weights = file_weights[idx_sample, ...]
            for idx_response, count in response_counts.items():
                sample_weights[response_indices == idx_response] = total_count / response_counts[idx_response]
        del file_responses, file_weights


def get_sample_count_less_than_x_classes(dir_responses: str, num_classes: int) -> Counter:
    filepaths_responses = sorted(
        [os.path.join(dir_responses, fn) for fn in os.listdir(dir_responses) if fn.startswith('responses')]
    )
    counts = Counter()
    for idx_filepath, filepath_response in enumerate(filepaths_responses):
        print('Response file {} ({} total)'.format(idx_filepath, len(filepaths_responses)))
        data = np.load(filepath_response, mmap_mode='r')
        for sample in tqdm(data, desc='Get sample counts'):
            codes = np.argmax(sample, axis=-1)
            unique = np.unique(codes)
            if len(unique) < num_classes:
                label = ''.join([str(val) for val in sorted(unique)])
                counts.update([label])
    return counts




"""
mappings = ['land', 'water', 'reef', 'lr', 'wr', 'waves', 'turbid', 'clouds', 'human', 'human']
0 land
1 water
2 reef
3 lr
4 wr
5 waves
6 turbid
7 clouds
8 human
9 human


02_nohumanwaves  sample pcts
water clouds 0.26
land water 0.18
land turbid 0.17
land 0.11
water 0.09
land clouds 0.05
land water clouds 0.04
land water turbid 0.03
clouds 0.02
turbid 0.02
reef 0.01
land reef 0.01
land reef wr 0.0
water turbid 0.0
reef wr 0.0
water reef wr 0.0
land reef lr 0.0
water lr 0.0
land water lr 0.0
land turbid clouds 0.0
land wr 0.0
reef lr 0.0
water lr clouds 0.0
land lr 0.0
land lr turbid 0.0
land reef clouds 0.0
"""