"""
Stamp Philatex Processor - Database Module
SQLite database for tracking processed stamps and duplicates."""

import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple
from contextlib import contextmanager
import json
import sys
import os

try:
    from utils import get_project_root, load_config, ensure_dirs
except ImportError:
    sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
    from scripts.utils import get_project_root, load_config, ensure_dirs


class StampDatabase:
    """
    SQLite database for tracking processed stamps.

    Stores:
    - Original and processed file paths
    - Perceptual hashes for duplicate detection
    - Processing metadata (confidence, timestamps, etc.)
    - Duplicate relationships
    """

    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize database connection.

        Args:
            db_path: Path to SQLite database file
        """
        if db_path is None:
            config = load_config()
            db_path = get_project_root() / config.get('paths', {}).get('database', 'database/stamps.db')

        self.db_path = Path(db_path)

        # DON'T create directory here - let _init_database() do it when needed
        # This prevents creating database folder in exe location

        self._init_database()

    @contextmanager
    def _get_connection(self):
        """Context manager for database connections."""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _init_database(self) -> None:
        """Initialize database schema."""
        # Create directory if needed (lazy creation)
        ensure_dirs([self.db_path.parent])

        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Main stamps table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS stamps (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    original_path TEXT NOT NULL,
                    processed_path TEXT,
                    phash TEXT,
                    dhash TEXT,
                    confidence REAL,
                    num_detections INTEGER,
                    processing_time REAL,
                    processed_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                    is_duplicate BOOLEAN DEFAULT 0,
                    duplicate_of INTEGER,
                    batch_id TEXT,
                    metadata TEXT,
                    FOREIGN KEY (duplicate_of) REFERENCES stamps(id)
                )
            ''')

            # Index for fast hash lookups
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_phash ON stamps(phash)
            ''')

            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_dhash ON stamps(dhash)
            ''')

            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_original_path ON stamps(original_path)
            ''')

            # Batches table for tracking processing sessions
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS batches (
                    id TEXT PRIMARY KEY,
                    start_time DATETIME DEFAULT CURRENT_TIMESTAMP,
                    end_time DATETIME,
                    total_images INTEGER,
                    successful INTEGER,
                    failed INTEGER,
                    duplicates INTEGER,
                    input_path TEXT,
                    status TEXT DEFAULT 'in_progress'
                )
            ''')

    def add_stamp(
        self,
        original_path: str,
        processed_path: Optional[str] = None,
        phash: Optional[str] = None,
        dhash: Optional[str] = None,
        confidence: float = 0.0,
        num_detections: int = 0,
        processing_time: float = 0.0,
        is_duplicate: bool = False,
        duplicate_of: Optional[int] = None,
        batch_id: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> int:
        """
        Add a processed stamp to the database.

        Args:
            original_path: Path to original image
            processed_path: Path to processed output
            phash: Perceptual hash
            dhash: Difference hash
            confidence: Detection confidence
            num_detections: Number of stamps detected
            processing_time: Processing time in seconds
            is_duplicate: Whether this is a duplicate
            duplicate_of: ID of original if duplicate
            batch_id: Processing batch identifier
            metadata: Additional metadata as dictionary

        Returns:
            ID of inserted record
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            metadata_json = json.dumps(metadata) if metadata else None

            cursor.execute('''
                INSERT INTO stamps (
                    original_path, processed_path, phash, dhash,
                    confidence, num_detections, processing_time,
                    is_duplicate, duplicate_of, batch_id, metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                str(original_path), str(processed_path) if processed_path else None,
                phash, dhash, confidence, num_detections, processing_time,
                is_duplicate, duplicate_of, batch_id, metadata_json
            ))

            return cursor.lastrowid

    def get_stamp_by_id(self, stamp_id: int) -> Optional[Dict]:
        """Get stamp record by ID."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM stamps WHERE id = ?', (stamp_id,))
            row = cursor.fetchone()

            if row:
                return dict(row)
            return None

    def get_stamp_by_path(self, original_path: str) -> Optional[Dict]:
        """Get stamp record by original path."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM stamps WHERE original_path = ?', (str(original_path),))
            row = cursor.fetchone()

            if row:
                return dict(row)
            return None

    def find_by_hash(
        self,
        phash: str,
        threshold: int = 10,
        limit: int = 10
    ) -> List[Tuple[Dict, int]]:
        """
        Find similar stamps by perceptual hash.

        Note: SQLite doesn't support Hamming distance natively,
        so we fetch candidates and filter in Python.

        Args:
            phash: Query hash
            threshold: Maximum Hamming distance
            limit: Maximum results

        Returns:
            List of (stamp_dict, distance) tuples
        """
        # Import here to avoid circular dependency
        from image_hash import ImageHasher

        hasher = ImageHasher()

        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Get all hashes (in production, use locality-sensitive hashing for scale)
            cursor.execute('SELECT id, phash FROM stamps WHERE phash IS NOT NULL')
            rows = cursor.fetchall()

            matches = []
            for row in rows:
                stored_hash = row['phash']
                distance = hasher.hamming_distance(phash, stored_hash)

                if distance <= threshold:
                    stamp = self.get_stamp_by_id(row['id'])
                    matches.append((stamp, distance))

            # Sort by distance and limit
            matches.sort(key=lambda x: x[1])
            return matches[:limit]

    def is_duplicate(self, phash: str, threshold: int = 10) -> Tuple[bool, Optional[int]]:
        """
        Check if a hash represents a duplicate.

        Args:
            phash: Hash to check
            threshold: Similarity threshold

        Returns:
            Tuple of (is_duplicate, original_id)
        """
        matches = self.find_by_hash(phash, threshold, limit=1)

        if matches:
            return True, matches[0][0]['id']

        return False, None

    def get_all_hashes(self) -> Dict[int, str]:
        """
        Get all stored hashes.

        Returns:
            Dictionary mapping stamp IDs to phash strings
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT id, phash FROM stamps WHERE phash IS NOT NULL')

            return {row['id']: row['phash'] for row in cursor.fetchall()}

    def get_duplicates(self, limit: int = 100) -> List[Dict]:
        """Get all records marked as duplicates."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT s.*, d.original_path as duplicate_original_path
                FROM stamps s
                LEFT JOIN stamps d ON s.duplicate_of = d.id
                WHERE s.is_duplicate = 1
                ORDER BY s.processed_date DESC
                LIMIT ?
            ''', (limit,))

            return [dict(row) for row in cursor.fetchall()]

    def get_statistics(self) -> Dict[str, Any]:
        """Get database statistics."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            stats = {}

            # Total stamps
            cursor.execute('SELECT COUNT(*) as count FROM stamps')
            stats['total_stamps'] = cursor.fetchone()['count']

            # Duplicates
            cursor.execute('SELECT COUNT(*) as count FROM stamps WHERE is_duplicate = 1')
            stats['total_duplicates'] = cursor.fetchone()['count']

            # Unique stamps
            stats['unique_stamps'] = stats['total_stamps'] - stats['total_duplicates']

            # Average confidence
            cursor.execute('SELECT AVG(confidence) as avg FROM stamps WHERE confidence > 0')
            row = cursor.fetchone()
            stats['average_confidence'] = row['avg'] if row['avg'] else 0

            # Processing batches
            cursor.execute('SELECT COUNT(*) as count FROM batches')
            stats['total_batches'] = cursor.fetchone()['count']

            # Latest processing date
            cursor.execute('SELECT MAX(processed_date) as latest FROM stamps')
            stats['last_processed'] = cursor.fetchone()['latest']

            return stats

    # Batch management methods

    def start_batch(self, batch_id: str, input_path: str, total_images: int) -> None:
        """Start a new processing batch."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO batches (id, input_path, total_images, successful, failed, duplicates)
                VALUES (?, ?, ?, 0, 0, 0)
            ''', (batch_id, str(input_path), total_images))

    def update_batch(
        self,
        batch_id: str,
        successful: int = None,
        failed: int = None,
        duplicates: int = None,
        status: str = None
    ) -> None:
        """Update batch statistics."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            updates = []
            params = []

            if successful is not None:
                updates.append('successful = ?')
                params.append(successful)
            if failed is not None:
                updates.append('failed = ?')
                params.append(failed)
            if duplicates is not None:
                updates.append('duplicates = ?')
                params.append(duplicates)
            if status is not None:
                updates.append('status = ?')
                params.append(status)
                if status == 'completed':
                    updates.append('end_time = CURRENT_TIMESTAMP')

            if updates:
                params.append(batch_id)
                cursor.execute(f'''
                    UPDATE batches SET {', '.join(updates)} WHERE id = ?
                ''', params)

    def get_batch(self, batch_id: str) -> Optional[Dict]:
        """Get batch information."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM batches WHERE id = ?', (batch_id,))
            row = cursor.fetchone()

            if row:
                return dict(row)
            return None

    def get_recent_batches(self, limit: int = 10) -> List[Dict]:
        """Get recent processing batches."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM batches ORDER BY start_time DESC LIMIT ?
            ''', (limit,))

            return [dict(row) for row in cursor.fetchall()]

    def clear_all(self) -> None:
        """Clear all data from database. Use with caution!"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM stamps')
            cursor.execute('DELETE FROM batches')

    def export_to_csv(self, output_path: str) -> None:
        """Export stamps table to CSV."""
        import csv

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM stamps')
            rows = cursor.fetchall()

            if not rows:
                return

            with open(output_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(rows[0].keys())
                writer.writerows([tuple(row) for row in rows])


if __name__ == "__main__":
    # Test the database
    db = StampDatabase()

    print("Database Statistics:")
    stats = db.get_statistics()
    for key, value in stats.items():
        print(f"  {key}: {value}")
