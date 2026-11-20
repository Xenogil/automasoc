# automasoc

A small, dependency-free scheduler for planning social media posts. It stores posts locally in JSON and can list posts that are ready to publish.

## Usage

```bash
python -m automasoc --store posts.json schedule twitter "Hello, world!" 2026-11-20T12:00:00Z
python -m automasoc --store posts.json list
python -m automasoc --store posts.json due --now 2026-11-20T12:01:00Z
```

## Python API

```python
from datetime import datetime, timezone
from automasoc import Scheduler

scheduler = Scheduler("posts.json")
post = scheduler.schedule(
    "mastodon",
    "A scheduled update",
    datetime.now(timezone.utc),
)
for due_post in scheduler.due():
    # Send due_post to the platform's API, then record the result.
    scheduler.mark_posted(due_post.id)
```