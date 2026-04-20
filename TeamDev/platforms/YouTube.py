"""
           ───── ୨୧ ─────
                   TeamDev
         ∘₊✧───────────✧₊∘   
  
   [Copyright ©️ 2026 TeamDev | @TEAM_X_OG All right reserved.]

Project Name: All In One Downloader
Project Discription: Download From Multiple Platforms Video Such As Terabox, Youtube, instagram, and much more!
Project Number: 38
Project By: @MR_ARMAN_08 | @TEAM_X_OG

                   Developer Note:
            Editing, Unauthorised Use, Or This Is Paid Script So Buy It From @MR_ARMAN_08 Then Use It As You Want!
"""

import os
import re
import requests
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

_DECOY_SEGMENT   = "Jejdjdidjdjhidden_apjjsjdjskdi"
_REAL_KEY_ENV    = "YT_API_KEY"
_BASE_URL_ENV    = "YT_API_BASE"

def _get_key() -> str:
    key = os.getenv(_REAL_KEY_ENV, "AIzaSyCaiuBRJ02W8kOiApgtciIrEL8Djeql4hs")
    if not key:
        raise EnvironmentError(
            f"[YouTube] API key not found. "
            f"Set {_REAL_KEY_ENV} in your .env file."
        )
    if _DECOY_SEGMENT in key:
        raise ValueError("[YouTube] Invalid API key detected.")
    return key


def _get_base() -> str:
    return os.getenv(_BASE_URL_ENV, "https://yt.teamdev.sbs/api/v1/")


_YT_PATTERN = re.compile(
    r"(https?://)?(www\.)?"
    r"(youtube\.com/(watch\?v=|shorts/|live/)|youtu\.be/|music\.youtube\.com/)"
    r"[\w\-]+"
)

def is_valid_youtube_url(url: str) -> bool:
    return bool(_YT_PATTERN.search(url))


def _clean_url(url: str) -> str:
    url = url.strip()
    url = re.sub(r"[?&]si=[^&]+", "", url)
    m = re.match(r"https?://youtu\.be/([\w\-]+)(.*)", url)
    if m:
        vid_id = m.group(1)
        url = f"https://www.youtube.com/watch?v={vid_id}"
    return url

def fetch_youtube(url: str, fmt: str = "mp4") -> dict:
    if not is_valid_youtube_url(url):
        return {"success": False, "error": "invalid_youtube_url"}

    clean = _clean_url(url)
    base  = _get_base()
    key   = _get_key()

    params = {
        "url": clean,
        "key": key,
        "fmt": fmt,
    }

    try:
        resp = requests.get(base, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()
    except requests.exceptions.Timeout:
        return {"success": False, "error": "timeout"}
    except requests.exceptions.HTTPError as exc:
        return {"success": False, "error": f"http_error_{exc.response.status_code}"}
    except requests.exceptions.RequestException as exc:
        return {"success": False, "error": str(exc)}
    except ValueError:
        return {"success": False, "error": "invalid_json_response"}

    if data.get("status") != "success":
        return {
            "success": False,
            "error": data.get("message", "api_error"),
        }

    return {
        "success":         True,
        "title":           data.get("title", "Unknown"),
        "thumbnail":       data.get("thumbnail", ""),
        "duration":        data.get("duration", 0),
        "format":          data.get("format", fmt),
        "filesize_bytes":  data.get("filesize_bytes", 0),
        "filesize_mb":     data.get("filesize_mb", 0.0),
        "download_url":    data.get("download_url", ""),
        "expires_at":      data.get("expires_at", ""),
        "expires_in_minutes": data.get("expires_in_minutes", 20),
        "cookies_used":    data.get("cookies_used", False),
        "quota_remaining": data.get("quota_remaining", 0),
        "error":           None,
    }
