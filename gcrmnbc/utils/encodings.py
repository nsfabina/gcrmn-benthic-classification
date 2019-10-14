# Original encodings

LAND = 'Land'
WATER = 'Deep Reef Water 10m+'
REEF_TOP = 'Reef Top'
NOT_REEF_TOP = 'Not Reef Top'
CLOUD_SHADE = 'Cloud-Shade'
UNKNOWN = 'Unknown'

# Fabina-generated boundary classes

EDGE_LW = 'Land-Water boundary'
EDGE_LR = 'Land-Reef boundary'
EDGE_LN = 'Land-NotReef boundary'
EDGE_WR = 'Water-Reef boundary'
EDGE_WN = 'Water-NotReef boundary'
EDGE_RN = 'Reef-NotReef boundary'

# Model-generated supplemental classes

CLOUDS = 'clouds'
HUMAN_DEVELOPMENT = 'human development'
WATER_TURBID = 'turbid water'
WAVES_BREAKING = 'breaking waves'


MAPPINGS = {
    LAND: 1,
    WATER: 2,
    REEF_TOP: 3,
    NOT_REEF_TOP: 4,
    CLOUD_SHADE: 5,
    UNKNOWN: 6,

    EDGE_LW: 11,
    EDGE_LR: 12,
    EDGE_LN: 13,
    EDGE_WR: 14,
    EDGE_WN: 15,
    EDGE_RN: 16,

    WAVES_BREAKING: 21,
    WATER_TURBID: 22,
    CLOUDS: 23,
    HUMAN_DEVELOPMENT: 24,
}
