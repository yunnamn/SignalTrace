import requests
import re
from bs4 import BeautifulSoup
from .base import BaseConnector

class TelegramConnector(BaseConnector):
    def fetch_account(self, target: str, limit: int = 15) -> list[dict]:
        target = target.lstrip("@")
        url = f"https://t.me/s/{target}"
        try:
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code != 200:
                return []
                
            soup = BeautifulSoup(response.text, 'html.parser')
            messages = soup.find_all('div', class_='tgme_widget_message_wrap')
            
            results = []
            for msg in messages[-limit:]:
                text_div = msg.find('div', class_='tgme_widget_message_text')
                link_a = msg.find('a', class_='tgme_widget_message_date')
                media_url = None
                video = msg.find("video")
                if video and video.get("src"):
                    media_url = video.get("src")
                if not media_url:
                    photo = msg.find("a", class_="tgme_widget_message_photo_wrap")
                    style = photo.get("style", "") if photo else ""
                    match = re.search(r"url\('([^']+)'\)", style)
                    if match:
                        media_url = match.group(1)
                
                if text_div and link_a:
                    text = text_div.get_text(separator=' ')
                    post_url = link_a.get('href')
                    if (text or media_url) and post_url:
                        results.append({
                            "platform": "telegram",
                            "author_handle": "@" + target,
                            "author_url": f"https://t.me/{target}",
                            "caption_text": text,
                            "media_url": media_url,
                            "post_url": post_url
                        })
            return results
        except Exception as e:
            print(f"Telegram parse error: {e}")
            return []
            
    def fetch_feed(self, target: str) -> list[dict]:
        return self.fetch_account(target, limit=3)
