#!/usr/bin/env python3
"""
Build a curated 200k-product working set of *actual electronic devices*,
excluding accessories (cases, cables, bags, adapters, stands, etc.).

Pass 1 — scan metadata, apply category + title filters, collect eligible ASINs.
Pass 2 — randomly sample 200k from the eligible pool.
Pass 3 — re-read metadata, write only selected ASINs.
Pass 4 — scan reviews, collect up to 2 reviews per selected ASIN.
Pass 5 — verify: every product has a valid ASIN, every review maps to a product.

Usage::

    python scripts/build_working_set_200k.py
    python scripts/build_working_set_200k.py --target 100000 --seed 7
"""

from __future__ import annotations

import argparse
import gzip
import json
import random
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

# ── main_category whitelist ──────────────────────────────────────────────
ALLOWED_MAIN_CATEGORIES = frozenset({
    "All Electronics",
    "Computers",
    "Camera & Photo",
    "Cell Phones & Accessories",
    "Home Audio & Theater",
    "Car Electronics",
    "Amazon Devices",
    "Portable Audio & Accessories",
    "GPS & Navigation",
    "Apple Products",
    "Amazon Fire TV",
})

# ── category-path blacklist ──────────────────────────────────────────────
# If ANY element in the product's `categories` list matches one of these
# (case-insensitive substring), the product is excluded.
CATEGORY_BLACKLIST_TERMS = [
    "laptop accessories",
    "tablet accessories",
    "tablet replacement parts",
    "skins & decals",
    "decals",
    "sleeves",
    "laptop bags",
    "bags & cases",
    "camera bags",
    "cable organizer",
    "cord management",
    "ac adapters",
    "power converters",
    "power strips",
    "surge protectors",
    "telephone accessories",
    "mp3 & mp4 player accessories",
    "gps system accessories",
    "vehicle electronics accessories",
    "arm & wristband accessories",
    "clips, arm & wristbands",
    "earpads",
    "headphone adapters",
    "headphone extension",
    "extension cords",
    "cases",  # headphone cases, eBook covers, etc.
    "covers",
    "screen protectors",
    "mounts",
    "stands",
    "office electronics accessories",
    "cleaning & repair",
    "cables & accessories",
    "computer cable adapters",
    "audio & video accessories",
    "memory card accessories",
    "hard drive accessories",
    "monitor accessories",
    "cable security",
    "blank media",
    "usb gadgets",
    "media storage",
    "racks & cabinets",
    "home audio accessories",
    "warranties",
    "service plans",
    "tripods & monopods",
    "straps",
    "battery holders",
    "replacement parts",
    "remote controls",
]

# ── title-level blacklist ────────────────────────────────────────────────
# Products whose title contains any of these words/phrases are excluded.
# NOTE: "case", "cover", "sleeve" etc. are handled separately in
# ACCESSORY_TITLE_TERMS (checked first, with no safelist override).
TITLE_BLACKLIST_TERMS = [
    "mount ",
    " mount",
    "bracket",
    "wall plate",
    "cable ",
    " cable",
    "adapter ",
    " adapter",
    "adaptor",
    "charger ",
    " charger",
    "charging ",
    "cord ",
    " cord",
    "extension",
    "converter",
    "replacement band",
    "wrist band",
    "wristband",
    "arm band",
    "armband",
    "strap ",
    " strap",
    "cleaning kit",
    "cleaning cloth",
    "screen wipe",
    "lens pen",
    "carrying bag",
    "travel bag",
    "backpack",
    "tote",
    "organizer",
    "holder",
    "clip ",
    " clip",
    "stand ",
    " stand",
    "tripod",
    "monopod",
    "remote control",
    "surge protector",
    "power strip",
    "wall mount",
    "desk mount",
    "car mount",
    "bike mount",
    "suction cup",
    "replacement battery",
    "replacement part",
    "antenna",
    "backdrop",
    "background",
    "green screen",
    "photo studio",
    "light box",
    "softbox",
    "umbrella light",
    "reflector",
    "diffuser",
    "filter ",
    " filter",
    "lens cap",
    "lens hood",
    "memory card",
    "sd card",
    "micro sd",
    "usb hub",
    "docking station",
    "dock ",
    " dock",
    "cradle",
    "car seat",
    "camp chair",
    "furniture",
    "bag ",
    " bag",
    "tray",
    "basket",
    "mat ",
    " mat",
    "pad ",
    " pad",
    "cushion",
]


CATEGORY_ELEMENT_WHITELIST = frozenset({
    "computer accessories & peripherals",
    "headphones, earbuds & accessories",
    "keyboards, mice & accessories",
})

ACCESSORY_TITLE_TERMS = [
    "case",
    "cover",
    "sleeve",
    "pouch",
    "holster",
    "protector",
    "screen guard",
    "skin ",
    " skin",
    "decal",
    "sticker",
    "film ",
    " film",
    "folio",
    "bumper",
    "shell ",
    " shell",
]


def _categories_pass(cats: list[str]) -> bool:
    """Return True if the category path looks like a real device, not an accessory."""
    for element in cats:
        el = element.lower()
        if el in CATEGORY_ELEMENT_WHITELIST:
            continue
        for term in CATEGORY_BLACKLIST_TERMS:
            if term in el:
                return False
        if el == "accessories":
            return False
    return True


def _title_pass(title: str) -> bool:
    """Return True if the title doesn't look like an accessory."""
    t = title.lower()

    # If the title contains an accessory indicator, reject it even if
    # a device keyword is also present (e.g. "iPhone Case" is still a case).
    for acc in ACCESSORY_TITLE_TERMS:
        if acc in t:
            return False

    # Check remaining blacklist (cables, adapters, mounts, etc.)
    for bad in TITLE_BLACKLIST_TERMS:
        if bad in t:
            # But if the product IS a device, rescue it (e.g. "charger station"
            # is an accessory, but "laptop" is a device even if the title also
            # says "charging").  Only rescue when the title's primary subject
            # is a device, not when a device name is incidental.
            return False

    return True


def _is_valid_product(obj: dict) -> bool:
    """Full eligibility check: main_category + categories path + title + required fields."""
    mc = obj.get("main_category")
    if mc not in ALLOWED_MAIN_CATEGORIES:
        return False

    title = obj.get("title")
    asin = obj.get("parent_asin")
    if not title or not asin:
        return False

    cats = obj.get("categories", [])
    if not _categories_pass(cats):
        return False

    if not _title_pass(title):
        return False

    return True


def main() -> None:
    parser = argparse.ArgumentParser(description="Build curated 200k electronics working set")
    parser.add_argument("--target", type=int, default=200_000, help="Number of products to select")
    parser.add_argument("--reviews-per-product", type=int, default=2, help="Reviews to keep per product")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument(
        "--meta-in",
        type=Path,
        default=REPO_ROOT / "datasets" / "active" / "meta_Electronics.jsonl.gz",
    )
    parser.add_argument(
        "--reviews-in",
        type=Path,
        default=REPO_ROOT / "datasets" / "active" / "Electronics.jsonl.gz",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=REPO_ROOT / "datasets" / "working_set",
    )
    args = parser.parse_args()

    rng = random.Random(args.seed)
    t0 = time.perf_counter()

    # ── Pass 1: scan metadata, collect eligible ASINs ────────────────────
    print(f"[Pass 1] Scanning metadata for eligible products ...")
    eligible_asins: list[str] = []
    total = 0
    cat_counts: Counter = Counter()

    with gzip.open(str(args.meta_in), "rt", encoding="utf-8") as f:
        for line in f:
            total += 1
            obj = json.loads(line)
            if _is_valid_product(obj):
                asin = obj["parent_asin"]
                eligible_asins.append(asin)
                mc = obj.get("main_category", "?")
                cat_counts[mc] += 1

            if total % 200_000 == 0:
                print(f"  ... scanned {total:,d} products, {len(eligible_asins):,d} eligible so far")

    print(f"  Done: {total:,d} total, {len(eligible_asins):,d} eligible ({100*len(eligible_asins)/total:.1f}%)")
    print(f"  Eligible by main_category:")
    for cat, n in cat_counts.most_common():
        print(f"    {n:>8,d}  {cat}")

    if len(eligible_asins) < args.target:
        print(
            f"\n  WARNING: only {len(eligible_asins):,d} eligible products, "
            f"target was {args.target:,d}. Using all eligible.",
            file=sys.stderr,
        )
        selected = set(eligible_asins)
    else:
        rng.shuffle(eligible_asins)
        selected = set(eligible_asins[: args.target])

    print(f"\n[Pass 2] Selected {len(selected):,d} products (seed={args.seed})")

    # ── Pass 3: re-read metadata, write selected products ────────────────
    meta_out = args.out_dir / "meta_Electronics_200k.jsonl.gz"
    args.out_dir.mkdir(parents=True, exist_ok=True)
    print(f"[Pass 3] Writing selected metadata -> {meta_out}")

    written_meta = 0
    written_cats: Counter = Counter()
    with gzip.open(str(args.meta_in), "rt", encoding="utf-8") as fin, \
         gzip.open(str(meta_out), "wt", encoding="utf-8") as fout:
        for line in fin:
            obj = json.loads(line)
            asin = obj.get("parent_asin")
            if asin in selected:
                fout.write(line)
                written_meta += 1
                written_cats[obj.get("main_category", "?")] += 1
                if written_meta % 50_000 == 0:
                    print(f"  ... written {written_meta:,d}")

    print(f"  Wrote {written_meta:,d} product records")
    print(f"  By main_category:")
    for cat, n in written_cats.most_common():
        print(f"    {n:>8,d}  {cat}")

    # ── Pass 4: scan reviews, keep up to N per selected ASIN ─────────────
    reviews_out = args.out_dir / "Electronics_200k.jsonl.gz"
    print(f"\n[Pass 4] Scanning reviews, keeping {args.reviews_per_product} per product -> {reviews_out}")

    review_count_per_asin: Counter = Counter()
    written_reviews = 0
    total_reviews = 0
    products_with_reviews: set[str] = set()

    with gzip.open(str(args.reviews_in), "rt", encoding="utf-8") as fin, \
         gzip.open(str(reviews_out), "wt", encoding="utf-8") as fout:
        for line in fin:
            total_reviews += 1
            obj = json.loads(line)
            asin = obj.get("parent_asin")
            if asin in selected and review_count_per_asin[asin] < args.reviews_per_product:
                fout.write(line)
                review_count_per_asin[asin] += 1
                written_reviews += 1
                products_with_reviews.add(asin)

            if total_reviews % 2_000_000 == 0:
                print(f"  ... scanned {total_reviews:,d} reviews, kept {written_reviews:,d}")

    print(f"  Scanned {total_reviews:,d} reviews total")
    print(f"  Wrote {written_reviews:,d} reviews for {len(products_with_reviews):,d} products")

    products_without_reviews = selected - products_with_reviews
    print(f"  Products with 0 reviews: {len(products_without_reviews):,d}")

    review_dist = Counter(review_count_per_asin.values())
    print(f"  Review count distribution:")
    for count, n_products in sorted(review_dist.items()):
        print(f"    {count} reviews: {n_products:,d} products")

    # ── Pass 5: verification ─────────────────────────────────────────────
    print(f"\n[Pass 5] Verifying output files ...")
    errors = 0

    verify_meta_asins: set[str] = set()
    with gzip.open(str(meta_out), "rt", encoding="utf-8") as f:
        for line in f:
            obj = json.loads(line)
            asin = obj.get("parent_asin")
            title = obj.get("title")
            if not asin or not title:
                print(f"  ERROR: metadata record missing asin or title: {line[:80]}")
                errors += 1
            verify_meta_asins.add(asin)

    verify_review_asins: set[str] = set()
    orphan_reviews = 0
    with gzip.open(str(reviews_out), "rt", encoding="utf-8") as f:
        for line in f:
            obj = json.loads(line)
            asin = obj.get("parent_asin")
            if asin not in verify_meta_asins:
                orphan_reviews += 1
                errors += 1
            verify_review_asins.add(asin)

    print(f"  Metadata file: {len(verify_meta_asins):,d} unique ASINs")
    print(f"  Reviews file:  {len(verify_review_asins):,d} unique ASINs with reviews")
    print(f"  Orphan reviews (no matching product): {orphan_reviews}")

    if verify_meta_asins != selected:
        diff = selected - verify_meta_asins
        print(f"  WARNING: {len(diff)} selected ASINs missing from output metadata")
        errors += 1

    elapsed = time.perf_counter() - t0
    print(f"\n{'='*60}")
    if errors == 0:
        print(f"  SUCCESS — {written_meta:,d} products, {written_reviews:,d} reviews")
    else:
        print(f"  COMPLETED WITH {errors} ERROR(S)")
    print(f"  Elapsed: {elapsed:.0f}s")
    print(f"  Output: {meta_out}")
    print(f"          {reviews_out}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
