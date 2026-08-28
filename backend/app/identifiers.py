import re
from backend.app.url_utils import canonicalize_url

def extract(text: str) -> list[dict]:
    if not text:
        return []
        
    identifiers = []
    
    # 1. Links
    link_pattern = re.compile(r'https?://[^\s<>"]+|www\.[^\s<>"]+')
    for match in link_pattern.finditer(text):
        val = match.group(0).lower()
        identifiers.append({"type": "link", "value": val})
        try:
            identifiers.append({"type": "canonical_url", "value": canonicalize_url(val)})
        except ValueError:
            pass
        
    # 2. Mentions
    mention_pattern = re.compile(r'@[A-Za-z0-9_.]+')
    for match in mention_pattern.finditer(text):
        identifiers.append({"type": "mention", "value": match.group(0)})
        
    # 3. Promocodes (words after promo/код/промокод that are ALL CAPS 4-12 chars)
    promo_pattern = re.compile(r'(?i)(?:promo|код|промокод)\s*[:\-]?\s*([A-Z0-9]{4,12})\b')
    for match in promo_pattern.finditer(text):
        identifiers.append({"type": "promo", "value": match.group(1)})
        
    # 4. Crypto wallets
    btc_pattern = re.compile(r'\b(1[a-km-zA-HJ-NP-Z1-9]{25,34}|3[a-km-zA-HJ-NP-Z1-9]{25,34}|bc1[a-z0-9]{39,59})\b')
    eth_pattern = re.compile(r'\b(0x[a-fA-F0-9]{40})\b')
    trc_pattern = re.compile(r'\b(T[a-zA-Z1-9]{33})\b')
    
    for match in btc_pattern.finditer(text):
        identifiers.append({"type": "wallet", "value": match.group(1)})
    for match in eth_pattern.finditer(text):
        identifiers.append({"type": "wallet", "value": match.group(1)})
    for match in trc_pattern.finditer(text):
        identifiers.append({"type": "wallet", "value": match.group(1)})
        
    # 5. Phones
    phone_pattern = re.compile(r'\+?[78][\s\-]?\(?\d{3}\)?[\s\-]?\d{3}[\s\-]?\d{2}[\s\-]?\d{2}')
    for match in phone_pattern.finditer(text):
        val = re.sub(r'\D', '', match.group(0))
        if val.startswith('8') and len(val) == 11:
            val = '7' + val[1:]
        if len(val) == 11:
            identifiers.append({"type": "phone", "value": "+" + val})
        
    return identifiers
