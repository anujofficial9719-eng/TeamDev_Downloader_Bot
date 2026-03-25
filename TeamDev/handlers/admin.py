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
from datetime import date, timedelta
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, Message, ForceReply

from config import ADMIN_IDS, DAILY_DOWNLOAD_LIMIT
from TeamDev.core.database import (
    get_setting, set_setting,
    get_user, update_user,
    count_all_users, count_premium_users,
    count_downloads_today_all, count_all_downloads, count_downloads_since,
    get_platform_stats, get_recent_logs, get_all_users,
    create_ad, get_all_ads, set_ad_active, delete_ad,
    _users,
)
from TeamDev.utils.i18n import t

_DIVIDER = "━━━━━━━━━━"

def _is_admin(uid: int) -> bool:
    return uid in ADMIN_IDS

_admin_state: dict[int, dict] = {}


def _main_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup()
    kb.row(
        InlineKeyboardButton("[ Stats ]",          callback_data="adm_stats"),
        InlineKeyboardButton("[ Platform Stats ]", callback_data="adm_platform_stats"),
    )
    kb.row(
        InlineKeyboardButton("[ Users ]",          callback_data="adm_users_menu"),
        InlineKeyboardButton("[ Broadcast ]",      callback_data="adm_broadcast"),
    )
    kb.row(
        InlineKeyboardButton("[ Ads ]",            callback_data="adm_ads_menu"),
        InlineKeyboardButton("[ Settings ]",       callback_data="adm_settings_menu"),
    )
    kb.row(
        InlineKeyboardButton("[ API Keys ]",       callback_data="adm_apikeys_menu"),
        InlineKeyboardButton("[ Logs ]",           callback_data="adm_logs"),
    )
    kb.add(InlineKeyboardButton("[ Help ]",        callback_data="adm_help"))
    return kb

def _back_kb(cb: str = "adm_main") -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("« Back", callback_data=cb))
    return kb

def _users_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup()
    kb.row(
        InlineKeyboardButton("[ Find User ]",      callback_data="adm_find_user"),
        InlineKeyboardButton("[ Grant Premium ]",  callback_data="adm_grant_premium"),
    )
    kb.row(
        InlineKeyboardButton("[ Revoke Premium ]", callback_data="adm_revoke_premium"),
        InlineKeyboardButton("[ Ban ]",            callback_data="adm_ban_user"),
    )
    kb.row(
        InlineKeyboardButton("[ Unban ]",          callback_data="adm_unban_user"),
        InlineKeyboardButton("[ Warn ]",           callback_data="adm_warn_user"),
    )
    kb.add(InlineKeyboardButton("« Back",          callback_data="adm_main"))
    return kb

def _ads_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup()
    kb.row(
        InlineKeyboardButton("[ Create Ad ]", callback_data="adm_create_ad"),
        InlineKeyboardButton("[ List Ads ]",  callback_data="adm_list_ads"),
    )
    kb.add(InlineKeyboardButton("« Back", callback_data="adm_main"))
    return kb

def _settings_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup()
    kb.row(
        InlineKeyboardButton("[ Daily Limit ]",    callback_data="adm_set_limit"),
        InlineKeyboardButton("[ Force Join ]",     callback_data="adm_toggle_forcejoin"),
    )
    kb.row(
        InlineKeyboardButton("[ Set Channel ]",    callback_data="adm_set_channel"),
        InlineKeyboardButton("[ Start Photo ]",    callback_data="adm_set_photo"),
    )
    kb.add(InlineKeyboardButton("« Back", callback_data="adm_main"))
    return kb

def _apikeys_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup()
    kb.row(
        InlineKeyboardButton("[ YT Key ]",      callback_data="adm_key_yt"),
        InlineKeyboardButton("[ Terabox Key ]", callback_data="adm_key_terabox"),
    )
    kb.add(InlineKeyboardButton("« Back", callback_data="adm_main"))
    return kb


def _fmt_user(user: dict) -> str:
    status = "★ Premium" if user.get("is_premium") else ("✗ Banned" if user.get("is_banned") else "◇ Free")
    return (
        f"◆ User Info\n"
        f"{_DIVIDER}\n"
        f"▸ ID:       {user['telegram_id']}\n"
        f"▸ Name:     {user.get('first_name','')}\n"
        f"▸ Username: @{user.get('username') or 'N/A'}\n"
        f"▸ Status:   {status}\n"
        f"▸ Warns:    {user.get('warn_count', 0)}\n"
        f"▸ Ref pts:  {user.get('referral_points', 0)}\n"
        f"▸ Language: {user.get('language','en')}\n"
        f"▸ Joined:   {str(user.get('created_at',''))[:10]}"
    )


def _send_main(bot, chat_id):
    bot.send_message(
        chat_id,
        f"◆ Admin Panel\n{_DIVIDER}\n_Select an action:_",
        reply_markup=_main_kb(),
        parse_mode="HTML",
    )


def register_admin_handlers(bot: telebot.TeleBot):

    @bot.message_handler(commands=["admin"])
    def cmd_admin(msg: Message):
        if not _is_admin(msg.from_user.id):
            bot.send_message(msg.chat.id, t("en", "not_admin"), parse_mode="HTML")
            return
        _send_main(bot, msg.chat.id)

    @bot.callback_query_handler(func=lambda c: c.data == "adm_main")
    def cb_main(call):
        if not _is_admin(call.from_user.id): return
        bot.answer_callback_query(call.id)
        try:
            bot.edit_message_text(
                f"◆ Admin Panel\n{_DIVIDER}\n_Select an action:_",
                call.message.chat.id, call.message.message_id,
                reply_markup=_main_kb(), parse_mode="HTML",
            )
        except Exception:
            _send_main(bot, call.message.chat.id)

    @bot.callback_query_handler(func=lambda c: c.data == "adm_users_menu")
    def cb_users_menu(call):
        if not _is_admin(call.from_user.id): return
        bot.answer_callback_query(call.id)
        bot.edit_message_text(
            f"◆ User Management\n{_DIVIDER}\n_Select action:_",
            call.message.chat.id, call.message.message_id,
            reply_markup=_users_kb(), parse_mode="HTML",
        )

    @bot.callback_query_handler(func=lambda c: c.data == "adm_ads_menu")
    def cb_ads_menu(call):
        if not _is_admin(call.from_user.id): return
        bot.answer_callback_query(call.id)
        bot.edit_message_text(
            f"◆ Ad Management\n{_DIVIDER}",
            call.message.chat.id, call.message.message_id,
            reply_markup=_ads_kb(), parse_mode="HTML",
        )

    @bot.callback_query_handler(func=lambda c: c.data == "adm_settings_menu")
    def cb_settings_menu(call):
        if not _is_admin(call.from_user.id): return
        bot.answer_callback_query(call.id)
        limit = get_setting("daily_limit", "3")
        fj    = get_setting("force_join_enabled", "true")
        ch    = get_setting("force_join_channel", "not set")
        bot.edit_message_text(
            f"◆ Bot Settings\n{_DIVIDER}\n"
            f"▸ Daily limit:  {limit}\n"
            f"▸ Force join:   {fj}\n"
            f"▸ Channel:      {ch}",
            call.message.chat.id, call.message.message_id,
            reply_markup=_settings_kb(), parse_mode="HTML",
        )

    @bot.callback_query_handler(func=lambda c: c.data == "adm_apikeys_menu")
    def cb_apikeys_menu(call):
        if not _is_admin(call.from_user.id): return
        bot.answer_callback_query(call.id)
        yt  = os.getenv("YT_API_KEY", "not set")
        tb  = os.getenv("TERABOX_API_KEY", "not set")
        bot.edit_message_text(
            f"◆ API Keys\n{_DIVIDER}\n"
            f"▸ YT Key:      ...{yt[-6:] if len(yt)>6 else yt}\n"
            f"▸ Terabox Key: ...{tb[-6:] if len(tb)>6 else tb}\n\n"
            f"_Tap to update:_",
            call.message.chat.id, call.message.message_id,
            reply_markup=_apikeys_kb(), parse_mode="HTML",
        )

    @bot.callback_query_handler(func=lambda c: c.data == "adm_stats")
    def cb_stats(call):
        if not _is_admin(call.from_user.id): return
        bot.answer_callback_query(call.id)
        total   = count_all_users()
        premium = count_premium_users()
        today   = count_downloads_today_all()
        total_dl= count_all_downloads()
        week    = count_downloads_since((date.today() - timedelta(days=7)).isoformat())
        bot.edit_message_text(
            f"◆ Statistics\n{_DIVIDER}\n"
            f"*Users*\n"
            f"▸ Total:    {total}\n"
            f"▸ Premium:  {premium}\n"
            f"▸ Free:     {total - premium}\n\n"
            f"*Downloads*\n"
            f"▸ Today:    {today}\n"
            f"▸ 7 days:   {week}\n"
            f"▸ All time: {total_dl}",
            call.message.chat.id, call.message.message_id,
            reply_markup=_back_kb(), parse_mode="HTML",
        )

    @bot.callback_query_handler(func=lambda c: c.data == "adm_platform_stats")
    def cb_platform_stats(call):
        if not _is_admin(call.from_user.id): return
        bot.answer_callback_query(call.id)
        stats = get_platform_stats()
        lines = [f"◆ Downloads by Platform\n{_DIVIDER}"]
        for row in stats:
            lines.append(f"▸ {row['_id'].title():<14} {row['count']}")
        if not stats:
            lines.append("_No downloads yet._")
        bot.edit_message_text(
            "\n".join(lines),
            call.message.chat.id, call.message.message_id,
            reply_markup=_back_kb(), parse_mode="HTML",
        )

    @bot.callback_query_handler(func=lambda c: c.data == "adm_logs")
    def cb_logs(call):
        if not _is_admin(call.from_user.id): return
        bot.answer_callback_query(call.id)
        logs  = get_recent_logs(10)
        lines = [f"◆ Last 10 Downloads\n{_DIVIDER}"]
        for log in logs:
            lines.append(f"▸ {log['date']} · {log['platform']} · uid:{log['telegram_id']}")
        if not logs:
            lines.append("_No logs yet._")
        bot.edit_message_text(
            "\n".join(lines),
            call.message.chat.id, call.message.message_id,
            reply_markup=_back_kb(), parse_mode="HTML",
        )

    @bot.callback_query_handler(func=lambda c: c.data == "adm_broadcast")
    def cb_broadcast(call):
        if not _is_admin(call.from_user.id): return
        bot.answer_callback_query(call.id)
        sent = bot.send_message(
            call.message.chat.id,
            f"◆ Broadcast\n{_DIVIDER}\nSend the message to broadcast:\n_(HTML supported)_",
            reply_markup=ForceReply(), parse_mode="HTML",
        )
        _admin_state[call.from_user.id] = {"action": "broadcast", "msg_id": sent.message_id}

    @bot.callback_query_handler(func=lambda c: c.data == "adm_find_user")
    def cb_find_user(call):
        if not _is_admin(call.from_user.id): return
        bot.answer_callback_query(call.id)
        sent = bot.send_message(call.message.chat.id, "Send *User ID* or *@username*:", reply_markup=ForceReply(), parse_mode="HTML")
        _admin_state[call.from_user.id] = {"action": "find_user", "msg_id": sent.message_id}

    @bot.callback_query_handler(func=lambda c: c.data in ("adm_grant_premium", "adm_revoke_premium"))
    def cb_premium_action(call):
        if not _is_admin(call.from_user.id): return
        action = "grant_premium" if call.data == "adm_grant_premium" else "revoke_premium"
        label  = "GRANT" if action == "grant_premium" else "REVOKE"
        bot.answer_callback_query(call.id)
        sent = bot.send_message(call.message.chat.id, f"Send *User ID* to {label} premium:", reply_markup=ForceReply(), parse_mode="HTML")
        _admin_state[call.from_user.id] = {"action": action, "msg_id": sent.message_id}

    @bot.callback_query_handler(func=lambda c: c.data in ("adm_ban_user", "adm_unban_user"))
    def cb_ban_action(call):
        if not _is_admin(call.from_user.id): return
        action = "ban_user" if call.data == "adm_ban_user" else "unban_user"
        label  = "BAN" if action == "ban_user" else "UNBAN"
        bot.answer_callback_query(call.id)
        sent = bot.send_message(call.message.chat.id, f"Send *User ID* to {label}:", reply_markup=ForceReply(), parse_mode="HTML")
        _admin_state[call.from_user.id] = {"action": action, "msg_id": sent.message_id}

    @bot.callback_query_handler(func=lambda c: c.data == "adm_warn_user")
    def cb_warn_user(call):
        if not _is_admin(call.from_user.id): return
        bot.answer_callback_query(call.id)
        sent = bot.send_message(call.message.chat.id, "Send *User ID* to warn:\n_(3 warns = auto ban)_", reply_markup=ForceReply(), parse_mode="HTML")
        _admin_state[call.from_user.id] = {"action": "warn_user", "msg_id": sent.message_id}

    @bot.callback_query_handler(func=lambda c: c.data == "adm_set_limit")
    def cb_set_limit(call):
        if not _is_admin(call.from_user.id): return
        bot.answer_callback_query(call.id)
        cur  = get_setting("daily_limit", "3")
        sent = bot.send_message(call.message.chat.id, f"Current limit: *{cur}*\n\nSend new limit:", reply_markup=ForceReply(), parse_mode="HTML")
        _admin_state[call.from_user.id] = {"action": "set_limit", "msg_id": sent.message_id}

    @bot.callback_query_handler(func=lambda c: c.data == "adm_toggle_forcejoin")
    def cb_toggle_fj(call):
        if not _is_admin(call.from_user.id): return
        bot.answer_callback_query(call.id)
        cur = get_setting("force_join_enabled", "true")
        new = "false" if cur == "true" else "true"
        set_setting("force_join_enabled", new)
        status = "Enabled" if new == "true" else "Disabled"
        bot.send_message(call.message.chat.id, f"◆ Force Join: *{status}*", parse_mode="HTML")

    @bot.callback_query_handler(func=lambda c: c.data == "adm_set_channel")
    def cb_set_channel(call):
        if not _is_admin(call.from_user.id): return
        bot.answer_callback_query(call.id)
        sent = bot.send_message(call.message.chat.id, "Send channel (e.g. @MyChannel):", reply_markup=ForceReply(), parse_mode="HTML")
        _admin_state[call.from_user.id] = {"action": "set_channel", "msg_id": sent.message_id}

    @bot.callback_query_handler(func=lambda c: c.data == "adm_set_photo")
    def cb_set_photo(call):
        if not _is_admin(call.from_user.id): return
        bot.answer_callback_query(call.id)
        sent = bot.send_message(call.message.chat.id, "Send start photo URL or file_id:", reply_markup=ForceReply(), parse_mode="HTML")
        _admin_state[call.from_user.id] = {"action": "set_photo", "msg_id": sent.message_id}

    @bot.callback_query_handler(func=lambda c: c.data in ("adm_key_yt", "adm_key_terabox"))
    def cb_api_key(call):
        if not _is_admin(call.from_user.id): return
        bot.answer_callback_query(call.id)
        key_map = {
            "adm_key_yt":      ("YT_API_KEY",     "YouTube"),
            "adm_key_terabox": ("TERABOX_API_KEY", "Terabox"),
        }
        env_key, label = key_map[call.data]
        sent = bot.send_message(
            call.message.chat.id,
            f"Send new *{label} API Key*:",
            reply_markup=ForceReply(), parse_mode="HTML",
        )
        _admin_state[call.from_user.id] = {"action": "set_api_key", "env_key": env_key, "label": label, "msg_id": sent.message_id}

    @bot.callback_query_handler(func=lambda c: c.data == "adm_create_ad")
    def cb_create_ad(call):
        if not _is_admin(call.from_user.id): return
        bot.answer_callback_query(call.id)
        instructions = (
            f"◆ *Create Ad*\n{_DIVIDER}\n"
            "Send ad in this format:\n\n"
            "TYPE: text|photo\n"
            "CONTENT: Your message\n"
            "PHOTO: url  _(optional)_\n"
            "BTN_TEXT: Label  _(optional)_\n"
            "BTN_URL: https://...  _(optional)_"
        )
        sent = bot.send_message(call.message.chat.id, instructions, reply_markup=ForceReply(), parse_mode="HTML")
        _admin_state[call.from_user.id] = {"action": "create_ad", "msg_id": sent.message_id}

    @bot.callback_query_handler(func=lambda c: c.data == "adm_list_ads")
    def cb_list_ads(call):
        if not _is_admin(call.from_user.id): return
        bot.answer_callback_query(call.id)
        ads = get_all_ads()
        if not ads:
            bot.send_message(call.message.chat.id, "◆ No ads found.", parse_mode="HTML")
            return
        for ad in ads:
            ad_id  = str(ad["_id"])
            status = "[ ACTIVE ]" if ad.get("is_active") else "[ OFF ]"
            text   = f"◆ *Ad {ad_id[-6:]}* {status}\nType: {ad.get('ad_type')}\n{ad.get('content','')[:80]}"
            kb     = InlineKeyboardMarkup()
            if ad.get("is_active"):
                kb.add(InlineKeyboardButton("[ Deactivate ]", callback_data=f"adm_deact_{ad_id}"))
            else:
                kb.add(InlineKeyboardButton("[ Activate ]",   callback_data=f"adm_act_{ad_id}"))
            kb.add(InlineKeyboardButton("[ Delete ]",         callback_data=f"adm_del_ad_{ad_id}"))
            bot.send_message(call.message.chat.id, text, reply_markup=kb, parse_mode="HTML")

    @bot.callback_query_handler(func=lambda c: c.data.startswith("adm_deact_"))
    def cb_deact_ad(call):
        if not _is_admin(call.from_user.id): return
        set_ad_active(call.data.replace("adm_deact_", ""), False)
        bot.answer_callback_query(call.id, "Deactivated.")
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id)

    @bot.callback_query_handler(func=lambda c: c.data.startswith("adm_act_"))
    def cb_act_ad(call):
        if not _is_admin(call.from_user.id): return
        set_ad_active(call.data.replace("adm_act_", ""), True)
        bot.answer_callback_query(call.id, "Activated.")
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id)

    @bot.callback_query_handler(func=lambda c: c.data.startswith("adm_del_ad_"))
    def cb_del_ad(call):
        if not _is_admin(call.from_user.id): return
        delete_ad(call.data.replace("adm_del_ad_", ""))
        bot.answer_callback_query(call.id, "Deleted.")
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id)

    @bot.callback_query_handler(func=lambda c: c.data == "adm_help")
    def cb_admin_help(call):
        if not _is_admin(call.from_user.id): return
        bot.answer_callback_query(call.id)
        help_text = (
            f"◆ *Admin Help*\n{_DIVIDER}\n\n"
            "▸ *Stats* — Users, downloads today/week/all\n"
            "▸ *Platform Stats* — Breakdown per platform\n"
            "▸ *Logs* — Last 10 download entries\n\n"
            f"*Users*\n"
            "▸ Find — Look up by ID or @username\n"
            "▸ Grant/Revoke Premium\n"
            "▸ Ban/Unban\n"
            "▸ Warn — 3 warns = auto ban\n\n"
            "▸ *Broadcast* — Message all users\n\n"
            f"*Ads*\n"
            "▸ Create text or photo ads\n"
            "▸ Activate / deactivate / delete\n\n"
            f"*Settings*\n"
            "▸ Daily Limit, Force Join, Channel, Start Photo\n\n"
            "▸ *API Keys* — Update YT/Terabox keys\n"
            "_(Updates runtime + .env file)_"
        )
        bot.edit_message_text(
            help_text, call.message.chat.id, call.message.message_id,
            reply_markup=_back_kb(), parse_mode="HTML",
        )

    @bot.message_handler(
        func=lambda m: (
            m.reply_to_message is not None
            and m.from_user.id in _admin_state
        )
    )
    def handle_admin_reply(msg: Message):
        if not _is_admin(msg.from_user.id): return
        state  = _admin_state.pop(msg.from_user.id, {})
        action = state.get("action", "")
        text   = (msg.text or "").strip()

        if action == "set_limit":
            try:
                limit = int(text)
                set_setting("daily_limit", str(limit))
                bot.send_message(msg.chat.id, f"◆ Daily limit set to *{limit}*.", parse_mode="HTML")
            except ValueError:
                bot.send_message(msg.chat.id, "◆ Invalid number.")

        elif action == "broadcast":
            users = get_all_users()
            count = 0
            for u in users:
                try:
                    bot.send_message(u["telegram_id"], text, parse_mode="HTML")
                    count += 1
                except Exception:
                    pass
            bot.send_message(msg.chat.id, f"◆ Sent to *{count}* users.", parse_mode="HTML")

        elif action == "find_user":
            if text.startswith("@"):
                user = _users().find_one({"username": text.lstrip("@")})
            else:
                try:
                    user = _users().find_one({"telegram_id": int(text)})
                except ValueError:
                    user = None
            if user:
                bot.send_message(msg.chat.id, _fmt_user(user), parse_mode="HTML")
            else:
                bot.send_message(msg.chat.id, "◆ User not found.")

        elif action in ("grant_premium", "revoke_premium"):
            try:
                tid    = int(text)
                is_p   = (action == "grant_premium")
                update_user(tid, is_premium=is_p)
                label  = "granted" if is_p else "revoked"
                bot.send_message(msg.chat.id, f"◆ Premium *{label}* for {tid}.", parse_mode="HTML")
                try:
                    note = "★ You have been granted *Premium* access!" if is_p else "◆ Your Premium access has been removed."
                    bot.send_message(tid, note, parse_mode="HTML")
                except Exception:
                    pass
            except ValueError:
                bot.send_message(msg.chat.id, "◆ Invalid user ID.")

        elif action in ("ban_user", "unban_user"):
            try:
                tid     = int(text)
                is_ban  = (action == "ban_user")
                update_user(tid, is_banned=is_ban)
                label   = "banned" if is_ban else "unbanned"
                bot.send_message(msg.chat.id, f"◆ User {tid} *{label}*.", parse_mode="HTML")
                if is_ban:
                    try:
                        bot.send_message(tid, "◆ You have been banned from this bot.")
                    except Exception:
                        pass
            except ValueError:
                bot.send_message(msg.chat.id, "◆ Invalid user ID.")

        elif action == "warn_user":
            try:
                tid  = int(text)
                user = _users().find_one({"telegram_id": tid})
                if user:
                    warns = user.get("warn_count", 0) + 1
                    update_user(tid, warn_count=warns)
                    bot.send_message(msg.chat.id, f"◆ Warning *{warns}/3* issued to {tid}.", parse_mode="HTML")
                    try:
                        note = f"◆ *Warning {warns}/3* received from admin."
                        if warns >= 3:
                            note += "\n_You have been banned after 3 warnings._"
                            update_user(tid, is_banned=True)
                        bot.send_message(tid, note, parse_mode="HTML")
                    except Exception:
                        pass
                    if warns >= 3:
                        bot.send_message(msg.chat.id, f"◆ User {tid} auto-banned.", parse_mode="HTML")
                else:
                    bot.send_message(msg.chat.id, "◆ User not found.")
            except ValueError:
                bot.send_message(msg.chat.id, "◆ Invalid user ID.")

        elif action == "set_channel":
            channel = text if text.startswith("@") else f"@{text}"
            set_setting("force_join_channel", channel)
            bot.send_message(msg.chat.id, f"◆ Channel set to {channel}.", parse_mode="HTML")

        elif action == "set_photo":
            set_setting("start_photo", text)
            bot.send_message(msg.chat.id, "◆ Start photo updated.", parse_mode="HTML")

        elif action == "set_api_key":
            env_key = state.get("env_key", "")
            label   = state.get("label", "")
            os.environ[env_key] = text
            try:
                env_path = ".env"
                if os.path.exists(env_path):
                    lines   = open(env_path).readlines()
                    updated = False
                    new_lines = []
                    for line in lines:
                        if line.startswith(f"{env_key}="):
                            new_lines.append(f"{env_key}={text}\n")
                            updated = True
                        else:
                            new_lines.append(line)
                    if not updated:
                        new_lines.append(f"\n{env_key}={text}\n")
                    open(env_path, "w").writelines(new_lines)
                bot.send_message(msg.chat.id, f"◆ *{label}* key updated — runtime + .env.", parse_mode="HTML")
            except Exception as e:
                bot.send_message(msg.chat.id, f"◆ Runtime updated, .env failed: {e}", parse_mode="HTML")

        elif action == "create_ad":
            params = {}
            for line in text.splitlines():
                if ":" in line:
                    k, _, v = line.partition(":")
                    params[k.strip().upper()] = v.strip()
            create_ad(
                ad_type   = params.get("TYPE", "text").lower(),
                content   = params.get("CONTENT", ""),
                photo_url = params.get("PHOTO") or None,
                btn_text  = params.get("BTN_TEXT") or None,
                btn_url   = params.get("BTN_URL") or None,
            )
            bot.send_message(msg.chat.id, "◆ Ad created and activated.", parse_mode="HTML")
