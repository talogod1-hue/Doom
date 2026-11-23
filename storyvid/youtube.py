"""Upload to YouTube with the YouTube Data API v3 (free quota). Stdlib HTTP only.

Needs three environment variables from a Google Cloud OAuth client
(see README): YOUTUBE_CLIENT_ID, YOUTUBE_CLIENT_SECRET, YOUTUBE_REFRESH_TOKEN.
"""
from __future__ import annotations

import json
import os
import urllib.parse
import urllib.request
from pathlib import Path

TOKEN_URL = "https://oauth2.googleapis.com/token"
UPLOAD_URL = "https://www.googleapis.com/upload/youtube/v3/videos?uploadType=resumable&part=snippet,status"
CATEGORY_GAMING = "20"


def access_token(client_id: str, client_secret: str, refresh_token: str) -> str:
    body = urllib.parse.urlencode({
        "client_id": client_id,
        "client_secret": client_secret,
        "refresh_token": refresh_token,
        "grant_type": "refresh_token",
    }).encode()
    req = urllib.request.Request(TOKEN_URL, data=body, method="POST")
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read())["access_token"]


def upload_video(video: Path, title: str, description: str, token: str,
                 privacy: str = "private", tags: list[str] | None = None) -> str:
    """Resumable upload. Returns the new YouTube video id."""
    metadata = {
        "snippet": {
            "title": title[:100],
            "description": description[:5000],
            "tags": tags or ["Minecraft", "Minecraft story", "gaming"],
            "categoryId": CATEGORY_GAMING,
        },
        "status": {"privacyStatus": privacy, "selfDeclaredMadeForKids": False},
    }
    init = urllib.request.Request(
        UPLOAD_URL, data=json.dumps(metadata).encode(), method="POST",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json; charset=UTF-8",
            "X-Upload-Content-Type": "video/mp4",
            "X-Upload-Content-Length": str(video.stat().st_size),
        },
    )
    with urllib.request.urlopen(init, timeout=60) as resp:
        upload_url = resp.headers["Location"]

    data = video.read_bytes()
    put = urllib.request.Request(
        upload_url, data=data, method="PUT",
        headers={"Content-Type": "video/mp4", "Content-Length": str(len(data))},
    )
    with urllib.request.urlopen(put, timeout=600) as resp:
        return json.loads(resp.read())["id"]


def upload_from_env(video: Path, title: str, description: str) -> str:
    missing = [k for k in ("YOUTUBE_CLIENT_ID", "YOUTUBE_CLIENT_SECRET", "YOUTUBE_REFRESH_TOKEN")
               if not os.environ.get(k)]
    if missing:
        raise RuntimeError("Missing environment variables: " + ", ".join(missing))
    token = access_token(os.environ["YOUTUBE_CLIENT_ID"], os.environ["YOUTUBE_CLIENT_SECRET"],
                         os.environ["YOUTUBE_REFRESH_TOKEN"])
    privacy = os.environ.get("YOUTUBE_PRIVACY", "private")
    return upload_video(video, title, description, token, privacy=privacy)
