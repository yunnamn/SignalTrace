import yt_dlp
from .base import BaseConnector

class YouTubeConnector(BaseConnector):
    def fetch_account(self, target: str, limit: int = 15) -> list[dict]:
        # Support ytsearch queries (e.g. "ytsearch5:казино")
        if target.startswith("ytsearch"):
            return self._fetch_search(target, limit)
            
        if not target.startswith("@") and not target.startswith("UC"):
            target = "@" + target
            
        url = f"https://www.youtube.com/{target}/videos"
        
        ydl_opts = {
            'quiet': True,
            'extract_flat': True,
            'playlist_end': limit,
            'no_warnings': True,
        }
        
        results = []
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                if not info or 'entries' not in info:
                    return []
                    
                for entry in info['entries']:
                    if not entry:
                        continue
                    video_url = entry.get('url') or entry.get('webpage_url')
                    if video_url and not video_url.startswith("http"):
                        video_url = f"https://www.youtube.com/watch?v={video_url}"
                        
                    title = entry.get('title', '')
                    channel = entry.get('channel', target)
                    channel_url = entry.get('channel_url', f"https://www.youtube.com/{target}")
                    results.append({
                        "platform": "youtube",
                        "author_handle": channel if channel else target,
                        "author_url": channel_url if channel_url else f"https://www.youtube.com/{target}",
                        "caption_text": title,
                        "media_url": None,
                        "post_url": video_url
                    })
        except Exception as e:
            print(f"YouTube parse error for {target}: {e}")
            
        return results
    
    def _fetch_search(self, query: str, limit: int = 5) -> list[dict]:
        """Search YouTube with ytsearch queries like 'ytsearch5:казино'"""
        ydl_opts = {
            'quiet': True,
            'extract_flat': True,
            'playlist_end': limit,
            'no_warnings': True,
        }
        
        results = []
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(query, download=False)
                if not info:
                    return []
                    
                entries = info.get('entries', [info]) if 'entries' in info else [info]
                for entry in entries:
                    if not entry:
                        continue
                    video_url = entry.get('url') or entry.get('webpage_url')
                    if video_url and not video_url.startswith("http"):
                        video_url = f"https://www.youtube.com/watch?v={video_url}"
                    
                    title = entry.get('title', '')
                    channel = entry.get('channel', 'Unknown')
                    channel_url = entry.get('channel_url', '')
                    
                    results.append({
                        "platform": "youtube",
                        "author_handle": channel,
                        "author_url": channel_url or "",
                        "caption_text": title,
                        "media_url": None,
                        "post_url": video_url
                    })
        except Exception as e:
            print(f"YouTube search error for {query}: {e}")
            
        return results
        
    def fetch_feed(self, target: str) -> list[dict]:
        return self.fetch_account(target, limit=3)
