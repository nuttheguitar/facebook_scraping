#!/usr/bin/env python3
"""
Models Module
Defines Facebook-specific data models and structures.
"""

from dataclasses import dataclass, asdict
from typing import Dict, Any, Optional
from strategies.base_scraper import ScrapedContent


@dataclass(kw_only=True)
class FacebookPost(ScrapedContent):
    """Facebook-specific post data model."""
    # Override base class fields to make them required
    content: str
    url: str
    scraped_at: str
    # Facebook-specific required fields
    post_id: str
    author: str
    timestamp: str
    post_url: str
    # Optional fields with defaults
    content_id: Optional[str] = None
    title: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    likes_count: int = 0
    comments_count: int = 0
    shares_count: int = 0
    group_name: str = ""

    def __post_init__(self):
        """Set up metadata after initialization."""
        if self.metadata is None:
            self.metadata = {}
        self.metadata.update({
            'likes_count': self.likes_count,
            'comments_count': self.comments_count,
            'shares_count': self.shares_count,
            'group_name': self.group_name,
            'platform': 'facebook',
            'content_type': 'post'
        })

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FacebookPost':
        """Create FacebookPost instance from dictionary."""
        return cls(
            content=data.get('content', ''),
            url=data.get('url', ''),
            scraped_at=data.get('scraped_at', ''),
            post_id=data.get('post_id', ''),
            author=data.get('author', ''),
            timestamp=data.get('timestamp', ''),
            post_url=data.get('post_url', ''),
            content_id=data.get('content_id'),
            title=data.get('title'),
            metadata=data.get('metadata', {}),
            likes_count=data.get('likes_count', 0),
            comments_count=data.get('comments_count', 0),
            shares_count=data.get('shares_count', 0),
            group_name=data.get('group_name', '')
        )

    def get_engagement_score(self) -> float:
        """Calculate engagement score based on likes, comments, and shares."""
        return (self.likes_count * 1.0 +
                self.comments_count * 2.0 +
                self.shares_count * 3.0)

    def is_high_engagement(self, threshold: float = 10.0) -> bool:
        """Check if post has high engagement."""
        return self.get_engagement_score() >= threshold
