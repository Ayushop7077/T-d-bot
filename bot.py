import os, random, threading
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

TOKEN=os.environ.get('BOT_TOKEN'); PORT=int(os.environ.get('PORT','10000'))
web=Flask(__name__)
@web.get('/')
def home(): return 'Truth & Dare bot is running.'
def run_web(): web.run(host='0.0.0.0',port=PORT)

TRUTHS=[
'What is your most embarrassing moment?','Who was your first crush?','What is the last lie you told?',
'What is one thing you pretend to like but actually don’t?','Who in this group would you trust with your biggest secret?',
'What is your weirdest habit?','What is something you have never told your parents?',
'What is the strangest thing you’ve searched online?','What is one fear you rarely admit?',
'If you could swap lives with someone here for a day, who would it be?','What is the most childish thing you still do?',
'What is one thing you would change about yourself?']
DARES=[
'Do your best impression of someone in this group for 20 seconds.','Sing the chorus of the first song that comes to your mind.',
'Do 10 squats while saying your name after each one.','Make everyone laugh without speaking.',
'Give a dramatic motivational speech about a random object.','Do your best celebrity impression.',
'Walk across the room like a runway model.','Make your funniest face and hold it for 10 seconds.',
'Speak in a dramatic movie voice until your next turn.','Dance for 20 seconds without music.',
'Try to say the alphabet backwards.','Let the group choose a funny nickname for you for the next round.']
games={}

def join_keyboard(): return InlineKeyboardMarkup([[InlineKeyboardButton('➕ Join Game',callback_data='join'),InlineKeyboardButton('👥 Players',callback_data='players')],[InlineKeyboardButton('🔒 Start Game',callback_data='startgame')],[InlineKeyboardButton('🛑 End Game',callback_data='end')]])
def game_keyboard(): return InlineKeyboardMarkup([[InlineKeyboardButton('👥 Players',callback_data='players')],[InlineKeyboardButton('🎡 Spin',callback_data='spin')],[InlineKeyboardButton('🛑 End Game',callback_data='end')]])
def truth_dare_keyboard(): return InlineKeyboardMarkup([[InlineKeyboardButton('💬 Truth',callback_data='truth'),InlineKeyboardButton('🔥 Dare',callback_data='dare')]])
def next_keyboard(): return InlineKeyboardMarkup([[InlineKeyboardButton('🎡 Next Round',callback_data='spin')],[InlineKeyboardButton('👥 Players',callback_data='players')]])

def game_text(g):
    names='\n'.join(f"• {p['name']}" for p in g['players']) if g['players'] else 'No players yet.'
    return f"🎡 *TRUTH & DARE*\n\nPlayers ({len(g['players'])}):\n{names}\n\n{'🔒 Player list is locked.' if g['locked'] else '🟢 Joining is open.'}"

async def start(update:Update,context:ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('🎡 *Truth & Dare Bot*\n\nUse /newgame in a group to start a game.',parse_mode='Markdown')
async def newgame(update:Update,context:ContextTypes.DEFAULT_TYPE):
    cid=update.effective_chat.id
    if cid in games: return await update.message.reply_text('⚠️ A game is already running. Use /endgame first.')
    u=update.effective_user; games[cid]={'host_id':u.id,'host_name':u.first_name,'players':[],'locked':False,'selected':None,'questioner':None}
    await update.message.reply_text(f"🎡 *NEW TRUTH & DARE GAME!*\n\n👑 Host: *{u.first_name}*\n\nEveryone who wants to play, press *Join Game*.\nWhen everyone has joined, the host should press *🔒 Start Game*.",reply_markup=join_keyboard(),parse_mode='Markdown')
async def add_player(user,cid,reply):
    g=games[cid]
    if g['locked']: return await reply('🔒 The player list is locked. You cannot join this game now.')
    if any(p['id']==user.id for p in g['players']): return await reply(f"👤 {user.first_name}, you're already in the game.")
    g['players'].append({'id':user.id,'name':user.first_name}); await reply(game_text(g),reply_markup=join_keyboard(),parse_mode='Markdown')
async def join_command(update:Update,context:ContextTypes.DEFAULT_TYPE):
    cid=update.effective_chat.id
    if cid not in games: return await update.message.reply_text('No game is running. Use /newgame first.')
    await add_player(update.effective_user,cid,update.message.reply_text)
async def players_command(update:Update,context:ContextTypes.DEFAULT_TYPE):
    cid=update.effective_chat.id
    if cid not in games: return await update.message.reply_text('No game is running.')
    g=games[cid]; await update.message.reply_text(game_text(g),reply_markup=game_keyboard() if g['locked'] else join_keyboard(),parse_mode='Markdown')
async def start_game(cid,user,reply):
    g=games.get(cid)
    if not g: return await reply('No game is running. Use /newgame first.')
    if user.id!=g['host_id']: return await reply(f"⛔ Only the host ({g['host_name']}) can start the game.")
    if g['locked']: return await reply('🔒 The player list is already locked.')
    if len(g['players'])<2: return await reply('⚠️ You need at least *2 players* before starting the game.',parse_mode='Markdown')
    g['locked']=True
    await reply('🔒 *PLAYER LIST LOCKED!*\n\n👥 '+str(len(g['players']))+' players are playing.\nNo more players can join this game.\n\n🎡 Press *Spin* to start the first round.',reply_markup=game_keyboard(),parse_mode='Markdown')
async def spin_game(message,context):
    cid=message.chat_id
    if cid not in games: return await message.reply_text('No game is running. Use /newgame first.')
    g=games[cid]
    if not g['locked']: return await message.reply_text('⏳ Players are still joining.\nThe host must press *🔒 Start Game* before anyone can spin.',parse_mode='Markdown')
    if len(g['players'])<2: return await message.reply_text('⚠️ You need at least *2 players* to spin.',parse_mode='Markdown')
    selected=random.choice(g['players']); questioner=random.choice([p for p in g['players'] if p['id']!=selected['id']]); g['selected']=selected; g['questioner']=questioner
    await message.reply_text(f"🎡 *SPINNING...*\n\n🎯 *PLAYER:* {selected['name']}\n❓ *QUESTIONER:* {questioner['name']}\n\nChoose:",reply_markup=truth_dare_keyboard(),parse_mode='Markdown')
async def spin_command(update,context): await spin_game(update.message,context)
async def endgame(update:Update,context:ContextTypes.DEFAULT_TYPE):
    cid=update.effective_chat.id
    if cid not in games: return await update.message.reply_text('No game is currently running.')
    del games[cid]; await update.message.reply_text('🛑 *Game ended.* Use /newgame to play again.',parse_mode='Markdown')
async def button(update:Update,context:ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer(); cid=q.message.chat_id
    if q.data=='join':
        if cid not in games: return await q.message.reply_text('No game is running. Use /newgame first.')
        await add_player(q.from_user,cid,q.message.reply_text)
    elif q.data=='players':
        if cid in games:
            g=games[cid]; await q.message.reply_text(game_text(g),reply_markup=game_keyboard() if g['locked'] else join_keyboard(),parse_mode='Markdown')
    elif q.data=='startgame': await start_game(cid,q.from_user,q.message.reply_text)
    elif q.data=='spin': await spin_game(q.message,context)
    elif q.data in ('truth','dare'):
        if cid not in games or not games[cid]['selected']: return await q.message.reply_text('Spin first.')
        g=games[cid]; prompt=random.choice(TRUTHS if q.data=='truth' else DARES); title='💬 *TRUTH*' if q.data=='truth' else '🔥 *DARE*'
        await q.message.reply_text(f"{title}\n\n🎯 *{g['selected']['name']}*\n\n{prompt}\n\nAsked/Given by: *{g['questioner']['name']}*",reply_markup=next_keyboard(),parse_mode='Markdown')
    elif q.data=='end':
        games.pop(cid,None); await q.message.reply_text('🛑 *Game ended.* Use /newgame to start again.',parse_mode='Markdown')

def main():
    if not TOKEN: raise RuntimeError('BOT_TOKEN is missing.')
    threading.Thread(target=run_web,daemon=True).start()
    app=Application.builder().token(TOKEN).build()
    for cmd,fn in [('start',start),('newgame',newgame),('join',join_command),('players',players_command),('spin',spin_command),('endgame',endgame)]: app.add_handler(CommandHandler(cmd,fn))
    app.add_handler(CallbackQueryHandler(button)); app.run_polling()
if __name__=='__main__': main()
