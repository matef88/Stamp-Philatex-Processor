"""
Stamp Detection Claude - Duplicate Detection Module
Detects duplicate stamps across batches and within batches.
"""

import sys
import os
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Set, Union
import numpy as np
from dataclasses import dataclass
from datetime import datetime
import shutil

try:
    from utils import load_config, get_project_root, setup_logging, ensure_dirs
    from image_hash import ImageHasher, compute_hash
    from database import StampDatabase
except ImportError:
    sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
    from scripts.utils import load_config, get_project_root, setup_logging, ensure_dirs
    from scripts.image_hash import ImageHasher, compute_hash
    from scripts.database import StampDatabase


@dataclass
class DuplicateMatch:
    """Represents a duplicate match."""
    query_path: Path
    query_hash: str
    match_id: int
    match_path: str
    match_hash: str
    distance: int
    match_type: str  # 'cross_batch' or 'within_batch'


class DuplicateDetector:
    """
    Detects duplicate stamps using perceptual hashing.

    Features:
    - Cross-batch detection (against previously processed stamps)
    - Within-batch detection (duplicates in current batch)
    - Configurable similarity threshold
    - Multiple actions: skip, flag, move
    """

    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize duplicate detector.

        Args:
            config: Configuration dictionary
        """
        self.config = config or load_config()
        self.logger = setup_logging("DuplicateDetector")

        # Get duplicate config
        dup_config = self.config.get('duplicates', {})

        self.enabled = dup_config.get('enabled', True)
        self.algorithm = dup_config.get('hash_algorithm', 'phash')
        self.threshold = dup_config.get('similarity_threshold', 10)
        self.check_cross_batch = dup_config.get('check_cross_batch', True)
        self.check_within_batch = dup_config.get('check_within_batch', True)
        self.action = dup_config.get('duplicate_action', 'flag')

        # Initialize hasher and database
        self.hasher = ImageHasher(self.algorithm)
        self.database = StampDatabase()

        # Setup duplicates folder if needed
        if self.action == 'move':
            self.duplicates_folder = get_project_root() / dup_config.get(
                'duplicates_folder', 'output/duplicates'
            )
            ensure_dirs([self.duplicates_folder])

        # Cache for within-batch detection
        self._batch_hashes: Dict[str, str] = {}

    def compute_image_hash(self, image: Union[str, Path, np.ndarray]) -> str:
        """
        Compute hash for an image.

        Args:
            image: Path to image or numpy array

        Returns:
            Hash string
        """
        return self.hasher.compute_hash(image)

    def check_cross_batch_duplicate(self, image_hash: str) -> Optional[DuplicateMatch]:
        """
        Check if image is duplicate of previously processed stamp.

        Args:
            image_hash: Hash of current image

        Returns:
            DuplicateMatch if found, None otherwise
        """
        if not self.check_cross_batch:
            return None

        is_dup, original_id = self.database.is_duplicate(image_hash, self.threshold)

        if is_dup and original_id:
            original = self.database.get_stamp_by_id(original_id)

            if original:
                distance = self.hasher.hamming_distance(image_hash, original['phash'])

                return DuplicateMatch(
                    query_path=Path(""),  # Will be set by caller
                    query_hash=image_hash,
                    match_id=original_id,
                    match_path=original['original_path'],
                    match_hash=original['phash'],
                    distance=distance,
                    match_type='cross_batch'
                )

        return None

    def check_within_batch_duplicate(
        self,
        image_path: Path,
        image_hash: str
    ) -> Optional[DuplicateMatch]:
        """
        Check if image is duplicate within current batch.

        Args:
            image_path: Path to current image
            image_hash: Hash of current image

        Returns:
            DuplicateMatch if found, None otherwise
        """
        if not self.check_within_batch:
            return None

        # Check against batch cache
        # If image_path is None (e.g. in-memory processing), we skip self-check logic
        # or we assume caller handles it.
        str_path = str(image_path) if image_path else ""

        for cached_path, cached_hash in self._batch_hashes.items():
            if str_path and cached_path == str_path:
                continue

            distance = self.hasher.hamming_distance(image_hash, cached_hash)

            if distance <= self.threshold:
                return DuplicateMatch(
                    query_path=image_path if image_path else Path("memory"),
                    query_hash=image_hash,
                    match_id=-1,  # Not in database yet
                    match_path=cached_path,
                    match_hash=cached_hash,
                    distance=distance,
                    match_type='within_batch'
                )

        return None

    def check_duplicate(self, image: Union[str, Path, np.ndarray], path_id: Optional[Union[str, Path]] = None) -> Tuple[bool, Optional[DuplicateMatch]]:
        """
        Check if an image is a duplicate.

        Args:
            image: Image path or numpy array
            path_id: Identifier for the image (file path), used for cache/self-check

        Returns:
            Tuple of (is_duplicate, match_info)
        """
        if not self.enabled:
            return False, None

        # Compute hash
        image_hash = self.compute_image_hash(image)

        # Use path_id if provided, otherwise check if image is a path
        if path_id is None and isinstance(image, (str, Path)):
            path_id = image

        # Check within batch first (faster)
        within_match = self.check_within_batch_duplicate(path_id, image_hash)
        if within_match:
            within_match.query_path = path_id if path_id else Path("memory")
            return True, within_match

        # Check cross-batch
        cross_match = self.check_cross_batch_duplicate(image_hash)
        if cross_match:
            cross_match.query_path = path_id if path_id else Path("memory")
            return True, cross_match

        # Add to batch cache if we have an ID
        if path_id:
            self._batch_hashes[str(path_id)] = image_hash

        return False, None

    def handle_duplicate(
        self,
        image_path: Path,
        match: DuplicateMatch
    ) -> str:
        """
        Handle a detected duplicate based on configured action.

        Args:
            image_path: Path to duplicate image
            match: Match information

        Returns:
            Action taken: 'skipped', 'flagged', or 'moved'
        """
        if self.action == 'skip':
            self.logger.info(f"Skipping duplicate: {image_path.name} "
                           f"(matches {Path(match.match_path).name}, distance={match.distance})")
            return 'skipped'

        elif self.action == 'move':
            # Move to duplicates folder
            dest_path = self.duplicates_folder / image_path.name

            # Handle name conflicts
            if dest_path.exists():
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                dest_path = self.duplicates_folder / f"{image_path.stem}_{timestamp}{image_path.suffix}"

            shutil.move(str(image_path), str(dest_path))
            self.logger.info(f"Moved duplicate: {image_path.name} -> {dest_path.name}")
            return 'moved'

        else:  # 'flag' - default action
            self.logger.info(f"Flagged duplicate: {image_path.name} "
                           f"(matches {Path(match.match_path).name}, distance={match.distance})")
            return 'flagged'

    def start_batch(self) -> None:
        """Clear batch cache for new processing batch."""
        self._batch_hashes.clear()

    def end_batch(self) -> Dict[str, int]:
        """
        End batch and return statistics.

        Returns:
            Dictionary with batch statistics
        """
        stats = {
            'images_in_batch': len(self._batch_hashes),
        }

        self._batch_hashes.clear()
        return stats

    def find_all_duplicates_in_database(self) -> List[Tuple[Dict, Dict, int]]:
        """
        Find all duplicate pairs in the database.

        Returns:
            List of (stamp1, stamp2, distance) tuples
        """
        all_hashes = self.database.get_all_hashes()

        duplicates = []
        checked = set()

        for id1, hash1 in all_hashes.items():
            for id2, hash2 in all_hashes.items():
                if id1 >= id2:
                    continue

                pair_key = (min(id1, id2), max(id1, id2))
                if pair_key in checked:
                    continue

                checked.add(pair_key)

                distance = self.hasher.hamming_distance(hash1, hash2)

                if distance <= self.threshold:
                    stamp1 = self.database.get_stamp_by_id(id1)
                    stamp2 = self.database.get_stamp_by_id(id2)

                    if stamp1 and stamp2:
                        duplicates.append((stamp1, stamp2, distance))

        return duplicates

    def get_duplicate_groups(self) -> List[List[Dict]]:
        """
        Group duplicates together.

        Returns:
            List of groups, where each group is a list of similar stamps
        """
        all_hashes = self.database.get_all_hashes()

        # Union-Find for grouping
        parent = {id_: id_ for id_ in all_hashes.keys()}

        def find(x):
            if parent[x] != x:
                parent[x] = find(parent[x])
            return parent[x]

        def union(x, y):
            px, py = find(x), find(y)
            if px != py:
                parent[px] = py

        # Connect similar stamps
        ids = list(all_hashes.keys())
        for i in range(len(ids)):
            for j in range(i + 1, len(ids)):
                id1, id2 = ids[i], ids[j]
                distance = self.hasher.hamming_distance(all_hashes[id1], all_hashes[id2])

                if distance <= self.threshold:
                    union(id1, id2)

        # Group by root
        groups_dict = {}
        for id_ in ids:
            root = find(id_)
            if root not in groups_dict:
                groups_dict[root] = []
            groups_dict[root].append(id_)

        # Convert to stamp records
        groups = []
        for group_ids in groups_dict.values():
            if len(group_ids) > 1:  # Only include actual duplicates
                group = [self.database.get_stamp_by_id(id_) for id_ in group_ids]
                group = [s for s in group if s is not None]
                if group:
                    groups.append(group)

        return groups


def check_duplicates_batch(
    image_paths: List[Path],
    config: Optional[Dict] = None
) -> Dict[Path, Optional[DuplicateMatch]]:
    """
    Check multiple images for duplicates.

    Args:
        image_paths: List of image paths
        config: Configuration dictionary

    Returns:
        Dictionary mapping paths to match info (None if not duplicate)
    """
    detector = DuplicateDetector(config)
    detector.start_batch()

    results = {}
    for path in image_paths:
        is_dup, match = detector.check_duplicate(path)
        results[path] = match if is_dup else None

    detector.end_batch()
    return results


if __name__ == "__main__":
    # Test duplicate detection
    import argparse

    parser = argparse.ArgumentParser(description="Duplicate Detection Utility")
    parser.add_argument("--scan", type=str, help="Scan directory for duplicates")
    parser.add_argument("--compare", type=str, nargs=2, help="Compare two images")
    parser.add_argument("--stats", action="store_true", help="Show database statistics")

    args = parser.parse_args()

    detector = DuplicateDetector()

    if args.compare:
        # Compare two images
        img1, img2 = args.compare
        hash1 = detector.compute_image_hash(Path(img1))
        hash2 = detector.compute_image_hash(Path(img2))

        distance = detector.hasher.hamming_distance(hash1, hash2)

        print(f"Image 1: {img1}")
        print(f"  Hash: {hash1}")
        print(f"\nImage 2: {img2}")
        print(f"  Hash: {hash2}")
        print(f"\nHamming Distance: {distance}")
        print(f"Are Duplicates (threshold {detector.threshold}): {'Yes' if distance <= detector.threshold else 'No'}")

    elif args.scan:
        # Scan directory
        from utils import get_image_files

        image_files = get_image_files(Path(args.scan))
        print(f"Scanning {len(image_files)} images...")

        detector.start_batch()
        duplicates = []

        for img_path in image_files:
            is_dup, match = detector.check_duplicate(img_path)
            if is_dup:
                duplicates.append((img_path, match))

        print(f"\nFound {len(duplicates)} duplicates:")
        for path, match in duplicates:
            print(f"  {path.name} -> {Path(match.match_path).name} (distance: {match.distance})")

    elif args.stats:
        # Show statistics
        stats = detector.database.get_statistics()
        print("Database Statistics:")
        for key, value in stats.items():
            print(f"  {key}: {value}")

        groups = detector.get_duplicate_groups()
        print(f"\nDuplicate groups: {len(groups)}")

    else:
        parser.print_help()
