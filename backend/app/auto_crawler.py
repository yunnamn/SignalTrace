import asyncio
from backend.app.database import SessionLocal
from backend.app.models import ContentLog, WatchTarget
from backend.app.connectors.youtube import YouTubeConnector
from backend.app.connectors.vk import VKConnector
from backend.app.connectors.telegram import TelegramConnector
from backend.app.url_utils import canonicalize_url

class AutoCrawler:
    def __init__(self):
        self.is_running = False
        self.task = None
        self.profile_id = None
        self.added_count = 0
        self.pending_keys = set()
        
        self.connectors = {
            "youtube": YouTubeConnector(),
            "vk": VKConnector(),
            "telegram": TelegramConnector()
        }

    def start(self, url_queue, profile_id):
        if self.is_running:
            return
        self.is_running = True
        self.profile_id = profile_id
        self.added_count = 0
        self.task = asyncio.create_task(self._crawl_loop(url_queue))
        print(f"AutoCrawler started with profile_id {profile_id}")

    def stop(self):
        self.is_running = False
        if self.task:
            self.task.cancel()
            self.task = None
        print("AutoCrawler stopped.")

    def _source_id(self, post_url):
        return canonicalize_url(post_url)

    def _preview_url(self, content_preview):
        if not content_preview:
            return None
        return content_preview.split(" ||| ")[-1]

    def _key(self, post_url, profile_id=None):
        return (self._source_id(post_url), profile_id if profile_id is not None else self.profile_id)

    def release_pending(self, dedupe_key):
        if dedupe_key:
            self.pending_keys.discard(tuple(dedupe_key))

    def _is_duplicate(self, post_url, profile_id=None):
        source_id = self._source_id(post_url)
        profile_id = profile_id if profile_id is not None else self.profile_id
        db = SessionLocal()
        try:
            if db.query(ContentLog).filter(
                ContentLog.source_id == source_id,
                ContentLog.profile_id == profile_id,
            ).first():
                return True

            old_logs = db.query(ContentLog.content_preview).filter(
                ContentLog.source_id == None,
                ContentLog.profile_id == profile_id,
            ).all()
            for (preview,) in old_logs:
                preview_url = self._preview_url(preview)
                try:
                    if preview_url and canonicalize_url(preview_url) == source_id:
                        return True
                except ValueError:
                    continue
            return False
        finally:
            db.close()

    async def _queue_posts(self, posts, url_queue):
        added = 0
        seen_source_ids = set()
        for post in posts:
            source_id = self._source_id(post["post_url"])
            dedupe_key = (source_id, self.profile_id)
            if source_id in seen_source_ids or dedupe_key in self.pending_keys:
                continue
            seen_source_ids.add(source_id)
            if not self._is_duplicate(post["post_url"]):
                print(f"AutoCrawler found new post: {post['post_url']}")
                self.pending_keys.add(dedupe_key)
                await url_queue.add(
                    url=post["post_url"],
                    profile_id=self.profile_id,
                    text=post["caption_text"],
                    title=post["caption_text"][:50] if post["caption_text"] else "No Title",
                    platform=post["platform"],
                    author_handle=post["author_handle"],
                    author_url=post["author_url"],
                    media_url=post.get("media_url"),
                    dedupe_key=dedupe_key,
                    on_complete=self.release_pending,
                )
                added += 1
        self.added_count += added
        return added

    async def _crawl_loop(self, url_queue):
        while self.is_running:
            try:
                db = SessionLocal()
                targets = db.query(WatchTarget).filter(WatchTarget.is_active == True).all()
                db.close()
                
                for target in targets:
                    if not self.is_running:
                        break
                        
                    connector = self.connectors.get(target.platform)
                    if not connector:
                        continue
                        
                    print(f"AutoCrawler checking target: {target.platform} - {target.target}")
                    
                    try:
                        posts = await asyncio.to_thread(connector.fetch_feed, target.target)
                        await self._queue_posts(posts, url_queue)
                    except Exception as e:
                        print(f"AutoCrawler fetch error on {target.platform}:{target.target}: {e}")
                        
                    # Wait between targets
                    await asyncio.sleep(5)
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"AutoCrawler error: {e}")
                
            # Wait before starting the next full loop
            if self.is_running:
                await asyncio.sleep(30)

auto_crawler_instance = AutoCrawler()
