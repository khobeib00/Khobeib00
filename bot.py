# -*- coding: utf-8 -*-
import os
import json
import random
from threading import Thread, Lock
import chess
import telebot
from flask import Flask
from telebot import types

# ==========================================
# 1. Configuration & Setup
# ==========================================
# التوكن الخاص بك مدمج بالكامل هنا
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8884224118:AAGfcnzmOJrYjElWslvhO5rAmJAd42zedkk")
OWNER_ID = int(os.environ.get("OWNER_ID", "0"))

bot = telebot.TeleBot(BOT_TOKEN)

# ==========================================
# 2. Flask Web Server (To keep Render alive)
# ==========================================
app = Flask('')

@app.route('/')
def home():
    return "Chess Bot is Running 24/7 Safely!"

def run_web_server():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

Thread(target=run_web_server, daemon=True).start()

# ==========================================
# 3. Data Storage (JSON)
# ==========================================
DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)
_lock = Lock()

def _path(name: str) -> str:
    return os.path.join(DATA_DIR, f"{name}.json")

def load_json(name: str, default):
    p = _path(name)
    if not os.path.exists(p):
        return default
    try:
        with open(p, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default

def save_json(name: str, data):
    with _lock:
        p = _path(name)
        with open(p, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

users_db = load_json("users", {})      
admins_db = load_json("admins", [])    
games_db = {}                          

# ==========================================
# 4. Custom Welcome Message & Texts
# ==========================================
WELCOME_MESSAGE = (
    "↳︎𝟔𝟒 𝐒𝐪𝐮𝐚𝐫𝐞𝐬... 𝐄𝐧𝐝𝐥𝐞𝐬𝐬 𝐏𝐨𝐬𝐬𝐢𝐛𝐢𝐥𝐢𝐭𝐢𝐞𝐬! ✨•\n"
    "↳︎𝐄𝐯𝐞𝐫𝐲 𝐦𝐨𝐯𝐞 𝐢𝐬 𝐚 𝐝𝐞𝐜𝐢𝐬𝐢𝐨𝐧, 𝐞𝐯𝐞𝐫𝐲 𝐦𝐚𝐭𝐜𝐡 𝐚 𝐛𝐚𝐭𝐭𝐥𝐞 𝐨𝐟 𝐦𝐢𝐧𝐝𝐬•\n"
    "↳︎𝐅𝐫𝐨𝐦 𝐭𝐡𝐞 𝐟𝐢𝐫𝐬𝐭 𝐦𝐨𝐯𝐞 𝐭𝐨 𝐭𝐡𝐞 𝐟𝐢𝐧𝐚𝐥 𝐜𝐡𝐞𝐜𝐤𝐦𝐚𝐭𝐞... 𝐰𝐫𝐢𝐭𝐞 𝐲𝐨𝐮𝐫 𝐨𝐰𝐧 𝐥𝐞𝐠𝐞𝐧𝐝•\n"
    "↳︎𝐀𝐫𝐞 𝐲𝐨𝐮 𝐭𝐡𝐞 𝐧𝐞𝐱𝐭 𝐜𝐡𝐚𝐦𝐩𝐢𝐨𝐧?!!•\n\n"
    "↳︎𝐃𝐞𝐯 @hihi_jl | @khobeib00"
)

HELP_TEXT = (
    "♟ **دليل تعليمات لعبة الشطرنج** ♟\n\n"
    "**🎮 أنماط اللعب:**\n"
    "• **اللعب ضد البوت:** اضغط `🤖 اللعب ضد البوت` للبدء فوراً.\n"
    "• **تحدي صديق:** اضغط `⚔️ تحدي صديق` وأرسل الرابط لشخص آخر.\n\n"
    "**🎯 كيفية التحريك والأكل:**\n"
    "1. اضغط على قطعة من قطاعك لتحديدها (تظهر بإيموجي 🎯).\n"
    "2. اضغط على المربع المطلوب للتحريك أو لأكل قطعة الخصم.\n\n"
    "**🏆 نظام النقاط والمتصدرين:**\n"
    "• **الفوز:** يحسب لك **⭐ +10 نقاط**.\n"
    "• **الخسارة:** تمنحك **⭐ +3 نقاط** لمشاركتك.\n"
    "• اعرض القائمة بالأمر `/top`.\n\n"
    "**⚙️ الأوامر السريعة:**\n"
    "• `/cancel` أو `/stop` — لإلغاء اللعبة الحالية.\n"
    "• `/lang` — لتغيير لغة البوت (عربي/إنجليزي).\n"
    "• `/help_chess` — لعرض هذه التعليمات."
)

TEXTS = {
    "ar": {
        "welcome": WELCOME_MESSAGE,
        "btn_vs_bot": "🤖 اللعب ضد البوت",
        "btn_vs_friend": "⚔️ تحدي صديق",
        "btn_leaderboard": "🏆 قائمة المتصدرين",
        "btn_lang": "🌐 تغيير اللغة",
        "btn_help": "📖 التعليمات",
        "choose_mode": "اختر نمط اللعب للبدء:",
        "invite_friend_msg": "أرسل هذا الرابط لصديقك لتحديه في اللعبة:\n\nhttps://t.me/{}?start=game_{}",
        "leaderboard_title": "🏆 **قائمة أفضل اللاعبين حسب النقاط:**\n\n",
        "no_players": "لا يوجد لاعبون مسجلون بعد.",
        "admin_only": "⚠️ هذا الأمر خاص بمالك البوت فقط.",
        "admin_added": "✅ تم رفع المستخدم كـ مساعد بنجاح.",
        "admin_removed": "✅ تم تنزيل المساعد بنجاح."
    },
    "en": {
        "welcome": WELCOME_MESSAGE,
        "btn_vs_bot": "🤖 Play vs Bot",
        "btn_vs_friend": "⚔️ Challenge a Friend",
        "btn_leaderboard": "🏆 Leaderboard",
        "btn_lang": "🌐 Change Language",
        "btn_help": "📖 Instructions",
        "choose_mode": "Choose game mode to start:",
        "invite_friend_msg": "Send this link to your friend to challenge them:\n\nhttps://t.me/{}?start=game_{}",
        "leaderboard_title": "🏆 **Top Ranked Players by Points:**\n\n",
        "no_players": "No ranked players yet.",
        "admin_only": "⚠️ This command is restricted to the Owner.",
        "admin_added": "✅ User successfully added as admin.",
        "admin_removed": "✅ Admin successfully removed."
    }
}

def get_user_lang(user_id):
    uid = str(user_id)
    if uid in users_db and "lang" in users_db[uid]:
        return users_db[uid]["lang"]
    return "ar"

def get_txt(user_id, key):
    lang = get_user_lang(user_id)
    return TEXTS[lang].get(key, TEXTS["ar"].get(key, ""))

def register_user(user):
    uid = str(user.id)
    username = f"@{user.username}" if user.username else user.first_name
    if uid not in users_db:
        users_db[uid] = {
            "name": username,
            "lang": "ar",
            "points": 0,
            "wins": 0,
            "losses": 0
        }
        save_json("users", users_db)

def add_points(user_id, is_win=True):
    uid = str(user_id)
    if uid in users_db:
        if is_win:
            users_db[uid]["points"] = users_db[uid].get("points", 0) + 10
            users_db[uid]["wins"] = users_db[uid].get("wins", 0) + 1
        else:
            users_db[uid]["points"] = users_db[uid].get("points", 0) + 3
            users_db[uid]["losses"] = users_db[uid].get("losses", 0) + 1
        save_json("users", users_db)

def is_group_admin_or_owner(chat_id, user_id):
    if user_id == OWNER_ID or user_id in admins_db:
        return True
    try:
        member = bot.get_chat_member(chat_id, user_id)
        if member.status in ['creator', 'administrator']:
            return True
    except Exception:
        pass
    return False

# ==========================================
# 5. UI Helpers (Board Rendering)
# ==========================================
PIECES = {
    'r': '♜', 'n': '♞', 'b': '♝', 'q': '♛', 'k': '♚', 'p': '♟',
    'R': '♖', 'N': '♘', 'B': '♗', 'Q': '♕', 'K': '♔', 'P': '♙',
    '.': '▫️'
}

def render_board_markup(board, selected_sq=None):
    markup = types.InlineKeyboardMarkup(row_width=8)
    buttons = []
    for sq in range(64):
        rank = 7 - (sq // 8)
        file = sq % 8
        square_id = chess.square(file, rank)
        piece = board.piece_at(square_id)
        
        symbol = PIECES.get(piece.symbol(), '▫️') if piece else '▫️'
        if selected_sq == square_id:
            symbol = "🎯"
            
        btn = types.InlineKeyboardButton(text=symbol, callback_data=f"sq_{square_id}")
        buttons.append(btn)
        
        if len(buttons) == 8:
            markup.row(*buttons)
            buttons = []
    return markup

# ==========================================
# 6. Handlers & Commands
# ==========================================
@bot.message_handler(commands=['start', 'play', 'start_game'])
def cmd_start(message):
    register_user(message.from_user)
    uid = message.from_user.id
    
    args = message.text.split()
    if len(args) > 1 and args[1].startswith("game_"):
        host_id = args[1].replace("game_", "")
        if host_id != str(uid):
            start_pvp_game(message.chat.id, int(host_id), uid)
            return

    msg_text = f"{get_txt(uid, 'welcome')}\n\n{get_txt(uid, 'choose_mode')}"
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton(get_txt(uid, "btn_vs_bot"), callback_data="mode_bot"),
        types.InlineKeyboardButton(get_txt(uid, "btn_vs_friend"), callback_data="mode_friend"),
        types.InlineKeyboardButton(get_txt(uid, "btn_leaderboard"), callback_data="view_leaderboard"),
        types.InlineKeyboardButton(get_txt(uid, "btn_help"), callback_data="view_help"),
        types.InlineKeyboardButton(get_txt(uid, "btn_lang"), callback_data="toggle_lang")
    )
    bot.send_message(message.chat.id, msg_text, reply_markup=markup)

@bot.message_handler(commands=['help', 'help_chess', 'تعليمات', 'التعليمات'])
def cmd_help(message):
    bot.send_message(message.chat.id, HELP_TEXT, parse_mode="Markdown")

@bot.message_handler(commands=['cancel', 'stop', 'القاء', 'الغاء'])
def cmd_cancel_game(message):
    uid = message.from_user.id
    chat_id = message.chat.id
    
    game_to_cancel = None
    for gid, gdata in list(games_db.items()):
        if gdata.get("chat_id") == chat_id or gdata["white"] == uid or gdata["black"] == uid:
            game_to_cancel = (gid, gdata)
            break

    if not game_to_cancel:
        bot.reply_to(message, "⚠️ لا توجد لعبة قائمة حالياً لإلغائها.")
        return

    gid, gdata = game_to_cancel
    is_player = (uid == gdata["white"] or uid == gdata["black"])
    is_admin = is_group_admin_or_owner(chat_id, uid)

    if is_player or is_admin:
        del games_db[gid]
        canceler_name = f"@{message.from_user.username}" if message.from_user.username else message.from_user.first_name
        role_label = "بواسطة مشرف/مالك" if is_admin and not is_player else "بواسطة اللاعب"
        bot.send_message(chat_id, f"🚫 **تم إلغاء اللعبة بنجاح** {role_label} ({canceler_name}).")
    else:
        bot.reply_to(message, "⚠️ لا تملك صلاحية إلغاء هذه اللعبة. الإلغاء متاح فقط للاعب المشارك أو للمشرفين والمدراء.")

@bot.message_handler(commands=['language', 'lang'])
def cmd_language(message):
    uid = str(message.from_user.id)
    register_user(message.from_user)
    users_db[uid]["lang"] = "en" if users_db[uid].get("lang") == "ar" else "ar"
    save_json("users", users_db)
    bot.reply_to(message, "✅ Language updated successfully / تم تغيير اللغة بنجاح!")

@bot.message_handler(commands=['leaderboard', 'top'])
def cmd_leaderboard(message):
    show_leaderboard(message.chat.id, message.from_user.id)

def show_leaderboard(chat_id, user_id):
    sorted_users = sorted(users_db.items(), key=lambda x: x[1].get("points", 0), reverse=True)[:10]
    if not sorted_users:
        bot.send_message(chat_id, get_txt(user_id, "no_players"))
        return
        
    text = get_txt(user_id, "leaderboard_title")
    medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
    for idx, (uid, udata) in enumerate(sorted_users):
        medal = medals[idx] if idx < len(medals) else "👤"
        text += f"{medal} **{udata.get('name', 'Player')}** — ⭐ `{udata.get('points', 0)} نقطة` (فوز: {udata.get('wins', 0)} / خسارة: {udata.get('losses', 0)})\n"
    
    bot.send_message(chat_id, text, parse_mode="Markdown")

@bot.message_handler(commands=['addadmin'])
def cmd_add_admin(message):
    if message.from_user.id != OWNER_ID:
        bot.reply_to(message, get_txt(message.from_user.id, "admin_only"))
        return
    try:
        new_admin = int(message.text.split()[1])
        if new_admin not in admins_db:
            admins_db.append(new_admin)
            save_json("admins", admins_db)
        bot.reply_to(message, get_txt(message.from_user.id, "admin_added"))
    except Exception:
        bot.reply_to(message, "Usage: `/addadmin <USER_ID>`", parse_mode="Markdown")

@bot.message_handler(commands=['removeadmin'])
def cmd_remove_admin(message):
    if message.from_user.id != OWNER_ID:
        bot.reply_to(message, get_txt(message.from_user.id, "admin_only"))
        return
    try:
        target_admin = int(message.text.split()[1])
        if target_admin in admins_db:
            admins_db.remove(target_admin)
            save_json("admins", admins_db)
        bot.reply_to(message, get_txt(message.from_user.id, "admin_removed"))
    except Exception:
        bot.reply_to(message, "Usage: `/removeadmin <USER_ID>`", parse_mode="Markdown")

# ==========================================
# 7. Callbacks & Game Engine
# ==========================================
@bot.callback_query_handler(func=lambda call: True)
def handle_callbacks(call):
    uid = call.from_user.id
    register_user(call.from_user)

    if call.data == "toggle_lang":
        users_db[str(uid)]["lang"] = "en" if get_user_lang(uid) == "ar" else "ar"
        save_json("users", users_db)
        bot.answer_callback_query(call.id, "Language changed!")
        cmd_start(call.message)

    elif call.data == "view_leaderboard":
        show_leaderboard(call.message.chat.id, uid)
        bot.answer_callback_query(call.id)

    elif call.data == "view_help":
        cmd_help(call.message)
        bot.answer_callback_query(call.id)

    elif call.data == "mode_bot":
        start_bot_game(call.message.chat.id, uid, call.message.message_id)

    elif call.data == "mode_friend":
        bot_username = bot.get_me().username
        link = get_txt(uid, "invite_friend_msg").format(bot_username, uid)
        bot.send_message(call.message.chat.id, link)
        bot.answer_callback_query(call.id)

    elif call.data.startswith("sq_"):
        handle_square_click(call)

def start_bot_game(chat_id, user_id, message_id=None):
    game_id = f"bot_{user_id}"
    games_db[game_id] = {
        "board": chess.Board(),
        "white": user_id,
        "black": "BOT",
        "selected": None,
        "turn": user_id,
        "chat_id": chat_id
    }
    board = games_db[game_id]["board"]
    markup = render_board_markup(board)
    user_handle = users_db.get(str(user_id), {}).get("name", "اللاعب")
    txt = f"🎮 **بدأت المباراة ضد الذكاء الاصطناعي!**\n\n👤 **دور:** {user_handle} (الأبيض)\n\nℹ️ يمكنك إلغاء اللعبة بـ `/cancel`"
    
    if message_id:
        bot.edit_message_text(txt, chat_id, message_id, reply_markup=markup, parse_mode="Markdown")
    else:
        bot.send_message(chat_id, txt, reply_markup=markup, parse_mode="Markdown")

def start_pvp_game(chat_id, white_id, black_id):
    game_id = f"pvp_{white_id}_{black_id}"
    games_db[game_id] = {
        "board": chess.Board(),
        "white": white_id,
        "black": black_id,
        "selected": None,
        "turn": white_id,
        "chat_id": chat_id
    }
    board = games_db[game_id]["board"]
    markup = render_board_markup(board)
    white_handle = users_db.get(str(white_id), {}).get("name", "اللاعب 1")
    bot.send_message(chat_id, f"⚔️ **بدأت المباراة!**\n\n👤 **دور:** {white_handle} (الأبيض)\n\nℹ️ يمكن إلغاء اللعبة بواسطة اللاعبين أو المشرفين عبر `/cancel`", reply_markup=markup, parse_mode="Markdown")

def handle_square_click(call):
    sq = int(call.data.split("_")[1])
    uid = call.from_user.id
    user_handle = users_db.get(str(uid), {}).get("name", f"@{call.from_user.username}" if call.from_user.username else call.from_user.first_name)

    game = None
    game_id = None
    for gid, gdata in games_db.items():
        if gdata["white"] == uid or gdata["black"] == uid:
            game = gdata
            game_id = gid
            break
            
    if not game:
        bot.answer_callback_query(call.id, "لا توجد لعبة نشطة حالياً.")
        return

    board = game["board"]
    selected = game["selected"]

    if selected is None:
        piece = board.piece_at(sq)
        if piece and ((game["turn"] == game["white"] and piece.color == chess.WHITE) or
                       (game["turn"] == game["black"] and piece.color == chess.BLACK)):
            game["selected"] = sq
            markup = render_board_markup(board, selected_sq=sq)
            bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=markup)
            bot.answer_callback_query(call.id, f"تم تحديد الخانة {chess.square_name(sq)}")
    else:
        move = chess.Move(selected, sq)
        if chess.Piece(chess.PAWN, board.turn) in [board.piece_at(selected)] and (sq // 8 in [0, 7]):
            move.promotion = chess.QUEEN

        if move in board.legal_moves:
            is_capture = board.is_capture(move)
            
            board.push(move)
            game["selected"] = None
            
            from_sq_name = chess.square_name(selected)
            to_sq_name = chess.square_name(sq)
            
            if is_capture:
                status_msg = f"⚔️ **قتال هجومي!**\nتم أكل قطعة بواسطة {user_handle} في الخانة `{to_sq_name}`"
            else:
                status_msg = f"♟ **نقلة بواسطة {user_handle}**\nمن `{from_sq_name}` إلى `{to_sq_name}`"

            if board.is_checkmate():
                add_points(uid, is_win=True)
                bot.edit_message_text(f"🎉 **كش مات! فاز اللاعب {user_handle}!**\nحصلت على ⭐ +10 نقاط!", call.message.chat.id, call.message.message_id)
                del games_db[game_id]
                return

            # AI Turn Logic
            if game["black"] == "BOT":
                legal_moves = list(board.legal_moves)
                if legal_moves:
                    ai_move = random.choice(legal_moves)
                    ai_capture = board.is_capture(ai_move)
                    board.push(ai_move)
                    
                    if ai_capture:
                        status_msg += f"\n\n⚔️ **الذكاء الاصطناعي أكل قطعتك!**"
                    else:
                        status_msg += f"\n\n🤖 **الذكاء الاصطناعي حرك من `{chess.square_name(ai_move.from_square)}` إلى `{chess.square_name(ai_move.to_square)}`**"

                if board.is_checkmate():
                    add_points(uid, is_win=False)
                    bot.edit_message_text("🤖 **فاز الذكاء الاصطناعي! هاردلك.**\nحصلت على ⭐ +3 نقاط لمشاركتك في المباراة!", call.message.chat.id, call.message.message_id)
                    del games_db[game_id]
                    return

            markup = render_board_markup(board)
            bot.edit_message_text(status_msg, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")
            bot.answer_callback_query(call.id)
        else:
            game["selected"] = None
            markup = render_board_markup(board)
            bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=markup)
            bot.answer_callback_query(call.id, "نقلة غير قانونية!")

# ==========================================
# 8. Start Bot Engine
# ==========================================
if __name__ == "__main__":
    print("Bot is starting...")
    bot.infinity_polling(skip_pending=True)

