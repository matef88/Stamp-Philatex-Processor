"""
Stamp Philatex Processor - Image Hashing Module
Provides perceptual hashing for duplicate detection.
"""

import numpy as np
from pathlib import Path
from typing import Union, Optional
from PIL import Image
import imagehash


class ImageHasher:
    """
    Perceptual image hashing for duplicate detection.

    Supports multiple algorithms:
    - pHash (perceptual hash): Best for detecting similar images
    - dHash (difference hash): Fast, good for detecting edits
    - aHash (average hash): Simple, fast but less accurate
    - wHash (wavelet hash): Good balance of speed and accuracy
    """

    ALGORITHMS = {
        'phash': imagehash.phash,
        'dhash': imagehash.dhash,
        'ahash': imagehash.average_hash,
        'whash': imagehash.whash
    }

    def __init__(self, algorithm: str = 'phash', hash_size: int = 8):
        """
        Initialize the hasher.

        Args:
            algorithm: Hash algorithm ('phash', 'dhash', 'ahash', 'whash')
            hash_size: Size of hash (larger = more accurate but slower)
        """
        if algorithm not in self.ALGORITHMS:
            raise ValueError(f"Unknown algorithm: {algorithm}. Use one of {list(self.ALGORITHMS.keys())}")

        self.algorithm = algorithm
        self.hash_func = self.ALGORITHMS[algorithm]
        self.hash_size = hash_size

    def compute_hash(self, image: Union[str, Path, Image.Image, np.ndarray]) -> str:
        """
        Compute perceptual hash of an image.

        Args:
            image: Image path, PIL Image, or numpy array

        Returns:
            Hexadecimal hash string
        """
        # Convert to PIL Image if needed
        if isinstance(image, (str, Path)):
            img = Image.open(image)
        elif isinstance(image, np.ndarray):
            # Convert BGR (OpenCV) to RGB
            if len(image.shape) == 3 and image.shape[2] == 3:
                image = image[:, :, ::-1]
            img = Image.fromarray(image)
        elif isinstance(image, Image.Image):
            img = image
        else:
            raise TypeError(f"Unsupported image type: {type(image)}")

        # Compute hash
        hash_value = self.hash_func(img, hash_size=self.hash_size)

        return str(hash_value)

    def compute_hash_from_file(self, file_path: Union[str, Path]) -> str:
        """
        Compute hash from file path.

        Args:
            file_path: Path to image file

        Returns:
            Hexadecimal hash string
        """
        return self.compute_hash(file_path)

    @staticmethod
    def hamming_distance(hash1: str, hash2: str) -> int:
        """
        Calculate Hamming distance between two hashes.

        Args:
            hash1: First hash string
            hash2: Second hash string

        Returns:
            Number of differing bits (0 = identical)
        """
        # Convert hex strings to imagehash objects for comparison
        h1 = imagehash.hex_to_hash(hash1)
        h2 = imagehash.hex_to_hash(hash2)

        return h1 - h2  # imagehash overloads subtraction to return Hamming distance

    def are_similar(self, hash1: str, hash2: str, threshold: int = 10) -> bool:
        """
        Check if two images are similar based on hash comparison.

        Args:
            hash1: First image hash
            hash2: Second image hash
            threshold: Maximum Hamming distance to consider similar

        Returns:
            True if images are similar (Hamming distance <= threshold)
        """
        distance = self.hamming_distance(hash1, hash2)
        return distance <= threshold

    def find_duplicates(
        self,
        hashes: dict,
        threshold: int = 10
    ) -> list:
        """
        Find all duplicate pairs in a collection of hashes.

        Args:
            hashes: Dictionary mapping identifiers to hash strings
            threshold: Similarity threshold

        Returns:
            List of tuples (id1, id2, distance) for duplicates
        """
        duplicates = []
        items = list(hashes.items())

        for i in range(len(items)):
            for j in range(i + 1, len(items)):
                id1, hash1 = items[i]
                id2, hash2 = items[j]

                distance = self.hamming_distance(hash1, hash2)

                if distance <= threshold:
                    duplicates.append((id1, id2, distance))

        return duplicates

    def find_matches(
        self,
        query_hash: str,
        database: dict,
        threshold: int = 10,
        max_results: int = None
    ) -> list:
        """
        Find matching images in a database.

        Args:
            query_hash: Hash of query image
            database: Dictionary mapping identifiers to hash strings
            threshold: Maximum distance to consider a match
            max_results: Maximum number of results to return

        Returns:
            List of tuples (identifier, distance) sorted by distance
        """
        matches = []

        for identifier, stored_hash in database.items():
            distance = self.hamming_distance(query_hash, stored_hash)

            if distance <= threshold:
                matches.append((identifier, distance))

        # Sort by distance
        matches.sort(key=lambda x: x[1])

        if max_results:
            matches = matches[:max_results]

        return matches


class MultiHasher:
    """
    Uses multiple hash algorithms for more robust duplicate detection.
    """

    def __init__(self, algorithms: list = None):
        """
        Initialize multi-algorithm hasher.

        Args:
            algorithms: List of algorithm names to use
        """
        if algorithms is None:
            algorithms = ['phash', 'dhash']

        self.hashers = {alg: ImageHasher(alg) for alg in algorithms}

    def compute_hashes(self, image: Union[str, Path, Image.Image, np.ndarray]) -> dict:
        """
        Compute multiple hashes for an image.

        Args:
            image: Input image

        Returns:
            Dictionary mapping algorithm names to hash strings
        """
        return {
            name: hasher.compute_hash(image)
            for name, hasher in self.hashers.items()
        }

    def are_similar(
        self,
        hashes1: dict,
        hashes2: dict,
        thresholds: dict = None,
        require_all: bool = False
    ) -> bool:
        """
        Check similarity using multiple algorithms.

        Args:
            hashes1: First image's hashes
            hashes2: Second image's hashes
            thresholds: Per-algorithm thresholds
            require_all: If True, all algorithms must agree

        Returns:
            True if images are similar
        """
        if thresholds is None:
            thresholds = {'phash': 10, 'dhash': 10, 'ahash': 10, 'whash': 10}

        results = []

        for alg, hasher in self.hashers.items():
            if alg in hashes1 and alg in hashes2:
                threshold = thresholds.get(alg, 10)
                is_similar = hasher.are_similar(hashes1[alg], hashes2[alg], threshold)
                results.append(is_similar)

        if not results:
            return False

        if require_all:
            return all(results)
        else:
            return any(results)


def compute_hash(image_path: Union[str, Path], algorithm: str = 'phash') -> str:
    """
    Convenience function to compute hash of an image.

    Args:
        image_path: Path to image
        algorithm: Hash algorithm

    Returns:
        Hash string
    """
    hasher = ImageHasher(algorithm)
    return hasher.compute_hash(image_path)


def are_duplicates(
    image1: Union[str, Path],
    image2: Union[str, Path],
    threshold: int = 10,
    algorithm: str = 'phash'
) -> bool:
    """
    Check if two images are duplicates.

    Args:
        image1: First image path
        image2: Second image path
        threshold: Similarity threshold
        algorithm: Hash algorithm

    Returns:
        True if images are duplicates
    """
    hasher = ImageHasher(algorithm)
    hash1 = hasher.compute_hash(image1)
    hash2 = hasher.compute_hash(image2)
    return hasher.are_similar(hash1, hash2, threshold)


if __name__ == "__main__":
    # Test the hashing module
    import sys

    if len(sys.argv) < 2:
        print("Usage: python image_hash.py <image1> [image2]")
        print("\nIf one image: compute and display hash")
        print("If two images: compare and show similarity")
        sys.exit(1)

    hasher = ImageHasher('phash')

    if len(sys.argv) == 2:
        # Single image - compute hash
        image_path = sys.argv[1]
        hash_value = hasher.compute_hash(image_path)
        print(f"Image: {image_path}")
        print(f"pHash: {hash_value}")

    else:
        # Two images - compare
        image1, image2 = sys.argv[1], sys.argv[2]

        hash1 = hasher.compute_hash(image1)
        hash2 = hasher.compute_hash(image2)

        distance = hasher.hamming_distance(hash1, hash2)

        print(f"Image 1: {image1}")
        print(f"  Hash: {hash1}")
        print(f"\nImage 2: {image2}")
        print(f"  Hash: {hash2}")
        print(f"\nHamming Distance: {distance}")
        print(f"Similar (threshold 10): {'Yes' if distance <= 10 else 'No'}")
