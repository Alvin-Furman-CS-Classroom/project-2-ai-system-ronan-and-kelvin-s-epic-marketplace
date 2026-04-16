"""
Shared vocabulary for detecting accessory-style product titles (cases, bags, etc.).

Used by :mod:`src.module3.query_understanding` (search ranking) and
:mod:`src.module4.query_features` (LTR title relevance) so the signal stays
consistent across modules.
"""

from __future__ import annotations

# Words that often indicate a product is an accessory *for* a device rather than
# the device itself (e.g. "laptop bag" vs "laptop").
ACCESSORY_PRODUCT_WORDS: frozenset[str] = frozenset({
    "bag", "case", "sleeve", "stand", "cover", "protector",
    "charger", "adapter", "cable", "dock", "hub", "mount",
    "pad", "mat", "backpack", "skin", "sticker", "decal",
    "holder", "cooler", "cooling", "fan", "tray", "table",
    "lock", "strap", "keyboard", "mouse", "compatible",
    "replacement", "carrying", "pouch", "rack", "bracket",
    "riser", "organizer", "shelf", "clip", "docking", "converter",
    "desk", "light", "lamp", "speaker", "pillow", "tote",
    "purse", "messenger", "satchel", "briefcase", "drive",
    "battery", "memory", "module", "disk", "dvd", "privacy",
})
