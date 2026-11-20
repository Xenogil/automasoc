"""Storage and scheduling primitives for social media posts."""

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Optional
import json
import uuid


SUPPORTED_PLATFORMS = ("bluesky", "facebook", "instagram", "linkedin", "mastodon", "twitter")


def _utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


@dataclass(frozen=True)
class Post:
    id: str
    platform: str
    text: str
    scheduled_at: datetime
    status: str = "scheduled"

    def to_dict(self) -> dict:
        data = asdict(self)
        data["scheduled_at"] = self.scheduled_at.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: dict) -> "Post":
        return cls(
            id=data["id"],
            platform=data["platform"],
            text=data["text"],
            scheduled_at=_utc(datetime.fromisoformat(data["scheduled_at"])),
            status=data.get("status", "scheduled"),
        )


class Scheduler:
    """Manage scheduled posts in a local JSON file."""

    def __init__(self, store: Optional[Path | str] = None):
        self.store = Path(store or "automasoc.json")
        self.posts: dict[str, Post] = {}
        self._load()

    def _load(self) -> None:
        if not self.store.exists():
            return
        with self.store.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
        self.posts = {item["id"]: Post.from_dict(item) for item in data}

    def _save(self) -> None:
        self.store.parent.mkdir(parents=True, exist_ok=True)
        with self.store.open("w", encoding="utf-8") as handle:
            json.dump([post.to_dict() for post in self.posts.values()], handle, indent=2)

    def schedule(self, platform: str, text: str, scheduled_at: datetime) -> Post:
        platform = platform.lower().strip()
        if platform not in SUPPORTED_PLATFORMS:
            raise ValueError("Unsupported platform: {}".format(platform))
        text = text.strip()
        if not text:
            raise ValueError("Post text cannot be empty")
        scheduled_at = _utc(scheduled_at)

        post = Post(
            id=str(uuid.uuid4()),
            platform=platform,
            text=text,
            scheduled_at=scheduled_at,
        )
        self.posts[post.id] = post
        self._save()
        return post

    def due(self, now: Optional[datetime] = None) -> list[Post]:
        now = _utc(now or datetime.now(timezone.utc))
        return sorted(
            (
                post
                for post in self.posts.values()
                if post.status == "scheduled" and post.scheduled_at <= now
            ),
            key=lambda post: post.scheduled_at,
        )

    def mark_posted(self, post_id: str) -> Post:
        post = self.posts.get(post_id)
        if post is None:
            raise KeyError(post_id)
        updated = Post(
            id=post.id,
            platform=post.platform,
            text=post.text,
            scheduled_at=post.scheduled_at,
            status="posted",
        )
        self.posts[post_id] = updated
        self._save()
        return updated

    def cancel(self, post_id: str) -> Post:
        post = self.posts.get(post_id)
        if post is None:
            raise KeyError(post_id)
        updated = Post(
            id=post.id,
            platform=post.platform,
            text=post.text,
            scheduled_at=post.scheduled_at,
            status="cancelled",
        )
        self.posts[post_id] = updated
        self._save()
        return updated

    def list(self, status: Optional[str] = None) -> Iterable[Post]:
        posts = self.posts.values()
        if status is not None:
            posts = (post for post in posts if post.status == status)
        return sorted(posts, key=lambda post: post.scheduled_at)
