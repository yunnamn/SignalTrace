import ipaddress
import socket
from urllib.parse import parse_qs, urlparse


ALLOWED_SCHEMES = {"http", "https"}
MAX_URL_LENGTH = 2048


class URLValidationError(ValueError):
    pass


def _ensure_url(raw_url: str) -> str:
    if not raw_url or not raw_url.strip():
        raise URLValidationError("URL is required")
    url = raw_url.strip()
    if len(url) > MAX_URL_LENGTH:
        raise URLValidationError("URL is too long")
    if "://" not in url:
        url = "https://" + url
    return url


def _host_is_public(hostname: str) -> bool:
    if not hostname:
        return False

    host = hostname.rstrip(".").lower()
    if host == "localhost" or host.endswith(".localhost"):
        return False

    try:
        addresses = {info[4][0] for info in socket.getaddrinfo(host, None)}
    except socket.gaierror as exc:
        raise URLValidationError("URL host could not be resolved") from exc

    for address in addresses:
        ip = ipaddress.ip_address(address)
        if (
            ip.is_private
            or ip.is_loopback
            or ip.is_link_local
            or ip.is_multicast
            or ip.is_reserved
            or ip.is_unspecified
        ):
            return False
    return True


def validate_public_url(raw_url: str) -> str:
    url = _ensure_url(raw_url)
    parsed = urlparse(url)
    if parsed.scheme.lower() not in ALLOWED_SCHEMES:
        raise URLValidationError("Only http and https URLs are supported")
    if not parsed.hostname:
        raise URLValidationError("URL host is required")
    if not _host_is_public(parsed.hostname):
        raise URLValidationError("Local, private, and internal hosts are not allowed")
    return url


def canonicalize_url(raw_url: str) -> str:
    url = _ensure_url(raw_url)
    parsed = urlparse(url)
    scheme = parsed.scheme.lower()
    host = (parsed.hostname or "").lower().removeprefix("www.")
    query = parse_qs(parsed.query)
    path = parsed.path.rstrip("/")

    if host in {"youtube.com", "m.youtube.com", "youtu.be", "youtube-nocookie.com"}:
        video_id = None
        if host == "youtu.be":
            video_id = path.lstrip("/").split("/")[0]
        elif path == "/watch":
            video_id = (query.get("v") or [None])[0]
        elif path.startswith("/shorts/") or path.startswith("/embed/"):
            video_id = path.split("/")[2] if len(path.split("/")) > 2 else None
        if video_id:
            return f"youtube:{video_id}"

    if host == "t.me":
        parts = [p for p in path.split("/") if p]
        if len(parts) >= 2:
            return f"telegram:{parts[0].lower()}:{parts[1]}"

    if host == "vk.com":
        parts = [p for p in path.split("/") if p]
        if parts:
            return f"vk:{parts[0].lower()}"

    normalized_path = path.lower() or "/"
    return f"{scheme}://{host}{normalized_path}"
