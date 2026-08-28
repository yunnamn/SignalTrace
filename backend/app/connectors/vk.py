import os
import requests
from .base import BaseConnector

class VKConnector(BaseConnector):
    def fetch_account(self, target: str, limit: int = 15) -> list[dict]:
        token = os.environ.get("VK_API_TOKEN")
        if not token:
            print("VK_API_TOKEN not set, skipping VK")
            return []
            
        url = "https://api.vk.com/method/wall.get"
        
        if target.startswith("vk.com/"):
            target = target.split("/")[-1]
        elif target.startswith("https://vk.com/"):
            target = target.split("/")[-1]
            
        params = {
            "count": limit,
            "access_token": token,
            "v": "5.199"
        }
        
        if target.lstrip("-").isdigit():
            params["owner_id"] = target
        else:
            params["domain"] = target
            
        try:
            resp = requests.get(url, params=params, timeout=10).json()
            if "error" in resp:
                print(f"VK API error: {resp['error']}")
                return []
                
            items = resp.get("response", {}).get("items", [])
            results = []
            for item in items:
                text = item.get("text", "")
                owner_id = item.get("owner_id")
                post_id = item.get("id")
                post_url = f"https://vk.com/wall{owner_id}_{post_id}"
                
                media_url = None
                if "attachments" in item:
                    for att in item["attachments"]:
                        if att["type"] == "video":
                            video = att["video"]
                            media_url = f"https://vk.com/video{video['owner_id']}_{video['id']}"
                            break
                            
                results.append({
                    "platform": "vk",
                    "author_handle": target,
                    "author_url": f"https://vk.com/{target}",
                    "caption_text": text,
                    "media_url": media_url,
                    "post_url": post_url
                })
            return results
        except Exception as e:
            print(f"VK fetch error: {e}")
            return []
            
    def fetch_feed(self, target: str) -> list[dict]:
        return self.fetch_account(target, limit=3)
