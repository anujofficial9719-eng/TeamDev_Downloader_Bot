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
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, Message

from config import TEAM_NAME, DEVELOPER_NAME, BOT_USERNAME, FORCE_JOIN_CHANNEL, FORCE_JOIN_ENABLED, DAILY_DOWNLOAD_LIMIT
from TeamDev.core.database import (
    get_or_create_user, get_user, update_user,
    get_user_lang, get_setting, set_setting,
)
from TeamDev.utils.i18n import t, SUPPORTED_LANGUAGES
from TeamDev.utils.helpers import build_referral_link


def _check_force_join(bot: telebot.TeleBot, user_id: int) -> bool:
    fj_enabled = get_setting("force_join_enabled", str(FORCE_JOIN_ENABLED)).lower() == "true"
    fj_channel = get_setting("force_join_channel", FORCE_JOIN_CHANNEL)
    if not fj_enabled or not fj_channel:
        return True
    try:
        member = bot.get_chat_member(fj_channel, user_id)
        return member.status not in ("left", "kicked")
    except Exception:
        return True


def _start_kb(lang: str) -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton(t(lang, "btn_download_now"), callback_data="cb_download_now"))
    kb.row(
        InlineKeyboardButton(t(lang, "btn_help"),    callback_data="cb_help"),
        InlineKeyboardButton(t(lang, "btn_premium"), callback_data="cb_premium"),
    )
    kb.row(
        InlineKeyboardButton(t(lang, "btn_referral"),  callback_data="cb_referral"),
        InlineKeyboardButton(t(lang, "btn_language"),  callback_data="cb_language"),
    )
    return kb


def register_start_handlers(bot: telebot.TeleBot):

    @bot.message_handler(commands=["start"])
    def cmd_start(msg: Message):
        uid   = msg.from_user.id
        fname = msg.from_user.first_name or ""
        uname = msg.from_user.username  or ""

        parts = msg.text.split()
        if len(parts) > 1 and parts[1].startswith("ref_"):
            try:
                ref_id = int(parts[1].replace("ref_", ""))
                if ref_id != uid:
                    existing = get_user(uid)
                    if not existing or not existing.get("referred_by"):
                        referrer = get_user(ref_id)
                        if referrer:
                            from TeamDev.core.database import _users
                            _users().update_one(
                                {"telegram_id": ref_id},
                                {"$inc": {"referral_points": 1}},
                            )
                            update_user(uid, referred_by=ref_id)
            except (ValueError, AttributeError):
                pass

        user = get_or_create_user(uid, fname, uname)
        lang = user.get("language", "en")

        if user.get("is_banned"):
            bot.send_message(uid, t(lang, "banned_msg"), parse_mode="HTML")
            return

        if not _check_force_join(bot, uid):
            fj_channel = get_setting("force_join_channel", FORCE_JOIN_CHANNEL)
            kb = InlineKeyboardMarkup()
            kb.add(InlineKeyboardButton(
                "▸ Join Channel",
                url=f"https://t.me/{fj_channel.lstrip('@')}"
            ))
            bot.send_message(uid, t(lang, "force_join"), reply_markup=kb, parse_mode="HTML")
            return

        bot_info = bot.get_me()
        caption  = t(
            lang, "start_caption",
            first_name=fname,
            bot_name=bot_info.first_name,
            team_name=TEAM_NAME,
            dev_name=DEVELOPER_NAME,
        )

        start_photo = get_setting("start_photo", os.getenv("START_PHOTO", ""))
        kb = _start_kb(lang)

        if start_photo:
            try:
                bot.send_photo(uid, start_photo, caption=caption, reply_markup=kb, parse_mode="HTML")
                return
            except Exception:
                pass
        bot.send_message(uid, caption, reply_markup=kb, parse_mode="HTML")

    @bot.message_handler(commands=["language", "lang"])
    def cmd_language(msg: Message):
        lang = get_user_lang(msg.from_user.id)
        _show_lang_menu(bot, msg.chat.id, lang)

    @bot.callback_query_handler(func=lambda c: c.data == "cb_language")
    def cb_language(call):
        lang = get_user_lang(call.from_user.id)
        bot.answer_callback_query(call.id)
        _show_lang_menu(bot, call.message.chat.id, lang)

    def _show_lang_menu(bot, chat_id: int, lang: str):
        kb = InlineKeyboardMarkup(row_width=2)
        btns = [
            InlineKeyboardButton(name, callback_data=f"setlang_{code}")
            for code, name in SUPPORTED_LANGUAGES.items()
        ]
        kb.add(*btns)
        bot.send_message(chat_id, t(lang, "choose_lang"), reply_markup=kb, parse_mode="HTML")

    @bot.callback_query_handler(func=lambda c: c.data.startswith("setlang_"))
    def cb_set_lang(call):
        code = call.data.replace("setlang_", "")
        if code not in SUPPORTED_LANGUAGES:
            bot.answer_callback_query(call.id)
            return
        update_user(call.from_user.id, language=code)
        bot.answer_callback_query(call.id, t(code, "lang_set"))
        bot.edit_message_text(
            t(code, "lang_set"),
            call.message.chat.id,
            call.message.message_id,
            parse_mode="HTML",
        )

    @bot.callback_query_handler(func=lambda c: c.data == "cb_help")
    def cb_help(call):
        lang  = get_user_lang(call.from_user.id)
        limit = int(get_setting("daily_limit", str(DAILY_DOWNLOAD_LIMIT)))
        bot.answer_callback_query(call.id)
        bot.send_message(
            call.message.chat.id,
            t(lang, "help_text", limit=limit),
            parse_mode="HTML",
        )

    @bot.callback_query_handler(func=lambda c: c.data == "cb_premium")
    def cb_premium(call):
        lang = get_user_lang(call.from_user.id)
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, t(lang, "premium_text"), parse_mode="HTML")

    @bot.callback_query_handler(func=lambda c: c.data == "cb_referral")
    def cb_referral(call):
        uid  = call.from_user.id
        user = get_user(uid)
        lang = user.get("language", "en") if user else "en"
        pts  = user.get("referral_points", 0) if user else 0
        link = build_referral_link(BOT_USERNAME, uid)
        bot.answer_callback_query(call.id)
        bot.send_message(
            call.message.chat.id,
            t(lang, "referral_text", ref_link=link, points=pts),
            parse_mode="HTML",
        )
