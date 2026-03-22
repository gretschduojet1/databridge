from enum import Enum


class Region(str, Enum):
    NORTHEAST = "Northeast"
    SOUTHEAST = "Southeast"
    MIDWEST = "Midwest"
    WEST = "West"


class Category(str, Enum):
    ELECTRONICS = "Electronics"
    OFFICE = "Office"
    SUPPLIES = "Supplies"
