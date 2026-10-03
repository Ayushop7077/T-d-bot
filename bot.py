import os
import random
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

TOKEN = os.environ.get("BOT_TOKEN")

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

# One active game per Telegram chat.
games = {}

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


def keyboard(game):
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("➕ Join Game", callback_data="join"),
            InlineKeyboardButton("👥 Players", callback_data="players")
        ],
        [
            InlineKeyboardButton("🎡 Spin", callback_data="spin")
        ],
        [
            InlineKeyboardButton("🛑 End Game", callback_data="end")
        ]
    ])


def truth_dare_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("💬 Truth", callback_data="truth"),
            InlineKeyboardButton("🔥 Dare", callback_data="dare")
        ]
    ])


def next_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🎡 Next Round", callback_data="spin")],
        [InlineKeyboardButton("👥 Players", callback_data="players")]
    ])


def game_text(game):
    names = "\n".join(f"• {p['name']}" for p in game["players"])
    return (
        "🎡 *TRUTH & DARE*\n\n"
        f"Players ({len(game['players'])}):\n{names}\n\n"
        "Press *Join Game* to enter.\n"
        "When everyone is ready, press *Spin*."
    )


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎡 *Truth & Dare Bot*\n\n"
        "Add me to a group and use /newgame to start a game.\n\n"
        "Commands:\n"
        "• /newgame — start a game\n"
        "• /join — join the game\n"
        "• /players — show players\n"
        "• /spin — spin the wheel\n"
        "• /endgame — end the game",
        parse_mode="Markdown"
    )


async def newgame(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id

    if chat_id in games:
        await update.message.reply_text(
            "⚠️ A game is already running in this group.\n"
            "Use /endgame before starting another one."
        )
        return

    games[chat_id] = {
        "players": [],
        "selected": None,
        "questioner": None,
        "round": 0
    }

    await update.message.reply_text(
        "🎡 *NEW TRUTH & DARE GAME!*\n\n"
        "Everyone who wants to play, press *Join Game*.\n"
        "Then press *Spin* when you're ready.",
        reply_markup=keyboard(games[chat_id]),
        parse_mode="Markdown"
    )


async def join_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id

    if chat_id not in games:
        await update.message.reply_text("No game is running. Use /newgame first.")
        return

    await add_player(update.effective_user, chat_id, update.message.reply_text)


async def add_player(user, chat_id, reply):
    game = games[chat_id]

    if any(p["id"] == user.id for p in game["players"]):
        await reply(f"👤 {user.first_name}, you're already in the game.")
        return

    game["players"].append({
        "id": user.id,
        "name": user.first_name
    })

    await reply(
        f"✅ *{user.first_name}* joined the game!\n\n"
        + game_text(game),
        reply_markup=keyboard(game),
        parse_mode="Markdown"
    )


async def players_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id

    if chat_id not in games:
        await update.message.reply_text("No game is running.")
        return

    await update.message.reply_text(
        game_text(games[chat_id]),
        reply_markup=keyboard(games[chat_id]),
        parse_mode="Markdown"
    )


async def spin_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id

    if chat_id not in games:
        await update.message.reply_text("No game is running. Use /newgame first.")
        return

    game = games[chat_id]

    if len(game["players"]) < 2:
        await update.message.reply_text(
            "⚠️ You need at least *2 players* to spin.",
            parse_mode="Markdown"
        )
        return

    game["round"] += 1

    selected = random.choice(game["players"])
    others = [p for p in game["players"] if p["id"] != selected["id"]]
    questioner = random.choice(others)

    game["selected"] = selected
    game["questioner"] = questioner

    await update.message.reply_text(
        "🎡 *SPINNING...*\n\n"
        "━━━━━━━━━━━━━━\n"
        f"🎯 *PLAYER*\n{selected['name']}\n\n"
        f"❓ *QUESTIONER*\n{questioner['name']}\n"
        "━━━━━━━━━━━━━━\n\n"
        "Choose what happens next:",
        reply_markup=truth_dare_keyboard(),
        parse_mode="Markdown"
    )


async def spin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await spin_game(update, context)


async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    chat_id = query.message.chat_id
    action = query.data

    if action == "join":
        if chat_id not in games:
            await query.message.reply_text("No game is running. Use /newgame first.")
            return

        await add_player(
            query.from_user,
            chat_id,
            query.message.reply_text
        )
        return

    if action == "players":
        if chat_id not in games:
            await query.message.reply_text("No game is running.")
            return

        await query.message.reply_text(
            game_text(games[chat_id]),
            reply_markup=keyboard(games[chat_id]),
            parse_mode="Markdown"
        )
        return

    if action == "spin":
        await spin_game(query.message, context)
        return

    if action in ("truth", "dare"):
        if chat_id not in games:
            return

        game = games[chat_id]

        if not game["selected"]:
            await query.message.reply_text("Spin first.")
            return

        selected = game["selected"]["name"]
        questioner = game["questioner"]["name"]

        prompt = random.choice(TRUTHS if action == "truth" else DARES)

        if action == "truth":
            text = (
                "💬 *TRUTH*\n\n"
                f"🎯 *{selected}*, answer this:\n\n"
                f"❓ {prompt}\n\n"
                f"Asked by: *{questioner}*"
            )
        else:
            text = (
                "🔥 *DARE*\n\n"
                f"🎯 *{selected}*, your dare:\n\n"
                f"👉 {prompt}\n\n"
                f"Given by: *{questioner}*"
            )

        await query.message.reply_text(
            text,
            reply_markup=next_keyboard(),
            parse_mode="Markdown"
        )
        return

    if action == "end":
        if chat_id in games:
            del games[chat_id]

        await query.message.reply_text(
            "🛑 *Game ended.*\n\nUse /newgame whenever you want to play again.",
            parse_mode="Markdown"
        )


async def endgame(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id

    if chat_id not in games:
        await update.message.reply_text("No game is currently running.")
        return

    del games[chat_id]

    await update.message.reply_text(
        "🛑 *Game ended.*\n\nUse /newgame to start a new game.",
        parse_mode="Markdown"
    )


def main():
    if not TOKEN:
        raise RuntimeError("BOT_TOKEN environment variable is missing.")

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("newgame", newgame))
    app.add_handler(CommandHandler("join", join_command))
    app.add_handler(CommandHandler("players", players_command))
    app.add_handler(CommandHandler("spin", spin_command))
    app.add_handler(CommandHandler("endgame", endgame))
    app.add_handler(CallbackQueryHandler(button))

    print("Truth & Dare bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()
