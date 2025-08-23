#!/usr/bin/env python3
"""
Database Module
Handles all database operations for storing scraped posts.
"""

import sqlite3
import json
import logging
from typing import List, Dict, Any


class DatabaseManager:
    """Manages database operations for scraped posts."""

    def __init__(self, db_path: str = "facebook_posts.db"):
        self.db_path = db_path
        self.logger = logging.getLogger(f"{__name__}.DatabaseManager")
        self._setup_database()

    def _setup_database(self):
        """Initialize the database and create tables if they don't exist."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS posts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    post_id TEXT UNIQUE,
                    author TEXT,
                    content TEXT,
                    timestamp TEXT,
                    likes_count INTEGER,
                    comments_count INTEGER,
                    shares_count INTEGER,
                    post_url TEXT,
                    group_name TEXT,
                    scraped_at TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            conn.commit()
            conn.close()
            self.logger.info(f"Database initialized successfully at {self.db_path}")

        except Exception as e:
            self.logger.error(f"Failed to setup database: {str(e)}")
            raise

    def save_posts(self, posts: List[Dict[str, Any]]) -> int:
        """Save posts to the database."""
        if not posts:
            return 0

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            saved_count = 0
            for post in posts:
                try:
                    cursor.execute(
                        """
                        INSERT OR IGNORE INTO posts 
                        (post_id, author, content, timestamp, likes_count, comments_count,
                         shares_count, post_url, group_name, scraped_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                        (
                            post.get("post_id"),
                            post.get("author"),
                            post.get("content"),
                            post.get("timestamp"),
                            post.get("likes_count", 0),
                            post.get("comments_count", 0),
                            post.get("shares_count", 0),
                            post.get("post_url"),
                            post.get("group_name"),
                            post.get("scraped_at"),
                        ),
                    )
                    saved_count += 1
                except Exception as e:
                    self.logger.error(
                        f"Error saving post {post.get('post_id')}: {str(e)}"
                    )
                    continue

            conn.commit()
            conn.close()

            self.logger.info(f"Saved {saved_count} posts to database")
            return saved_count

        except Exception as e:
            self.logger.error(f"Database error: {str(e)}")
            return 0

    def get_posts(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """Retrieve posts from the database."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT post_id, author, content, timestamp, likes_count, comments_count,
                       shares_count, post_url, group_name, scraped_at, created_at
                FROM posts 
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?
            """,
                (limit, offset),
            )

            rows = cursor.fetchall()
            conn.close()

            posts = []
            for row in rows:
                posts.append(
                    {
                        "post_id": row[0],
                        "author": row[1],
                        "content": row[2],
                        "timestamp": row[3],
                        "likes_count": row[4],
                        "comments_count": row[5],
                        "shares_count": row[6],
                        "post_url": row[7],
                        "group_name": row[8],
                        "scraped_at": row[9],
                        "created_at": row[10],
                    }
                )

            return posts

        except Exception as e:
            self.logger.error(f"Error retrieving posts: {str(e)}")
            return []

    def get_posts_by_group(
        self, group_name: str, limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Retrieve posts from a specific group."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT post_id, author, content, timestamp, likes_count, comments_count,
                       shares_count, post_url, group_name, scraped_at, created_at
                FROM posts 
                WHERE group_name = ?
                ORDER BY created_at DESC
                LIMIT ?
            """,
                (group_name, limit),
            )

            rows = cursor.fetchall()
            conn.close()

            posts = []
            for row in rows:
                posts.append(
                    {
                        "post_id": row[0],
                        "author": row[1],
                        "content": row[2],
                        "timestamp": row[3],
                        "likes_count": row[4],
                        "comments_count": row[5],
                        "shares_count": row[6],
                        "post_url": row[7],
                        "group_name": row[8],
                        "scraped_at": row[9],
                        "created_at": row[10],
                    }
                )

            return posts

        except Exception as e:
            self.logger.error(f"Error retrieving posts by group: {str(e)}")
            return []

    def get_post_count(self) -> int:
        """Get total number of posts in the database."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("SELECT COUNT(*) FROM posts")
            count = cursor.fetchone()[0]

            conn.close()
            return count

        except Exception as e:
            self.logger.error(f"Error getting post count: {str(e)}")
            return 0

    def delete_post(self, post_id: str) -> bool:
        """Delete a specific post from the database."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("DELETE FROM posts WHERE post_id = ?", (post_id,))
            deleted_count = cursor.rowcount

            conn.commit()
            conn.close()

            if deleted_count > 0:
                self.logger.info(f"Deleted post {post_id}")
                return True
            else:
                self.logger.warning(f"Post {post_id} not found")
                return False

        except Exception as e:
            self.logger.error(f"Error deleting post: {str(e)}")
            return False

    def clear_database(self) -> bool:
        """Clear all posts from the database."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("DELETE FROM posts")
            deleted_count = cursor.rowcount

            conn.commit()
            conn.close()

            self.logger.info(f"Cleared {deleted_count} posts from database")
            return True

        except Exception as e:
            self.logger.error(f"Error clearing database: {str(e)}")
            return False

    def export_to_json(self, filename: str = "facebook_posts.json") -> bool:
        """Export all posts to a JSON file."""
        try:
            posts = self.get_posts(limit=10000)  # Get all posts

            with open(filename, "w", encoding="utf-8") as f:
                json.dump(posts, f, indent=2, ensure_ascii=False)

            self.logger.info(f"Exported {len(posts)} posts to {filename}")
            return True

        except Exception as e:
            self.logger.error(f"Error exporting to JSON: {str(e)}")
            return False

    def get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Get total post count
            cursor.execute("SELECT COUNT(*) FROM posts")
            total_posts = cursor.fetchone()[0]

            # Get group count
            cursor.execute("SELECT COUNT(DISTINCT group_name) FROM posts")
            group_count = cursor.fetchone()[0]

            # Get latest post date
            cursor.execute("SELECT MAX(created_at) FROM posts")
            latest_post = cursor.fetchone()[0]

            conn.close()

            return {
                "total_posts": total_posts,
                "group_count": group_count,
                "latest_post_date": latest_post,
                "database_path": self.db_path,
            }

        except Exception as e:
            self.logger.error(f"Error getting database stats: {str(e)}")
            return {}

    def close(self):
        """Close database connections."""
        # SQLite connections are automatically closed, but we can add cleanup here if needed
        pass

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
