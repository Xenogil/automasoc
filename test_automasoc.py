import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from tempfile import TemporaryDirectory

from automasoc import Scheduler


class SchedulerTests(unittest.TestCase):
    def test_schedule_persists_and_loads_post(self):
        with TemporaryDirectory() as directory:
            store = Path(directory) / "posts.json"
            scheduler = Scheduler(store)
            post = scheduler.schedule(
                "Twitter",
                "  Hello, world!  ",
                datetime(2026, 11, 20, 12, tzinfo=timezone.utc),
            )

            reloaded = Scheduler(store)
            self.assertEqual(reloaded.posts[post.id].text, "Hello, world!")
            self.assertEqual(reloaded.posts[post.id].platform, "twitter")

    def test_due_only_returns_scheduled_posts_at_or_before_now(self):
        with TemporaryDirectory() as directory:
            scheduler = Scheduler(Path(directory) / "posts.json")
            now = datetime(2026, 11, 20, 12, tzinfo=timezone.utc)
            due_post = scheduler.schedule("mastodon", "Ready", now - timedelta(minutes=1))
            scheduler.schedule("linkedin", "Later", now + timedelta(minutes=1))

            self.assertEqual([post.id for post in scheduler.due(now)], [due_post.id])

            scheduler.mark_posted(due_post.id)
            self.assertEqual(scheduler.due(now), [])

    def test_invalid_post_is_rejected(self):
        with TemporaryDirectory() as directory:
            scheduler = Scheduler(Path(directory) / "posts.json")
            with self.assertRaises(ValueError):
                scheduler.schedule("unknown", "Text", datetime.now(timezone.utc))
            with self.assertRaises(ValueError):
                scheduler.schedule("bluesky", "  ", datetime.now(timezone.utc))


if __name__ == "__main__":
    unittest.main()
