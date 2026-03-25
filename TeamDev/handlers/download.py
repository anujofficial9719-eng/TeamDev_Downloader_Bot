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

import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, Message, CallbackQuery

from config import DAILY_DOWNLOAD_LIMIT
from TeamDev.core.database import (
    get_or_create_user, get_user, get_user_lang,
    count_downloads_today, log_download,
    get_active_ad, get_setting,
)
from TeamDev.utils.i18n import t
from TeamDev.utils.helpers import detect_platform, format_duration, PLATFORM_META
from TeamDev.platforms.YouTube    import fetch_youtube
from TeamDev.platforms.multi_down import fetch_multi
from TeamDev.platforms.Terabox    import fetch_terabox
from TeamDev.platforms.Vimeo      import fetch_vimeo
from TeamDev.platforms.Spotify    import fetch_spotify

import os
import re
import requests as _requests

_MULTI_PLATFORMS   = {"instagram", "facebook", "pinterest", "twitter", "tiktok", "soundcloud"}
_TERABOX_PLATFORMS = {"terabox"}
_VIMEO_PLATFORMS   = {"vimeo"}
_SPOTIFY_PLATFORMS = {"spotify"}

_PLATFORM_ROWS = [
    ["youtube"],
    ["instagram", "facebook"],
    ["pinterest", "twitter"],
    ["tiktok",    "soundcloud"],
    ["terabox",   "vimeo"],
    ["spotify"],
]

_WAITING_URL: dict[int, str] = {}


def _send_ad(bot: telebot.TeleBot, chat_id: int, lang: str):
    ad = get_active_ad()
    if not ad:
        return
    label = t(lang, "ad_label")
    try:
        kb = None
        if ad.get("button_text") and ad.get("button_url"):
            kb = InlineKeyboardMarkup()
            kb.add(InlineKeyboardButton(ad["button_text"], url=ad["button_url"]))
        if ad.get("ad_type") == "photo" and ad.get("photo_url"):
            caption = f"{label}\n\n{ad.get('content','')}" if ad.get("content") else label
            bot.send_photo(chat_id, ad["photo_url"], caption=caption, reply_markup=kb, parse_mode="HTML")
        else:
            bot.send_message(chat_id, f"{label}\n\n{ad.get('content','')}", reply_markup=kb, parse_mode="HTML")
    except Exception:
        pass


def _check_limit(uid: int, lang: str) -> tuple[bool, int]:
    user  = get_user(uid)
    if not user:
        return True, 0
    if user.get("is_premium"):
        return True, 0
    limit     = int(get_setting("daily_limit", str(DAILY_DOWNLOAD_LIMIT)))
    used      = count_downloads_today(uid)
    effective = limit + user.get("referral_points", 0)
    return used < effective, effective


def _build_platform_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup()
    for row in _PLATFORM_ROWS:
        btns = []
        for p in row:
            meta = PLATFORM_META.get(p, {"label": p.title()})
            btns.append(InlineKeyboardButton(
                f"[ {meta['label']} ]",
                callback_data=f"pick_platform|{p}"
            ))
        kb.row(*btns)
    return kb


def _build_result_caption(lang: str, platform: str, result: dict) -> str:
    title        = result.get("title") or result.get("author") or "Media"
    author       = result.get("author", "")
    quality      = result.get("quality", "")
    fmt          = result.get("format", "")
    duration_str = format_duration(result.get("duration", 0))
    size_mb      = result.get("filesize_mb", 0.0)
    size_str     = result.get("filesize_str", "")

    author_line   = f"◇ By: `{author}`\n"   if (author and author != title) else ""
    quality_line  = f"◇ Quality: `{quality}`\n" if quality else (f"◇ Format: `{fmt}`\n" if fmt else "")
    duration_line = f"◇ Duration: `{duration_str}`\n" if duration_str not in ("00:00", "0:00") else ""
    size_line     = f"◇ Size: `{size_str}`\n" if size_str else (f"◇ Size: `{size_mb:.2f} MB`\n" if size_mb > 0 else "")

    return t(
        lang, "download_ready",
        title=title,
        author_line=author_line,
        quality_line=quality_line,
        duration_line=duration_line,
        size_line=size_line,
    )


def _safe_filename(title: str) -> str:
    """Sanitise a track title for use as a filename."""
    name = re.sub(r'[^\w\s\-]', '', title).strip()
    name = re.sub(r'\s+', '_', name)
    return name[:60] if name else "track"


def _unique_path(base: str) -> str:
    """Return a unique file path, appending _1/_2/... if needed."""
    path = f"{base}.mp3"
    counter = 1
    while os.path.exists(path):
        path = f"{base}_{counter}.mp3"
        counter += 1
    return path


def _do_spotify(bot: telebot.TeleBot, chat_id: int, uid: int, lang: str,
                url: str, wait_msg_id: int | None = None):
    """Fetch Spotify track, download MP3, send to user, delete file."""

    # Edit waiting message
    def _edit(text: str):
        if wait_msg_id:
            try:
                bot.edit_message_text(text, chat_id, wait_msg_id, parse_mode="HTML")
                return
            except Exception:
                pass
        bot.send_message(chat_id, text, parse_mode="HTML")

    result = fetch_spotify(url)

    if not result.get("success"):
        err = result.get("error", "unknown")
        if err == "spotify_only_tracks_supported":
            _edit(t(lang, "spotify_only_tracks"))
        else:
            _edit(t(lang, "error_generic", err=err))
        return

    title      = result.get("title", "TEAM_X_OG")
    author     = result.get("author", "")
    thumbnail  = result.get("thumbnail", "")
    duration   = result.get("duration", 0)
    dl_url     = result.get("download_url", "")

    # Update waiting message → sending status
    _edit(t(lang, "spotify_sending"))

    # Build a safe local filename like @TEAM_X_OG.mp3 (unique)
    safe_base  = _safe_filename(title) or "TEAM_X_OG"
    file_path  = _unique_path(f"@{safe_base}")

    try:
        # Stream download
        r = _requests.get(dl_url, stream=True, timeout=60)
        r.raise_for_status()
        with open(file_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=4096):
                if chunk:
                    f.write(chunk)

        # Build caption
        author_line   = f"◇ By: <code>{author}</code>\n" if author else ""
        duration_line = f"◇ Duration: <code>{format_duration(duration)}</code>\n" if duration else ""
        caption = (
            f"◆ <b>{title}</b>\n"
            f"━━━━━━━━━━━━\n"
            f"{author_line}"
            f"{duration_line}"
            f"◇ Format: <code>MP3 · 320kbps</code>\n"
            f"━━━━━━━━━━━━\n"
            f"<i>Powered by TeamDev</i>"
        )

        # Delete the waiting/status message
        if wait_msg_id:
            try:
                bot.delete_message(chat_id, wait_msg_id)
            except Exception:
                pass

        # Send thumbnail + audio
        if thumbnail:
            try:
                bot.send_photo(chat_id, thumbnail, caption=caption, parse_mode="HTML")
            except Exception:
                pass

        with open(file_path, "rb") as audio_f:
            bot.send_audio(
                chat_id,
                audio_f,
                title=title,
                performer=author,
                caption=caption,
                parse_mode="HTML",
            )

        log_download(uid, "spotify", url)

        user = get_user(uid)
        if user and not user.get("is_premium"):
            limit     = int(get_setting("daily_limit", str(DAILY_DOWNLOAD_LIMIT)))
            used_now  = count_downloads_today(uid)
            effective = limit + user.get("referral_points", 0)
            left      = max(0, effective - used_now)
            bot.send_message(chat_id, t(lang, "downloads_left", left=left), parse_mode="HTML")
            _send_ad(bot, chat_id, lang)

    except _requests.exceptions.Timeout:
        _edit(t(lang, "error_generic", err="timeout"))
    except _requests.exceptions.RequestException as exc:
        _edit(t(lang, "error_generic", err=str(exc)))
    except Exception as exc:
        _edit(t(lang, "error_generic", err=str(exc)))
    finally:
        # Always delete the local file
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception:
            pass


def _do_download(bot: telebot.TeleBot, chat_id: int, uid: int, lang: str,
                 platform: str, url: str, wait_msg_id: int | None = None):

    if platform in _SPOTIFY_PLATFORMS:
        _do_spotify(bot, chat_id, uid, lang, url, wait_msg_id)
        return

    if platform == "youtube":
        result = fetch_youtube(url, fmt="mp4")
    elif platform in _MULTI_PLATFORMS:
        result = fetch_multi(url)
    elif platform in _TERABOX_PLATFORMS:
        result = fetch_terabox(url)
    elif platform in _VIMEO_PLATFORMS:
        result = fetch_vimeo(url)
    else:
        result = {"success": False, "error": f"{platform}_not_supported"}

    if not result or not result.get("success"):
        err  = result.get("error", "") if result else "unknown"
        text = t(lang, "error_generic", err=err)
        if wait_msg_id:
            try:
                bot.edit_message_text(text, chat_id, wait_msg_id, parse_mode="HTML")
                return
            except Exception:
                pass
        bot.send_message(chat_id, text, parse_mode="HTML")
        return

    log_download(uid, platform, url)

    caption   = _build_result_caption(lang, platform, result)
    dl_url    = result.get("download_url", "")
    thumbnail = result.get("thumbnail", "")

    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton(t(lang, "btn_download_file"), url=dl_url))

    if wait_msg_id:
        try:
            bot.delete_message(chat_id, wait_msg_id)
        except Exception:
            pass

    if thumbnail:
        try:
            bot.send_photo(chat_id, thumbnail, caption=caption, reply_markup=kb, parse_mode="HTML")
        except Exception:
            bot.send_message(chat_id, caption, reply_markup=kb, parse_mode="HTML")
    else:
        bot.send_message(chat_id, caption, reply_markup=kb, parse_mode="HTML")

    user = get_user(uid)
    if user and not user.get("is_premium"):
        limit     = int(get_setting("daily_limit", str(DAILY_DOWNLOAD_LIMIT)))
        used_now  = count_downloads_today(uid)
        effective = limit + user.get("referral_points", 0)
        left      = max(0, effective - used_now)
        bot.send_message(chat_id, t(lang, "downloads_left", left=left), parse_mode="HTML")
        _send_ad(bot, chat_id, lang)


def register_download_handlers(bot: telebot.TeleBot):

    @bot.callback_query_handler(func=lambda c: c.data == "cb_download_now")
    def cb_download_now(call: CallbackQuery):
        lang = get_user_lang(call.from_user.id)
        bot.answer_callback_query(call.id)
        bot.send_message(
            call.message.chat.id,
            t(lang, "choose_platform"),
            reply_markup=_build_platform_kb(),
            parse_mode="HTML",
        )

    @bot.callback_query_handler(func=lambda c: c.data and c.data.startswith("pick_platform|"))
    def cb_pick_platform(call: CallbackQuery):
        parts = call.data.split("|", 1)
        if len(parts) != 2:
            bot.answer_callback_query(call.id)
            return
        platform = parts[1]
        uid      = call.from_user.id
        lang     = get_user_lang(uid)
        meta     = PLATFORM_META.get(platform, {"label": platform.title()})

        bot.answer_callback_query(call.id)
        _WAITING_URL[uid] = platform

        try:
            bot.edit_message_text(
                t(lang, "platform_selected", platform=meta["label"]),
                call.message.chat.id,
                call.message.message_id,
                parse_mode="HTML",
            )
        except Exception:
            bot.send_message(
                call.message.chat.id,
                t(lang, "platform_selected", platform=meta["label"]),
                parse_mode="HTML",
            )

    @bot.message_handler(
        func=lambda m: m.text and (
            m.text.startswith("http://") or m.text.startswith("https://")
        )
    )
    def handle_url(msg: Message):
        uid  = msg.from_user.id
        url  = msg.text.strip()
        lang = get_user_lang(uid)

        user = get_or_create_user(uid, msg.from_user.first_name or "", msg.from_user.username or "")
        if user.get("is_banned"):
            bot.send_message(msg.chat.id, t(lang, "banned_msg"), parse_mode="HTML")
            return

        allowed, effective = _check_limit(uid, lang)
        if not allowed:
            bot.send_message(msg.chat.id, t(lang, "limit_reached", limit=effective), parse_mode="HTML")
            return

        if uid in _WAITING_URL:
            platform = _WAITING_URL.pop(uid)
            meta     = PLATFORM_META.get(platform, {"label": platform.title()})
            wait_msg = bot.send_message(
                msg.chat.id,
                t(lang, "fetching", platform=meta["label"]),
                parse_mode="HTML",
            )
            _do_download(bot, msg.chat.id, uid, lang, platform, url, wait_msg.message_id)
            return

        platform = detect_platform(url)
        if platform is None:
            bot.send_message(msg.chat.id, t(lang, "invalid_url"), parse_mode="HTML")
            return

        meta     = PLATFORM_META.get(platform, {"label": platform.title()})
        wait_msg = bot.send_message(
            msg.chat.id,
            t(lang, "auto_detected", platform=meta["label"]),
            parse_mode="HTML",
        )
        _do_download(bot, msg.chat.id, uid, lang, platform, url, wait_msg.message_id)
