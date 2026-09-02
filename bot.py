# -*- coding: utf-8 -*-
import os
import json
import random
import uuid
from threading import Thread, Lock
import chess
import telebot
from flask import Flask
from telebot import types

# ==========================================
# 1. Configuration & Setup
# ==========================================
BOT_TOKEN = os.environ.get("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
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
pending_challenges = {} 
group_challenges = {}  # للتحديات الخاصة بالمجموعات
games_db = {}                          

# ==========================================
# 4. Helper Functions & Permissions
# ==========================================
WELCOME_MESSAGE = (
    "↳︎𝟔𝟒 𝐒𝐪𝐮𝐚𝐫𝐞𝐬... 𝐄𝐧𝐝𝐥𝐞𝐬𝐬 𝐏𝐨𝐬𝐬𝐢𝐛𝐢𝐥𝐢𝐭𝐢𝐞𝐬! ✨•\n"
    "↳︎𝐄𝐯𝐞𝐫𝐲 𝐦𝐨𝐯𝐞 𝐢𝐬 𝐚 𝐝𝐞𝐜𝐢𝐬𝐢𝐨𝐧, 𝐞𝐯𝐞𝐫𝐲 𝐦𝐚𝐭𝐜𝐡 𝐚 𝐛𝐚𝐭𝐭𝐥𝐞 𝐨𝐟 𝐦𝐢𝐧𝐝𝐬•\n"
    "↳︎𝐅𝐫𝐨𝐦 𝐭𝐡𝐞 𝐟𝐢𝐫𝐬𝐭 𝐦𝐨𝐯𝐞 𝐭𝐨 𝐭𝐡𝐞 𝐟𝐢𝐧𝐚𝐥 𝐜𝐡𝐞𝐜𝐤𝐦𝐚𝐭𝐞... 𝐰𝐫𝐢𝐭𝐞 𝐲𝐨𝐮𝐫 𝐨𝐰𝐧 𝐥𝐞𝐠𝐞𝐧𝐝•\n"
    "↳︎𝐀𝐫𝐞 𝐲𝐨𝐮 𝐭𝐡𝐞 𝐧𝐞𝐱𝐭 𝐜𝐡𝐚𝐦𝐩𝐢𝐨𝐧?!!•\n\n"
    "↳︎𝐃𝐞𝐯 @hihi_jl | @khobeib00"
)

def get_user_lang(user_id):
    uid = str(user_id)
    return users_db.get(uid, {}).get("lang", "ar")

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

def is_owner(user_id):
    return user_id == OWNER_ID

def is_admin_or_owner(user_id):
    return user_id == OWNER_ID or user_id in admins_db

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
# 6. Command Handlers
# ==========================================
@bot.message_handler(commands=['start', 'play'])
def cmd_start(message):
    register_user(message.from_user)
    uid = message.from_user.id
    
    args = message.text.split()
    if len(args) > 1 and args[1].startswith("game_"):
        challenge_id = args[1].replace("game_", "")
        if challenge_id in pending_challenges:
            host_id = pending_challenges[challenge_id]["host_id"]
            if host_id != uid:
                del pending_challenges[challenge_id]
                start_pvp_game(host_id, uid)
                return
            else:
                bot.reply_to(message, "⚠️ لا يمكنك قبول تحدي أنشأته بنفسك!")
                return
        else:
            bot.reply_to(message, "⚠️ رابط التحدي غير صالح أو تم استخدامه.")
            return

    msg_text = f"{WELCOME_MESSAGE}\n\nاختر نمط اللعب للبدء:"
    markup = types.InlineKeyboardMarkup(row_width=2)
    
    # 6 خانات تفاعلية
    markup.add(
        types.InlineKeyboardButton("🤖 اللعب ضد البوت", callback_data="mode_bot"),
        types.InlineKeyboardButton("⚔️ تحدي صديق", callback_data="mode_friend"),
        types.InlineKeyboardButton("👥 اللعب في المجموعة", callback_data="mode_group"),
        types.InlineKeyboardButton("🏆 المتصدرين", callback_data="view_leaderboard"),
        types.InlineKeyboardButton("📖 التعليمات والأوامر", callback_data="view_help"),
        types.InlineKeyboardButton("🌐 تغيير اللغة", callback_data="toggle_lang")
    )
    bot.send_message(message.chat.id, msg_text, reply_markup=markup)

@bot.message_handler(commands=['help', 'التعليمات', 'اوامري'])
def cmd_help(message):
    uid = message.from_user.id
    
    help_msg = (
        "♟ **أوامر وبوت الشطرنج العامة:**\n\n"
        "• `/start` — تشغيل البوت وعرض القائمة الرئيسية.\n"
        "• `/top` أو `/leaderboard` — عرض قائمة المتصدرين.\n"
        "• `/cancel` أو `/stop` — إلغاء اللعبة الحالية التي تخوضها.\n"
        "• `/lang` — تغيير لغة البوت (عربي/إنجليزي).\n"
        "• `/help` — عرض هذه القائمة التعليمية.\n"
    )

    if is_admin_or_owner(uid):
        help_msg += (
            "\n🛠 **أوامر المساعدين (الإشراف):**\n"
            "• `/reset_game <ID>` — إنهاء مباراة قائمة لأي لاعب بالقوة.\n"
            "• `/stats` — عرض إحصائيات سريعة عن مستخدمي البوت والألعاب النشطة.\n"
        )

    if is_owner(uid):
        help_msg += (
            "\n👑 **أوامر المالك الحصرية:**\n"
            "• `/addadmin <ID>` — تعيين مساعد جديد للبوت.\n"
            "• `/removeadmin <ID>` — تنزيل مساعد من الصلاحيات.\n"
            "• `/admins` — عرض قائمة المساعدين المعينين حالياً.\n"
            "• `/broadcast <الرسالة>` — إرسال إشعار جماعي لجميع مستخدمي البوت.\n"
        )

    bot.send_message(message.chat.id, help_msg, parse_mode="Markdown")

# ------------------------------------------
# 👑 أوامر المالك الحصرية (Owner Only)
# ------------------------------------------
@bot.message_handler(commands=['addadmin'])
def cmd_add_admin(message):
    if not is_owner(message.from_user.id):
        bot.reply_to(message, "⚠️ هذا الأمر خاص بمالك البوت فقط.")
        return
    try:
        new_admin = int(message.text.split()[1])
        if new_admin not in admins_db:
            admins_db.append(new_admin)
            save_json("admins", admins_db)
            bot.reply_to(message, f"✅ تم تعيين المستخدم `{new_admin}` كـ مساعد بنجاح.", parse_mode="Markdown")
        else:
            bot.reply_to(message, "⚠️ هذا المستخدم موجود بالفعل كـ مساعد.")
    except Exception:
        bot.reply_to(message, "الاستخدام الصحيح: `/addadmin <USER_ID>`", parse_mode="Markdown")

@bot.message_handler(commands=['removeadmin'])
def cmd_remove_admin(message):
    if not is_owner(message.from_user.id):
        bot.reply_to(message, "⚠️ هذا الأمر خاص بمالك البوت فقط.")
        return
    try:
        target_admin = int(message.text.split()[1])
        if target_admin in admins_db:
            admins_db.remove(target_admin)
            save_json("admins", admins_db)
            bot.reply_to(message, f"✅ تم تنزيل المساعد `{target_admin}` بنجاح.", parse_mode="Markdown")
        else:
            bot.reply_to(message, "⚠️ هذا المستخدم ليس مساعداً في البوت.")
    except Exception:
        bot.reply_to(message, "الاستخدام الصحيح: `/removeadmin <USER_ID>`", parse_mode="Markdown")

@bot.message_handler(commands=['admins'])
def cmd_list_admins(message):
    if not is_owner(message.from_user.id):
        bot.reply_to(message, "⚠️ هذا الأمر خاص بمالك البوت فقط.")
        return
    if not admins_db:
        bot.reply_to(message, "📋 لا يوجد مساعدون مضافون حالياً.")
        return
    
    text = "📋 **قائمة المساعدين المعتمدين:**\n\n"
    for aid in admins_db:
        text += f"• ID: `{aid}`\n"
    bot.reply_to(message, text, parse_mode="Markdown")

@bot.message_handler(commands=['broadcast'])
def cmd_broadcast(message):
    if not is_owner(message.from_user.id):
        bot.reply_to(message, "⚠️ هذا الأمر خاص بمالك البوت فقط.")
        return
    
    msg_text = message.text.replace("/broadcast", "").strip()
    if not msg_text:
        bot.reply_to(message, "أدخل الرسالة المراد إرسالها للجميع:\n`/broadcast نص الرسالة`", parse_mode="Markdown")
        return

    count = 0
    for uid in list(users_db.keys()):
        try:
            bot.send_message(int(uid), f"📢 **تنبيه من المالك:**\n\n{msg_text}", parse_mode="Markdown")
            count += 1
        except Exception:
            pass
    bot.reply_to(message, f"✅ تم إرسال الإذاعة إلى {count} مستخدم بنجاح.")

# ------------------------------------------
# 🛠 أوامر المساعدين والمالك (Admins & Owner)
# ------------------------------------------
@bot.message_handler(commands=['reset_game'])
def cmd_force_reset_game(message):
    if not is_admin_or_owner(message.from_user.id):
        bot.reply_to(message, "⚠️ هذا الأمر خاص بالمساعدين والمالك فقط.")
        return
    
    args = message.text.split()
    if len(args) < 2:
        bot.reply_to(message, "أرسل معرف المستخدم لإلغاء لعبته الحالية:\n`/reset_game <USER_ID>`", parse_mode="Markdown")
        return

    try:
        target_uid = int(args[1])
        game_to_cancel = None
        for gid, gdata in list(games_db.items()):
            if gdata["white"] == target_uid or gdata["black"] == target_uid:
                game_to_cancel = gid
                break

        if game_to_cancel:
            del games_db[game_to_cancel]
            bot.reply_to(message, f"✅ تم إغلاق وإنهاء مباراة المستخدم `{target_uid}` بنجاح.", parse_mode="Markdown")
        else:
            bot.reply_to(message, "❌ هذا المستخدم ليس لديه مباراة قائمة حالياً.")
    except Exception:
        bot.reply_to(message, "يرجى كتابة المعرف بشكل صحيح كأرقام.")

@bot.message_handler(commands=['stats'])
def cmd_bot_stats(message):
    if not is_admin_or_owner(message.from_user.id):
        bot.reply_to(message, "⚠️ هذا الأمر خاص بالمساعدين والمالك فقط.")
        return
    
    total_users = len(users_db)
    active_games = len(games_db)
    pending_links = len(pending_challenges)
    
    stats_msg = (
        "📊 **إحصائيات البوت الحالية:**\n\n"
        f"• **إجمالي المسجلين:** `{total_users}` مستخدم\n"
        f"• **المباريات القائمة حالياً:** `{active_games}` مباراة\n"
        f"• **روابط التحدي المعلقة:** `{pending_links}` رابط\n"
    )
    bot.reply_to(message, stats_msg, parse_mode="Markdown")

# ------------------------------------------
# 👤 الأوامر العامة لكل المستخدمين (Public)
# ------------------------------------------
@bot.message_handler(commands=['cancel', 'stop'])
def cmd_cancel_game(message):
    uid = message.from_user.id
    game_to_cancel = None
    for gid, gdata in list(games_db.items()):
        if gdata["white"] == uid or gdata["black"] == uid:
            game_to_cancel = (gid, gdata)
            break

    if not game_to_cancel:
        bot.reply_to(message, "⚠️ لا توجد لعبة قائمة حالياً لإلغائها.")
        return

    gid, gdata = game_to_cancel
    canceler_name = f"@{message.from_user.username}" if message.from_user.username else message.from_user.first_name
    cancel_msg = f"🚫 **تم إلغاء اللعبة بواسطة اللاعب** ({canceler_name})."
    
    for p_id in [gdata["white"], gdata["black"]]:
        if p_id != "BOT":
            try:
                bot.send_message(p_id, cancel_msg)
            except Exception:
                pass
                
    del games_db[gid]

@bot.message_handler(commands=['leaderboard', 'top'])
def cmd_leaderboard(message):
    sorted_users = sorted(users_db.items(), key=lambda x: x[1].get("points", 0), reverse=True)[:10]
    if not sorted_users:
        bot.send_message(message.chat.id, "لا يوجد لاعبون مسجلون بعد.")
        return
        
    text = "🏆 **قائمة أفضل 10 لاعبين:**\n\n"
    medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
    for idx, (uid, udata) in enumerate(sorted_users):
        medal = medals[idx] if idx < len(medals) else "👤"
        text += f"{medal} **{udata.get('name', 'Player')}** — ⭐ `{udata.get('points', 0)} نقطة`\n"
    
    bot.send_message(message.chat.id, text, parse_mode="Markdown")

@bot.message_handler(commands=['lang', 'language'])
def cmd_language(message):
    uid = str(message.from_user.id)
    register_user(message.from_user)
    users_db[uid]["lang"] = "en" if users_db[uid].get("lang") == "ar" else "ar"
    save_json("users", users_db)
    bot.reply_to(message, "✅ تم تغيير لغة البوت بنجاح!")

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
        cmd_leaderboard(call.message)
        bot.answer_callback_query(call.id)

    elif call.data == "view_help":
        cmd_help(call.message)
        bot.answer_callback_query(call.id)

    elif call.data == "mode_bot":
        start_bot_game(call.message.chat.id, uid, call.message.message_id)

    elif call.data == "mode_friend":
        challenge_id = str(uuid.uuid4())[:8]
        pending_challenges[challenge_id] = {"host_id": uid}
        bot_username = bot.get_me().username
        link = f"أرسل هذا الرابط الفريد لصديقك لتحديه في اللعبة:\n\nhttps://t.me/{bot_username}?start=game_{challenge_id}"
        bot.send_message(call.message.chat.id, link)
        bot.answer_callback_query(call.id)

    elif call.data == "mode_group":
        # التأكد مما إذا كان الأمر تم استدعاؤه داخل مجموعة أو محادثة خاصة
        if call.message.chat.type in ['group', 'supergroup']:
            user_handle = users_db.get(str(uid), {}).get("name", call.from_user.first_name)
            challenge_id = f"grp_{call.message.chat.id}_{uid}"
            group_challenges[challenge_id] = {"host_id": uid}
            
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("⚔️ قبول التحدي والبدء", callback_data=f"join_grp_{challenge_id}"))
            
            txt = f"⚔️ **تحدي شطرنج جديد في المجموعة!**\n\nأنشأ {user_handle} تحدياً مفتوحاً. اضغط على الزر أدناه للانضمام واللعب ضد"
            bot.send_message(call.message.chat.id, txt, reply_markup=markup, parse_mode="Markdown")
            bot.answer_callback_query(call.id)
        else:
            bot.answer_callback_query(call.id, "⚠️ هذا الخيار مخصص للاستخدام داخل المجموعات فقط!", show_alert=True)

    elif call.data.startswith("join_grp_"):
        challenge_id = call.data.replace("join_grp_", "")
        if challenge_id in group_challenges:
            host_id = group_challenges[challenge_id]["host_id"]
            if host_id != uid:
                del group_challenges[challenge_id]
                start_pvp_game(host_id, uid, group_chat_id=call.message.chat.id)
                bot.answer_callback_query(call.id)
            else:
                bot.answer_callback_query(call.id, "⚠️ لا يمكنك قبول التحدي الذي أنشأته بنفسك!", show_alert=True)
        else:
            bot.answer_callback_query(call.id, "⚠️ التحدي انتهى أو تم قبوله بالفعل.", show_alert=True)

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
        "msg_ids": {}
    }
    board = games_db[game_id]["board"]
    markup = render_board_markup(board)
    user_handle = users_db.get(str(user_id), {}).get("name", "اللاعب")
    txt = f"🎮 **بدأت المباراة ضد الذكاء الاصطناعي!**\n\n👤 **دور:** {user_handle} (الأبيض)"
    
    if message_id:
        bot.edit_message_text(txt, chat_id, message_id, reply_markup=markup, parse_mode="Markdown")
        games_db[game_id]["msg_ids"][user_id] = message_id
    else:
        msg = bot.send_message(chat_id, txt, reply_markup=markup, parse_mode="Markdown")
        games_db[game_id]["msg_ids"][user_id] = msg.message_id

def start_pvp_game(white_id, black_id, group_chat_id=None):
    game_id = f"pvp_{white_id}_{black_id}"
    games_db[game_id] = {
        "board": chess.Board(),
        "white": white_id,
        "black": black_id,
        "selected": None,
        "turn": white_id,
        "msg_ids": {}
    }
    board = games_db[game_id]["board"]
    markup = render_board_markup(board)
    
    white_handle = users_db.get(str(white_id), {}).get("name", "اللاعب 1")
    black_handle = users_db.get(str(black_id), {}).get("name", "اللاعب 2")
    
    txt_white = f"⚔️ **بدأت المباراة!**\n\nأنت بالقطع البيضاء ضد {black_handle}.\n👤 **دور:** {white_handle}"
    txt_black = f"⚔️ **بدأت المباراة!**\n\nأنت بالقطع السوداء ضد {white_handle}.\n👤 **دور:** {white_handle}"

    if group_chat_id:
        txt_grp = f"⚔️ **بدأت المباراة داخل المجموعة!**\n\n⚪ الأبيض: {white_handle}\n⚫ الأسود: {black_handle}\n\n👤 **دور:** {white_handle}"
        msg_grp = bot.send_message(group_chat_id, txt_grp, reply_markup=markup, parse_mode="Markdown")
        games_db[game_id]["msg_ids"][white_id] = msg_grp.message_id
        games_db[game_id]["msg_ids"][black_id] = msg_grp.message_id
    else:
        msg1 = bot.send_message(white_id, txt_white, reply_markup=markup, parse_mode="Markdown")
        msg2 = bot.send_message(black_id, txt_black, reply_markup=markup, parse_mode="Markdown")
        games_db[game_id]["msg_ids"][white_id] = msg1.message_id
        games_db[game_id]["msg_ids"][black_id] = msg2.message_id

def update_game_ui(game_id, status_msg):
    game = games_db[game_id]
    board = game["board"]
    markup = render_board_markup(board)
    
    white_handle = users_db.get(str(game["white"]), {}).get("name", "اللاعب 1")
    black_handle = users_db.get(str(game["black"]), {}).get("name", "اللاعب 2") if game["black"] != "BOT" else "الذكاء الاصطناعي"
    
    current_turn_user = white_handle if game["turn"] == game["white"] else black_handle
    full_msg = f"{status_msg}\n\n👤 **دور:** {current_turn_user}"

    for p_id, m_id in game["msg_ids"].items():
        try:
            bot.edit_message_text(full_msg, chat_id=p_id, message_id=m_id, reply_markup=markup, parse_mode="Markdown")
        except Exception:
            pass

def handle_square_click(call):
    sq = int(call.data.split("_")[1])
    uid = call.from_user.id
    user_handle = users_db.get(str(uid), {}).get("name", call.from_user.first_name)

    game, game_id = None, None
    for gid, gdata in games_db.items():
        if gdata["white"] == uid or gdata["black"] == uid:
            game = gdata
            game_id = gid
            break
            
    if not game:
        bot.answer_callback_query(call.id, "لا توجد لعبة نشطة حالياً.")
        return

    if game["turn"] != uid:
        bot.answer_callback_query(call.id, "ليس دورك الآن! انتظر حركة الخصم.")
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
            
            status_msg = f"⚔️ **أكل قطعة!**" if is_capture else f"♟ **نقلة بواسطة {user_handle}**"
            next_turn = game["black"] if game["turn"] == game["white"] else game["white"]
            game["turn"] = next_turn

            if board.is_checkmate():
                add_points(uid, is_win=True)
                for p_id, m_id in game["msg_ids"].items():
                    try:
                        bot.edit_message_text(f"🎉 **كش مات! فاز اللاعب {user_handle}!**", chat_id=p_id, message_id=m_id)
                    except Exception:
                        pass
                del games_db[game_id]
                return

            if game["black"] == "BOT":
                legal_moves = list(board.legal_moves)
                if legal_moves:
                    ai_move = random.choice(legal_moves)
                    board.push(ai_move)
                game["turn"] = game["white"]

                if board.is_checkmate():
                    add_points(uid, is_win=False)
                    bot.edit_message_text("🤖 **فاز الذكاء الاصطناعي!**", call.message.chat.id, call.message.message_id)
                    del games_db[game_id]
                    return

            update_game_ui(game_id, status_msg)
            bot.answer_callback_query(call.id)
        else:
            game["selected"] = None
            markup = render_board_markup(board)
            bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=markup)
            bot.answer_callback_query(call.id, "نقلة غير قانونية!")

if __name__ == "__main__":
    print("Bot is starting...")
    bot.infinity_polling(skip_pending=True)

