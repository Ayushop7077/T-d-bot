import os
import random
import threading
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

TOKEN = os.environ.get("BOT_TOKEN")
PORT = int(os.environ.get("PORT", "10000"))

# Tiny HTTP server so Render can health-check the service.
web = Flask(__name__)

@web.get("/")
def home():
    return "Truth & Dare bot is running."

def run_web():
    web.run(host="0.0.0.0", port=PORT)

TRUTHS = [
    "What is your most embarrassing moment?",
    "Who was your first crush?",
    "What is the last lie you told?",
    "What is one thing you pretend to like but actually don't?",
    "Who in this group would you trust with your biggest secret?",
    "What is your weirdest habit?",
    "What is something you have never told your parents?",
    "What is the strangest thing you've searched online?",
    "What is one fear you rarely admit?",
    "If you could swap lives with someone here for a day, who would it be?",
    "What is the most childish thing you still do?",
    "What is one thing you would change about yourself?"
]

DARES = [
    "Do your best impression of someone in this group for 20 seconds.",
    "Sing the chorus of the first song that comes to your mind.",
    "Do 10 squats while saying your name after each one.",
    "Make everyone laugh without speaking.",
    "Give a dramatic motivational speech about a random object.",
    "Do your best celebrity impression.",
    "Walk across the room like a runway model.",
    "Make your funniest face and hold it for 10 seconds.",
    "Speak in a dramatic movie voice until your next turn.",
    "Dance for 20 seconds without music.",
    "Try to say the alphabet backwards.",
    "Let the group choose a funny nickname for you for the next round."
]

games = {}

def main_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ Join Game", callback_data="join"),
         InlineKeyboardButton("👥 Players", callback_data="players")],
        [InlineKeyboardButton("🎡 Spin", callback_data="spin")],
        [InlineKeyboardButton("🛑 End Game", callback_data="end")]
    ])

def truth_dare_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💬 Truth", callback_data="truth"),
         InlineKeyboardButton("🔥 Dare", callback_data="dare")]
    ])

def next_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🎡 Next Round", callback_data="spin")],
        [InlineKeyboardButton("👥 Players", callback_data="players")]
    ])

def game_text(game):
    if not game["players"]:
        names = "No players yet."
    else:
        names = "\n".join(f"• {p['name']}" for p in game["players"])
    return f"🎡 *TRUTH & DARE*\n\nPlayers ({len(game['players'])}):\n{names}\n\nPress *Join Game* to enter."

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎡 *Truth & Dare Bot*\n\n"
        "Use /newgame in a group to start a game.",
        parse_mode="Markdown"
    )

async def newgame(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if chat_id in games:
        await update.message.reply_text("⚠️ A game is already running. Use /endgame first.")
        return
    games[chat_id] = {"players": [], "selected": None, "questioner": None}
    await update.message.reply_text(
        "🎡 *NEW TRUTH & DARE GAME!*\n\nEveryone who wants to play, press *Join Game*.",
        reply_markup=main_keyboard(),
        parse_mode="Markdown"
    )

async def add_player(user, chat_id, reply):
    game = games[chat_id]
    if any(p["id"] == user.id for p in game["players"]):
        await reply(f"👤 {user.first_name}, you're already in the game.")
        return
    game["players"].append({"id": user.id, "name": user.first_name})
    await reply(game_text(game), reply_markup=main_keyboard(), parse_mode="Markdown")

async def join_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if chat_id not in games:
        await update.message.reply_text("No game is running. Use /newgame first.")
        return
    await add_player(update.effective_user, chat_id, update.message.reply_text)

async def players_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if chat_id not in games:
        await update.message.reply_text("No game is running.")
        return
    await update.message.reply_text(game_text(games[chat_id]), reply_markup=main_keyboard(), parse_mode="Markdown")

async def spin_game(message, context):
    chat_id = message.chat_id
    if chat_id not in games:
        await message.reply_text("No game is running. Use /newgame first.")
        return
    game = games[chat_id]
    if len(game["players"]) < 2:
        await message.reply_text("⚠️ You need at least *2 players* to spin.", parse_mode="Markdown")
        return
    selected = random.choice(game["players"])
    others = [p for p in game["players"] if p["id"] != selected["id"]]
    questioner = random.choice(others)
    game["selected"] = selected
    game["questioner"] = questioner
    await message.reply_text(
        "🎡 *SPINNING...*\n\n"
        f"🎯 *PLAYER:* {selected['name']}\n"
        f"❓ *QUESTIONER:* {questioner['name']}\n\n"
        "Choose:",
        reply_markup=truth_dare_keyboard(),
        parse_mode="Markdown"
    )

async def spin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await spin_game(update.message, context)

async def endgame(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if chat_id not in games:
        await update.message.reply_text("No game is currently running.")
        return
    del games[chat_id]
    await update.message.reply_text("🛑 *Game ended.* Use /newgame to play again.", parse_mode="Markdown")

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    chat_id = q.message.chat_id

    if q.data == "join":
        if chat_id not in games:
            await q.message.reply_text("No game is running. Use /newgame first.")
            return
        await add_player(q.from_user, chat_id, q.message.reply_text)

    elif q.data == "players":
        if chat_id in games:
            await q.message.reply_text(game_text(games[chat_id]), reply_markup=main_keyboard(), parse_mode="Markdown")

    elif q.data == "spin":
        await spin_game(q.message, context)

    elif q.data in ("truth", "dare"):
        if chat_id not in games or not games[chat_id]["selected"]:
            await q.message.reply_text("Spin first.")
            return
        game = games[chat_id]
        selected = game["selected"]["name"]
        questioner = game["questioner"]["name"]
        prompt = random.choice(TRUTHS if q.data == "truth" else DARES)
        title = "💬 *TRUTH*" if q.data == "truth" else "🔥 *DARE*"
        await q.message.reply_text(
            f"{title}\n\n🎯 *{selected}*\n\n{prompt}\n\nAsked/Given by: *{questioner}*",
            reply_markup=next_keyboard(),
            parse_mode="Markdown"
        )

    elif q.data == "end":
        games.pop(chat_id, None)
        await q.message.reply_text("🛑 *Game ended.* Use /newgame to start again.", parse_mode="Markdown")

def main():
    if not TOKEN:
        raise RuntimeError("BOT_TOKEN is missing.")
    threading.Thread(target=run_web, daemon=True).start()
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("newgame", newgame))
    application.add_handler(CommandHandler("join", join_command))
    application.add_handler(CommandHandler("players", players_command))
    application.add_handler(CommandHandler("spin", spin_command))
    application.add_handler(CommandHandler("endgame", endgame))
    application.add_handler(CallbackQueryHandler(button))
    application.run_polling()

if __name__ == "__main__":
    main()
