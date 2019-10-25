"""
Note:  L4 has a collision for code "2", which represents attributes "brackish atoll lagoon" (824 instances) and
"bay exposed fringing" (462 instances). I added a code for the latter manually
"""


MAPPINGS_L1 = {
    0: 'oceanic',
    1: 'continental',
    2: 'main land',
    2000: 'deep water',  # Added manually to account for deep water
    2001: 'clouds',  # Added manually to account for clouds
}

MAPPINGS_L2 = {
    1: 'Oceanic atoll',
    2: 'Oceanic uplifted/filled atoll',
    3: 'Oceanic Bank',
    4: 'Oceanic island',
    5: 'Continental atoll',
    7: 'Continental bank',
    8: 'Continental island',
    9: 'Continental Patch complex',
    10: 'Continental intra-shelf barrier',
    11: 'Continental outer shelf barrier',
    12: 'Continental Fringing',
    13: 'Shelf marginal structures',
    14: 'cross shelf',
    1000: 'main land',
    1001: 'aquatic land features',
    2000: 'deep water',  # Added manually to account for deep water
    2001: 'clouds',  # Added manually to account for clouds
}

MAPPINGS_L3 = {
    1: 'Drowned atoll',
    2: 'Atoll rim',
    3: 'Atoll rim land',
    4: 'Atoll lagoon',
    5: 'Atoll patch',
    6: 'Atoll patch land',
    7: 'Uplifted atoll',
    8: 'Drowned bank',
    9: 'Bank barrier',
    10: 'Bank barrier land',
    11: 'Bank lagoon',
    12: 'Bank patch',
    13: 'Bank patch land',
    14: 'Island lagoon',
    15: 'Barrier land',
    16: 'Outer Barrier Reef Complex',
    17: 'Multiple Barrier Complex',
    18: 'Imbricated Barrier Reef Complex',
    19: 'Coastal Barrier Reef Complex',
    20: 'Barrier-Fringing Reef Complex',
    21: 'Faro Barrier Reef Complex',
    22: 'Coastal/fringing patch',
    23: 'Patch land',
    24: 'Intra-lagoon patch-reef complex',
    25: 'Intra-seas patch-reef complex',
    26: 'Shelf patch-reef complex',
    27: 'Ocean exposed fringing',
    28: 'Intra-seas exposed fringing',
    29: 'Lagoon exposed fringing',
    30: 'Bay exposed fringing',
    31: 'Diffuse fringing',
    32: 'Fringing of coastal barrier complex',
    33: 'Fringing of  barrier-fringing complex',
    34: 'Exposed shelf reef',
    35: 'Sheltered margin reef',
    36: 'Shelf terrace',
    37: 'Shelf structure',
    38: 'Shelf slope',
    40: 'Cross Shelf',
    1000: 'Main Land',
    1001: 'Aquatic Land Features',
    2000: 'deep water',  # Added manually to account for deep water
    2001: 'clouds',  # Added manually to account for clouds
}

MAPPINGS_L4 = {
    1: 'barrier reef pinnacle/patch',
    2: 'brackish atoll lagoon',
    3: 'bridge',
    4: 'channel',
    5: 'crest',
    6: 'cross shelf',
    7: 'deep drowned reef flat',
    8: 'deep lagoon',
    9: 'deep lagoon with constructions',
    10: 'deep terrace',
    11: 'deep terrace with constructions',
    12: 'diffuse fringing',
    13: 'double barrier lagoon',
    15: 'drowned bank',
    16: 'drowned inner slope',
    17: 'drowned lagoon',
    18: 'drowned pass',
    19: 'drowned patch',
    20: 'drowned rim',
    21: 'enclosed basin',
    22: 'enclosed lagoon',
    23: 'enclosed lagoon or basin',
    24: 'enclosed lagoon or basin with constructions',
    25: 'enclosed lagoon with constructions',
    27: 'faro enclosed lagoon',
    28: 'faro forereef',
    29: 'faro reef flat',
    30: 'forereef',
    31: 'forereef or terrace',
    32: 'fractal reef flat',
    33: 'haa enclosed lagoon',
    34: 'haa subtidal reef flat',
    35: 'immature reef flat',
    37: 'inner slope',
    38: 'inner terrace',
    39: 'intermediate reef flat',
    40: 'lagoon pinnacle',
    41: 'linear reef flat',
    42: 'outer terrace',
    43: 'pass',
    44: 'pass reef flat',
    47: 'pinnacle',
    48: 'reef flat',
    49: 'reticulated fringing',
    50: 'ridge and fossil crest',
    51: 'shallow lagoon',
    52: 'shallow lagoon with constructions',
    53: 'shallow lagoonal terrace',
    54: 'shallow lagoonal terrace with constructions',
    56: 'shallow terrace',
    57: 'shallow terrace with constructions',
    58: 'shelf hardground',
    59: 'shelf slope',
    60: 'shelf terrace',
    61: 'shelf terrace with constructions',
    63: 'subtidal reef flat',
    64: 'undetermined envelope',
    65: 'uplifted reef flat',
    66: 'bay exposed fringing',  # Added manually due to collision
    999: 'land on reef',
    1000: 'main land',
    1001: 'aquatic land features',
    2000: 'deep water',  # Added manually to account for deep water
    2001: 'clouds',  # Added manually to account for clouds
}

MAPPINGS_RB = {
    0: 'non-reef',
    1: 'land',
    2: 'barrier island',
    3: 'barrier continental',
    4: 'barrier atoll-bank',
    5: 'fringing island',
    6: 'fringing continental',
    7: 'patch island',
    8: 'patch continental',
    9: 'patch atoll-bank',
    10: 'shelf island',
    11: 'shelf continental',
}

MAPPINGS_DEPTH = {
    0: 'shallow',
    1: 'variable',
    2: 'deep',
    3: 'land',
    2000: 'deep water',  # Added manually to account for deep water
    2001: 'clouds',  # Added manually to account for clouds
}


# Mappings for converting Millennium Project classes to a subset of visually distinct classes
# Assumptions
# Reef and non reef features should be kept separate
# Shallow and variable depth features should be kept separate
# Deep features are not always visible in the imagery and should be removed
# Features with constructions mess up the training data because they cover many different patterns with the reef
# "webbing" or constructions running through them, and they are inexact when they match up with the visual pattern; it's
# probably better to not fit over these areas and then let the model split them later based on what it's learned.
# Example:  terrace with constructions is actually two separate things, a terrace and the constructions on it; the model
# learns terraces and reef features through other classes, and should be able to divide up the terrace with
# constructions rather than group it all into one class.
# Water within land features and other water features are distinct enough to have separate classes


CODE_LAND = 0  # Dark brown
CODE_WATER_TERRESTRIAL = 1  # Light brown
CODE_LAND_SUPP = 2000  # Dark brown

CODE_WATER_SHALLOW = 10  # Light blue
CODE_WATER_DEEP = 11  # Dark blue
CODE_WATER_SUPP = 2001  # Dark blue

CODE_FOREREEF = 20   # Medium green
CODE_REEFFLAT_SHALLOW = 21  # Light green
CODE_REEFFLAT_VARIABLE = 22  # Light green
CODE_PINNACLES = 23  # Medium green
CODE_CONSTRUCTIONS = -9999  # Pink

CODE_NONREEF_SHALLOW = 30  # Light yellow
CODE_NONREEF_VARIABLE = 31  # Medium yellow
CODE_NONREEF_DEEP = 32  # Dark yellow

CODE_CLOUDS_SUPP = 2002  # Gray

CODE_REMOVE = -9999  # Either not many examples, not clear examples, or not in imagery (drowned classes)
CODE_UNKNOWN = -9999  # Pretty sure this class is unknown


MAPPINGS_CUSTOM = {
    999: CODE_LAND,  # 'land on reef',  ~13000
    1000: CODE_LAND,  # 'main land',  ~35000

    2: CODE_WATER_TERRESTRIAL,  # 'brackish atoll lagoon',  ~1000
    1001: CODE_WATER_TERRESTRIAL,  # 'aquatic land features',  ~7000

    4: CODE_WATER_SHALLOW,  # 'channel',
    21: CODE_WATER_SHALLOW,  # 'enclosed basin',  ~1000
    22: CODE_WATER_SHALLOW,  # 'enclosed lagoon',  ~1000
    23: CODE_WATER_SHALLOW,  # 'enclosed lagoon or basin',  ~1000
    27: CODE_WATER_SHALLOW,  # 'faro enclosed lagoon',  ~ 1000
    51: CODE_WATER_SHALLOW,  # 'shallow lagoon',

    8: CODE_WATER_DEEP,  # 'deep lagoon',  ~1000
    13: CODE_WATER_DEEP,  # 'double barrier lagoon',
    17: CODE_WATER_DEEP,  # 'drowned lagoon',
    33: CODE_WATER_DEEP,  # 'haa enclosed lagoon',
    43: CODE_WATER_DEEP,  # 'pass',  ~1000

    28: CODE_FOREREEF,  # 'faro forereef',
    30: CODE_FOREREEF,  # 'forereef',  ~20000

    5: CODE_REEFFLAT_SHALLOW,  # 'crest',
    29: CODE_REEFFLAT_SHALLOW,  # 'faro reef flat',  ~1300
    32: CODE_REEFFLAT_SHALLOW,  # 'fractal reef flat',
    39: CODE_REEFFLAT_SHALLOW,  # 'intermediate reef flat',
    41: CODE_REEFFLAT_SHALLOW,  # 'linear reef flat',
    44: CODE_REEFFLAT_SHALLOW,  # 'pass reef flat',
    48: CODE_REEFFLAT_SHALLOW,  # 'reef flat',  ~55000
    50: CODE_REEFFLAT_SHALLOW,  # 'ridge and fossil crest',
    65: CODE_REEFFLAT_SHALLOW,  # 'uplifted reef flat',
    66: CODE_REEFFLAT_SHALLOW,  # 'bay exposed fringing',  # Added manually due to collision

    # Reticulated fringing can be a bit poorly defined, e.g., Solomon Islands, where it looks much like nonreef features
    # and doesn't match the visual imagery well, removing to avoid contaminating dataset
    49: CODE_REMOVE,  # 'reticulated fringing',

    35: CODE_REEFFLAT_VARIABLE,  # 'immature reef flat',  ~20000
    63: CODE_REEFFLAT_VARIABLE,  # 'subtidal reef flat',

    1: CODE_PINNACLES,  # 'barrier reef pinnacle/patch',  ~22000
    40: CODE_PINNACLES,  # 'lagoon pinnacle',  ~3000
    47: CODE_PINNACLES,  # 'pinnacle',  ~2000

    9: CODE_CONSTRUCTIONS,  # 'deep lagoon with constructions',
    11: CODE_CONSTRUCTIONS,  # 'deep terrace with constructions',
    24: CODE_CONSTRUCTIONS,  # 'enclosed lagoon or basin with constructions',
    25: CODE_CONSTRUCTIONS,  # 'enclosed lagoon with constructions',
    52: CODE_CONSTRUCTIONS,  # 'shallow lagoon with constructions',
    54: CODE_CONSTRUCTIONS,  # 'shallow lagoonal terrace with constructions',
    57: CODE_CONSTRUCTIONS,  # 'shallow terrace with constructions',
    61: CODE_CONSTRUCTIONS,  # 'shelf terrace with constructions',

    12: CODE_NONREEF_SHALLOW,  # 'diffuse fringing',  ~3000

    6: CODE_NONREEF_VARIABLE,  # 'cross shelf',
    37: CODE_NONREEF_VARIABLE,  # 'inner slope',  ~1000
    38: CODE_NONREEF_VARIABLE,  # 'inner terrace',
    42: CODE_NONREEF_VARIABLE,  # 'outer terrace',
    53: CODE_NONREEF_VARIABLE,  # 'shallow lagoonal terrace',
    56: CODE_NONREEF_VARIABLE,  # 'shallow terrace',  ~12000
    60: CODE_NONREEF_VARIABLE,  # 'shelf terrace',  ~1000

    58: CODE_NONREEF_DEEP,  # 'shelf hardground',
    59: CODE_NONREEF_DEEP,  # 'shelf slope',  ~2000

    3: CODE_REMOVE,  # 'bridge',
    7: CODE_REMOVE,  # 'deep drowned reef flat',
    10: CODE_REMOVE,  # 'deep terrace',
    15: CODE_REMOVE,  # 'drowned bank',
    16: CODE_REMOVE,  # 'drowned inner slope',
    18: CODE_REMOVE,  # 'drowned pass',
    19: CODE_REMOVE,  # 'drowned patch',
    20: CODE_REMOVE,  # 'drowned rim',
    31: CODE_REMOVE,  # 'forereef or terrace',
    34: CODE_REMOVE,  # 'haa subtidal reef flat',

    64: CODE_UNKNOWN,  # 'undetermined envelope',
}


def _parse_all_codes():
    """
    Not meant to be called, was used to parse codes and keeping it here in case it's useful in the future
    """
    all_codes = dict()
    filenames = [fn for fn in os.listdir('.') if fn.endswith('.shp')]
    for fn in tqdm(filenames):
        features = fiona.open(fn)
        for feature in features:
            properties = feature['properties']
            for meta in ('L1', 'L2', 'L3', 'L4', 'L5', 'RB'):
                code = properties.get(meta + 'CODE')
                attr = properties.get(meta + '_ATTRIB')
                all_codes.setdefault(meta, dict()).setdefault(code, Counter()).update([attr])
            code = properties.get('DEPTHCODE')
            attr = properties.get('DEPTHLABEL')
            all_codes.setdefault('DEPTH', dict()).setdefault(code, Counter()).update([attr])
            all_codes.setdefault('VALIDATED', set()).update([properties.get('Validated')])


def _parse_codes_another_way():
    """
    Not meant to be called, was used to parse codes and keeping it here in case it's useful in the future
    """
    from collections import Counter
    import os
    import fiona
    from tqdm import tqdm
    code_counter = Counter()
    reef_counter = dict()
    filenames = [fn for fn in os.listdir('.') if fn.endswith('.shp')]
    for fn in tqdm(filenames):
        features = fiona.open(fn)
        for feature in features:
            reef_counter.setdefault(feature['properties']['L4_ATTRIB'], Counter()).update([feature['properties']['REEF']])
            attr = ('L4_ATTRIB', 'REEF', 'DEPTHLABEL', 'RB_DEPTH_A') #'L3_ATTRIB', 'RB_ATTRIB')
            label = ' / '.join([str(feature['properties'].get(a)) for a in attr])
            code_counter.update([label])


def _get_duplicated_codes():
    """
    Not meant to be called, was used to parse codes and keeping it here in case it's useful in the future
    """
    for k, v in all_codes.items():
        for kk, vv in v.items():
            if len(vv) > 1:
                print(k, kk, vv)


def _print_encodings_in_dictionary_format():
    """
    Not meant to be called, was used to parse codes and keeping it here in case it's useful in the future, meant to use
    the parsed dictionary from the above function

    Exclude L5 because there are no attributes names

    There's a duplicate in L4
    """
    for meta in ('L1', 'L2', 'L3', 'L4', 'RB', 'DEPTH'):
        mappings = sorted([(code, counter.most_common()[0][0]) for code, counter in all_codes[meta].items()],
                          key=lambda x: x[0])
        print(meta)
        for m in mappings:
            print('    {}: \'{}\','.format(m[0], m[1]))
        for _ in range(3):
            print()
