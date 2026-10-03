# 🎡 Truth & Dare — Telegram Group Bot

This version works entirely inside a Telegram group.

There is NO Mini App and NO website interface.

## Features

- `/newgame` creates a game
- Inline **Join Game** button
- `/join` also works
- Random player selection
- Random questioner selection
- Player and questioner are always different
- Truth/Dare buttons
- Random Truth questions
- Random Dare challenges
- `/players`
- `/spin`
- `/endgame`
- Multiple Telegram groups can run their own game independently

## 1. Create the bot

Open @BotFather in Telegram.

Send:

/newbot

Choose a name and username.

BotFather will give you a bot token.

KEEP THE TOKEN PRIVATE.

## 2. Add the bot to your group

Add the bot as a member of your Telegram group.

If the bot cannot receive group messages, check its BotFather privacy setting.

You do NOT need to disable privacy for button interactions and commands such as /newgame, /join, /players, /spin and /endgame.

## 3. Install Python

Python 3.10+ is recommended.

Install dependencies:

pip install -r requirements.txt

## 4. Set your token

Linux/macOS:

export BOT_TOKEN="YOUR_BOT_TOKEN"

Windows PowerShell:

$env:BOT_TOKEN="YOUR_BOT_TOKEN"

## 5. Run

python bot.py

The bot will poll Telegram and work directly in your group.

## Important limitation

This simple version stores games in RAM.

If the bot restarts, active games disappear.

For a permanent public bot, add Redis/PostgreSQL later.

## Basic gameplay

/newgame

Everyone presses:

➕ Join Game

Then:

🎡 Spin

The bot selects:

🎯 Player
❓ Questioner

Then:

💬 Truth / 🔥 Dare

Finally:

🎡 Next Round
