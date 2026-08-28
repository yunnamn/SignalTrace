import asyncio
import traceback
from backend.app.database import SessionLocal
from backend.app.models import Profile, ContentLog
import requests
from bs4 import BeautifulSoup
from backend.app.url_utils import URLValidationError, canonicalize_url, validate_public_url

import itertools

class URLQueue:
    def __init__(self):
        self.is_running = False
        self.task = None
        self.queue = asyncio.PriorityQueue()
        self.last_processed_url = None
        self._counter = itertools.count()

    @property
    def queue_size(self):
        return self.queue.qsize()

    async def add(self, url: str, profile_id: int, text: str = None, title: str = None, priority: int = 1, platform: str = None, author_handle: str = None, author_url: str = None, media_url: str = None, dedupe_key=None, on_complete=None):
        await self.queue.put((priority, next(self._counter), {"url": url, "profile_id": profile_id, "text": text, "title": title, "platform": platform, "author_handle": author_handle, "author_url": author_url, "media_url": media_url, "dedupe_key": dedupe_key, "on_complete": on_complete}))

    def start(self, ml_classifier):
        if self.is_running:
            return
        self.is_running = True
        self.task = asyncio.create_task(self._process_loop(ml_classifier))
        print("URL Queue processor started.")

    def stop(self):
        self.is_running = False
        if self.task:
            self.task.cancel()
            self.task = None
        self.queue = asyncio.PriorityQueue()
        print("URL Queue processor stopped and cleared.")

    def clear(self):
        self.queue = asyncio.PriorityQueue()
        print("URL Queue cleared manually.")

    async def _process_loop(self, ml_classifier):
        while self.is_running:
            dedupe_key = None
            on_complete = None
            try:
                if self.queue.empty():
                    await asyncio.sleep(1)
                    continue

                _, _, item = await self.queue.get()
                url = item["url"]
                profile_id = item["profile_id"]
                text = item.get("text")
                title = item.get("title")
                platform = item.get("platform")
                author_handle = item.get("author_handle")
                author_url = item.get("author_url")
                media_url = item.get("media_url") or url
                dedupe_key = item.get("dedupe_key")
                on_complete = item.get("on_complete")
                
                print(f"Queue processing URL: {url} with profile {profile_id}")
                
                # Run ML analysis in thread
                try:
                    safe_media_url = validate_public_url(media_url) if media_url else None
                    result = await asyncio.to_thread(ml_classifier.classify_content, text=text, image=None, url=safe_media_url)
                except (URLValidationError, Exception) as exc:
                    print(f"Media analysis unavailable for {media_url}: {exc}")
                    result = await asyncio.to_thread(ml_classifier.classify_content, text=text, image=None, url=None)
                
                # If analysis returns no transcription/scores (e.g. video download failed)
                if not result.get("transcription") and sum(result.get("scores", {}).values()) < 0.1 and not text:
                    if not title and url:
                        try:
                            req_url = url if url.startswith("http") else "https://" + url
                            req_url = validate_public_url(req_url)
                            # Try to fetch title using requests as a last resort
                            resp = await asyncio.to_thread(requests.get, req_url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=5)
                            soup = BeautifulSoup(resp.text, 'html.parser')
                            title = soup.title.string if soup.title else "Unknown Video"
                            print(f"Extracted title from URL: {title}")
                        except Exception as e:
                            print(f"Failed to fetch title for {url}: {e}")
                            title = "Unknown Video"
                            
                    if title:
                        print(f"Video analysis failed, falling back to title: {title}")
                        fallback_result = await asyncio.to_thread(ml_classifier.classify_content, text=title, image=None, url=None)
                        result["scores"] = fallback_result.get("scores", {})
                        result["transcription"] = f"[TITLE ANALYSIS]: {title}"
                
                # Save to DB
                await asyncio.to_thread(self._save_to_db, url, profile_id, result, text, title, platform, author_handle, author_url)
                if on_complete:
                    on_complete(dedupe_key)
                
                self.last_processed_url = url
                self.queue.task_done()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Queue error: {e}")
                traceback.print_exc()
                if on_complete:
                    on_complete(dedupe_key)
            
            # Delay between items
            await asyncio.sleep(1)

    def _save_to_db(self, url, profile_id, result, text=None, title=None, platform=None, author_handle=None, author_url=None):
        db = SessionLocal()
        try:
            profile = db.query(Profile).filter(Profile.id == profile_id).first()
            if not profile:
                return

            scores = result.get("scores", {})
            transcription = result.get("transcription", "")
            
            from backend.app.scoring import evaluate
            from backend.app.identifiers import extract
            
            evaluation = evaluate(scores, profile.thresholds)
            decision = evaluation["decision"]
            explanation = evaluation["explanation"]
            risk_score = evaluation["risk_score"]

            content_type = "video_url" if url and not text else "text"
            preview_url = url
            preview_string = f"{title} ||| {preview_url}" if title and preview_url else (preview_url if preview_url else (text[:100] if text else "Unknown"))
            
            all_text = (text or "") + "\n" + transcription
            identifiers = extract(all_text)
            
            log_entry = ContentLog(
                content_type=content_type,
                content_preview=preview_string,
                scores=scores,
                profile_id=profile.id,
                decision=decision,
                explanation=explanation,
                risk_score=risk_score,
                source_id=canonicalize_url(url) if url else None,
                source_platform=platform or ("youtube" if url and "youtu" in url else None),
                author_handle=author_handle,
                author_url=author_url,
                caption_text=text,
                transcription_text=transcription,
                extracted_identifiers=identifiers
            )
            
            db.add(log_entry)
            db.commit()
            print(f"Queue saved log for {url}: {decision}")
        except Exception as e:
            print(f"Queue DB error: {e}")
        finally:
            db.close()

url_queue_instance = URLQueue()
