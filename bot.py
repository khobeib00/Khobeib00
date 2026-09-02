# -*- coding: utf-8 -*-
import os
import json
import random
from threading import Thread, Lock
import chess
import telebot
from flask import Flask
from telebot import types

# ---------------------------------------------------------------------------
# 1) الإعدادات والتكوين (Config)
# ---------------------------------------------------------------------------
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8884224118:AAGfcnzmOJrYjElWslvhO5rAmJAd42zedkk")
OWNER_ID = int(os.environ.get("OWNER_ID", "0"))
REQUIRED_CHANNELS = ["chessprinecgame", "HFEE55_07"]
DEFAULT_ASSISTANTS = [8326588605]
DEFAULT_RATING = 1200

# ---------------------------------------------------------------------------
# 2) خادم ويب بسيط لإبقاء Render يعمل 24/7
# ---------------------------------------------------------------------------
app = Flask('')

@app.route('/')
def home():
    return "Chess Bot is Running 24/7 Safely!"

def run_web_server():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

Thread(target=run_web_server, daemon=True).start()

# ---------------------------------------------------------------------------
# 3) نظام التخزين المحلي (Storage)
# ---------------------------------------------------------------------------
DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)
_lock = Lock()

def _path(name: str) -> str:
    return os.path.join(DATA_DIR, f"{name}.json")

def load_data(name: str, default):
    path = _path(name)
    if not os.path.exists(path):
        save_data(name, default)
        return default
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        save_data(name, default)
        return default

def save_data(name: str, data) -> None:
    path = _path(name)
    tmp_path = path + ".tmp"
    with _lock:
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        os.replace(tmp_path, path)

# ---------------------------------------------------------------------------
# 4) إدارة المستخدمين والتصنيف (Users & Elo)
# ---------------------------------------------------------------------------
def get_user(user_id: int, name: str = "لاعب") -> dict:
    users = load_data("users", {})
    key = str(user_id)
    if key not in users:
        users[key] = {
            "name": name,
            "rating": DEFAULT_RATING,
            "wins": 0,
            "losses": 0,
            "draws": 0,
            "games": 0,
        }
        save_data("users", users)
    else:
        if name and users[key].get("name") != name:
            users[key]["name"] = name
            save_data("users", users)
    return users[key]

def calculate_elo(rating_a: int, rating_b: int, score_a: float, k: int = 32) -> int:
    expected_a = 1 / (1 + 10 ** ((rating_b - rating_a) / 400))
    new_rating_a = rating_a + k * (score_a - expected_a)
    return round(new_rating_a)

def apply_result(white_id: int, black_id: int, result: str) -> tuple:
    if white_id == 0 or black_id == 0:
        human_id = white_id or black_id
        is_white = white_id != 0
        get_user(human_id)
        opp_rating = DEFAULT_RATING
        if result == "draw":
            score = 0.5
        elif (result == "white" and is_white) or (result == "black" and not is_white):
            score = 1
        else:
            score = 0
        users = load_data("users", {})
        key = str(human_id)
        old = users[key]["rating"]
        new = calculate_elo(old, opp_rating, score)
        users[key]["rating"] = new
        users[key]["games"] += 1
        if score == 1:
            users[key]["wins"] += 1
        elif score == 0:
            users[key]["losses"] += 1
        else:
            users[key]["draws"] += 1
        save_data("users", users)
        return new - old, None

    users = load_data("users", {})
    wkey, bkey = str(white_id), str(black_id)
    get_user(white_id)
    get_user(black_id)
    users = load_data("users", {})

    w_old = users[wkey]["rating"]
    b_old = users[bkey]["rating"]

    if result == "draw":
        w_score, b_score = 0.5, 0.5
    elif result == "white":
        w_score, b_score = 1, 0
    else:
        w_score, b_score = 0, 1

    w_new = calculate_elo(w_old, b_old, w_score)
    b_new = calculate_elo(b_old, w_old, b_score)

    users[wkey]["rating"] = w_new
    users[bkey]["rating"] = b_new
    users[wkey]["games"] += 1
    users[bkey]["games"] += 1

    if result == "draw":
        users[wkey]["draws"] += 1
        users[bkey]["draws"] += 1
    elif result == "white":
        users[wkey]["wins"] += 1
        users[bkey]["losses"] += 1
    else:
        users[bkey]["wins"] += 1
        users[wkey]["losses"] += 1

    save_data("users", users)
    return w_new - w_old, b_new - b_old

def leaderboard(limit: int = 10) -> list:
    users = load_data("users", {})
    ranked = sorted(users.items(), key=lambda kv: kv[1]["rating"], reverse=True)
    return ranked[:limit]

def all_user_ids() -> list:
    users = load_data("users", {})
    return [int(uid) for uid in users.keys()]

def _ensure_assistants_loaded() -> list:
    assistants = load_data("assistants", None)
    if assistants is None:
        assistants = list(DEFAULT_ASSISTANTS)
        save_data("assistants", assistants)
    return assistants

def get_assistants() -> list:
    return _ensure_assistants_loaded()

def add_assistant(user_id: int) -> bool:
    assistants = _ensure_assistants_loaded()
    if user_id in assistants:
        return False
    assistants.append(user_id)
    save_data("assistants", assistants)
    return True

def remove_assistant(user_id: int) -> bool:
    assistants = _ensure_assistants_loaded()
    if user_id not in assistants:
        return False
    assistants.remove(user_id)
    save_data("assistants", assistants)
    return True

def is_owner(user_id: int) -> bool:
    return OWNER_ID != 0 and user_id == OWNER_ID

def is_assistant(user_id: int) -> bool:
    return user_id in _ensure_assistants_loaded()

def is_admin(user_id: int) -> bool:
    return is_owner(user_id) or is_assistant(user_id)

# ---------------------------------------------------------------------------
# 5) الاشتراك الإجباري (Subscription)
# ---------------------------------------------------------------------------
def get_missing_channels(bot, user_id: int, channels: list) -> list:
    missing = []
    for ch in channels:
        try:
            member = bot.get_chat_member(f"@{ch}", user_id)
            if member.status in ("left", "kicked"):
                missing.append(ch)
        except Exception:
            missing.append(ch)
    return missing

def subscription_markup(channels: list) -> types.InlineKeyboardMarkup:
    markup = types.InlineKeyboardMarkup(row_width=1)
    for ch in channels:
        markup.add(types.InlineKeyboardButton(f"📢 اشترك في القناة", url=f"https://t.me/{ch}"))
    markup.add(types.InlineKeyboardButton("✅ لقد اشتركت، تحقق الآن", callback_data="check_sub"))
    return markup

def subscription_text() -> str:
    return (
        "🔒 <b>عذراً، لاستخدام البوت يجب عليك الاشتراك في القنوات التالية أولاً:</b>\n\n"
        "بعد الاشتراك اضغط على زر «تحقق الآن» 👇"
    )

# ---------------------------------------------------------------------------
# 6) لعبة الشطرنج والذكاء الاصطناعي (Game Logic)
# ---------------------------------------------------------------------------
PIECES_MAP = {
    'r': '♜', 'n': '♞', 'b': '♝', 'q': '♛', 'k': '♚', 'p': '♟',
    'R': '♖', 'N': '♘', 'B': '♗', 'Q': '♕', 'K': '♔', 'P': '♙',
    '.': '▪️'
}

def create_board_text(board: chess.Board, extra_status: str = "") -> str:
    board_str = str(board)
    for k, v in PIECES_MAP.items():
        board_str = board_str.replace(k, v)

    lines = board_str.split('\n')
    formatted = "<b>  a  b  c  d  e  f  g  h</b>\n"
    for idx, line in enumerate(lines):
        formatted += f"<b>{8 - idx}</b> {line} <b>{8 - idx}</b>\n"
    formatted += "<b>  a  b  c  d  e  f  g  h</b>"

    if extra_status:
        formatted += f"\n\n{extra_status}"
    return formatted

def create_board_markup(board: chess.Board, selected: str = None) -> types.InlineKeyboardMarkup:
    markup = types.InlineKeyboardMarkup(row_width=8)
    buttons = []

    for square in chess.SQUARES_180:
        piece = board.piece_at(square)
        label = piece.unicode_symbol() if piece else " "
        sq_name = chess.square_name(square)
        if selected == sq_name:
            label = f"🔸{label}" if piece else "🔸"
        buttons.append(types.InlineKeyboardButton(text=label, callback_data=f"sq_{sq_name}"))

        if len(buttons) == 8:
            markup.row(*buttons)
            buttons = []

    return markup

def game_status_text(board: chess.Board) -> str:
    if board.is_checkmate():
        winner = "الأسود ⚫" if board.turn == chess.WHITE else "الأبيض ⚪"
        return f"🏆 <b>كش ملك! فاز {winner}</b>"
    if board.is_stalemate():
        return "🤝 <b>تعادل (Stalemate)</b>"
    if board.is_insufficient_material():
        return "🤝 <b>تعادل (قطع غير كافية)</b>"
    if board.can_claim_fifty_moves():
        return "🤝 <b>تعادل (قاعدة 50 نقلة)</b>"
    if board.can_claim_threefold_repetition():
        return "🤝 <b>تعادل (تكرار الوضعية 3 مرات)</b>"
    if board.is_check():
        turn = "الأبيض ⚪" if board.turn == chess.WHITE else "الأسود ⚫"
        return f"⚠️ <b>كش! دور {turn}</b>"
    return ""

def is_game_over(board: chess.Board) -> bool:
    return board.is_game_over()

def game_result(board: chess.Board) -> str:
    if board.is_checkmate():
        return "black" if board.turn == chess.WHITE else "white"
    return "draw"

def pick_ai_move(board: chess.Board) -> chess.Move:
    legal_moves = list(board.legal_moves)
    if not legal_moves:
        return None

    values = {chess.PAWN: 1, chess.KNIGHT: 3, chess.BISHOP: 3,
              chess.ROOK: 5, chess.QUEEN: 9, chess.KING: 0}

    mating_moves = []
    capture_moves = []

    for move in legal_moves:
        board.push(move)
        if board.is_checkmate():
            mating_moves.append(move)
        board.pop()

        if board.is_capture(move):
            captured = board.piece_at(move.to_square)
            score = values.get(captured.piece_type, 0) if captured else 0
            capture_moves.append((score, move))

    if mating_moves:
        return random.choice(mating_moves)

    if capture_moves:
        capture_moves.sort(key=lambda x: x[0], reverse=True)
        best_score = capture_moves[0][0]
        best_moves = [m for s, m in capture_moves if s == best_score]
        return random.choice(best_moves)

    return random.choice(legal_moves)

# ---------------------------------------------------------------------------
# 7) إعداد المحركات وأوامر البوت (Main Bot Setup)
# ---------------------------------------------------------------------------
bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")
games = {}

HELP_TEXT = (
    "♟️ <b>أوامر بوت الشطرنج</b>\n\n"
    "🔹 /start - بدء استخدام البوت\n"
    "🔹 /newgame - لعبة جديدة ضد الذكاء الاصطناعي 🤖\n"
    "🔹 /challenge - تحدي لاعب آخر (بالرد على رسالته)\n"
    "🔹 /resign - الاستسلام من المباراة الحالية\n"
    "🔹 /rating - عرض تصنيفك الحالي\n"
    "🏆 /leaderboard - قائمة أفضل 10 لاعبين\n"
    "🔹 /help - عرض هذه القائمة\n"
)

ADMIN_HELP_TEXT = (
    "\n👑 <b>أوامر خاصة بالمالك والمساعدين</b>\n\n"
    "🔸 /addassistant [آيدي] - إضافة مساعد جديد\n"
    "🔸 /removeassistant [آيدي] - إزالة مساعد\n"
    "🔸 /assistants - عرض قائمة المساعدين\n"
    "🔸 /stats - إحصائيات البوت\n"
    "🔸 /broadcast [رسالة] - إذاعة رسالة للجميع\n"
)

def require_subscription(user_id: int) -> bool:
    if is_admin(user_id):
        return True
    missing = get_missing_channels(bot, user_id, REQUIRED_CHANNELS)
    return len(missing) == 0

def send_subscription_prompt(chat_id: int):
    bot.send_message(
        chat_id,
        subscription_text(),
        reply_markup=subscription_markup(REQUIRED_CHANNELS),
    )

def main_menu_markup() -> types.InlineKeyboardMarkup:
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(types.InlineKeyboardButton("🤖 لعب ضد الذكاء الاصطناعي", callback_data="new_ai"))
    markup.add(types.InlineKeyboardButton("🏆 لوحة المتصدرين", callback_data="show_leaderboard"))
    markup.add(types.InlineKeyboardButton("📊 تصنيفي", callback_data="show_rating"))
    return markup

def start_ai_game(chat_id: int, user_id: int, user_name: str):
    board = chess.Board()
    get_user(user_id, user_name)
    games[chat_id] = {
        "board": board,
        "selected": None,
        "white_id": user_id,
        "black_id": 0,
        "white_name": user_name,
        "black_name": "الذكاء الاصطناعي 🤖",
        "mode": "ai",
    }
    send_board(chat_id, header="♟️ <b>بدأت لعبة جديدة ضد الذكاء الاصطناعي!</b>\nأنت تلعب بالأبيض ⚪")

def start_pvp_game(chat_id: int, white_id: int, white_name: str, black_id: int, black_name: str):
    board = chess.Board()
    get_user(white_id, white_name)
    get_user(black_id, black_name)
    games[chat_id] = {
        "board": board,
        "selected": None,
        "white_id": white_id,
        "black_id": black_id,
        "white_name": white_name,
        "black_name": black_name,
        "mode": "pvp",
    }
    send_board(
        chat_id,
        header=f"♟️ <b>تحدٍ جديد!</b>\n⚪ {white_name} ضد ⚫ {black_name}\nدور الأبيض الآن!",
    )

def send_board(chat_id: int, header: str = "", edit_message_id: int = None):
    g = games.get(chat_id)
    if not g:
        return
    board = g["board"]
    status = game_status_text(board)
    text = f"{header}\n\n" if header else ""
    text += create_board_text(board, extra_status=status)
    markup = create_board_markup(board, selected=g["selected"])

    if edit_message_id:
        try:
            bot.edit_message_text(chat_id=chat_id, message_id=edit_message_id, text=text, reply_markup=markup)
            return
        except Exception:
            pass
    bot.send_message(chat_id, text, reply_markup=markup)

def finish_game_if_over(chat_id: int) -> bool:
    g = games.get(chat_id)
    if not g:
        return False
    board = g["board"]
    if not is_game_over(board):
        return False

    result = game_result(board)
    w_delta, b_delta = apply_result(g["white_id"], g["black_id"], result)

    if result == "draw":
        result_text = "🤝 <b>انتهت المباراة بالتعادل!</b>"
    else:
        winner_name = g["white_name"] if result == "white" else g["black_name"]
        result_text = f"🏆 <b>مبروك! فاز {winner_name}</b>"

    if w_delta is not None:
        sign = "+" if w_delta >= 0 else ""
        result_text += f"\n⚪ {g['white_name']}: {sign}{w_delta}"
    if b_delta is not None:
        sign = "+" if b_delta >= 0 else ""
        result_text += f"\n⚫ {g['black_name']}: {sign}{b_delta}"

    bot.send_message(chat_id, result_text)
    del games[chat_id]
    return True

@bot.message_handler(commands=['start'])
def cmd_start(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    name = message.from_user.first_name or "لاعب"
    get_user(user_id, name)

    if not require_subscription(user_id):
        send_subscription_prompt(chat_id)
        return

    text = (
        f"♟️ <b>أهلاً بك {name} في بوت الشطرنج!</b> ♛\n\n"
        "🔥 نافس، اربح، وارتقِ في التصنيف العالمي!\n"
        "اختر من القائمة تحت 👇"
    )
    bot.send_message(chat_id, text, reply_markup=main_menu_markup())

@bot.message_handler(commands=['help'])
def cmd_help(message):
    text = HELP_TEXT
    if is_admin(message.from_user.id):
        text += ADMIN_HELP_TEXT
    bot.send_message(message.chat.id, text)

@bot.message_handler(commands=['newgame'])
def cmd_newgame(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    name = message.from_user.first_name or "لاعب"

    if not require_subscription(user_id):
        send_subscription_prompt(chat_id)
        return

    start_ai_game(chat_id, user_id, name)

@bot.message_handler(commands=['challenge'])
def cmd_challenge(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    name = message.from_user.first_name or "لاعب"

    if not require_subscription(user_id):
        send_subscription_prompt(chat_id)
        return

    if not message.reply_to_message:
        bot.reply_to(message, "⚔️ لتحدي لاعب آخر، قم بالرد على إحدى رسائله في القروب بأمر /challenge")
        return

    opponent = message.reply_to_message.from_user
    if opponent.is_bot or opponent.id == user_id:
        bot.reply_to(message, "🚫 لا يمكنك تحدي نفسك أو تحدي بوت آخر!")
        return

    if chat_id in games:
        bot.reply_to(message, "⚠️ توجد مباراة قائمة بالفعل هنا، أنهِها أولاً بـ /resign")
        return

    start_pvp_game(
        chat_id,
        white_id=user_id,
        white_name=name,
        black_id=opponent.id,
        black_name=opponent.first_name or "لاعب",
    )

@bot.message_handler(commands=['resign'])
def cmd_resign(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    g = games.get(chat_id)
    if not g:
        bot.reply_to(message, "لا توجد مباراة قائمة حالياً.")
        return
    if user_id not in (g["white_id"], g["black_id"]) and not is_admin(user_id):
        bot.reply_to(message, "🚫 هذه ليست مباراتك!")
        return

    if g["mode"] == "pvp" and g["white_id"] != 0 and g["black_id"] != 0:
        result = "black" if user_id == g["white_id"] else "white"
        apply_result(g["white_id"], g["black_id"], result)
        winner = g["black_name"] if result == "black" else g["white_name"]
        bot.send_message(chat_id, f"🏳️ تم الاستسلام. فاز {winner} 🏆")
    else:
        bot.send_message(chat_id, "🏳️ تم إنهاء المباراة.")

    del games[chat_id]

@bot.message_handler(commands=['rating'])
def cmd_rating(message):
    user_id = message.from_user.id
    name = message.from_user.first_name or "لاعب"
    u = get_user(user_id, name)
    text = (
        f"📊 <b>تصنيف {u['name']}</b>\n\n"
        f"⭐ التصنيف (Elo): <b>{u['rating']}</b>\n"
        f"✅ انتصارات: {u['wins']}\n"
        f"❌ خسائر: {u['losses']}\n"
        f"🤝 تعادلات: {u['draws']}\n"
        f"🎮 مجموع المباريات: {u['games']}"
    )
    bot.send_message(message.chat.id, text)

@bot.message_handler(commands=['leaderboard'])
def cmd_leaderboard(message):
    bot.send_message(message.chat.id, build_leaderboard_text())

def build_leaderboard_text() -> str:
    top = leaderboard(10)
    if not top:
        return "لا يوجد لاعبون مسجلون بعد!"
    text = "🏆 <b>لوحة المتصدرين</b> 🏆\n\n"
    medals = ["🥇", "🥈", "🥉"]
    for i, (uid, data) in enumerate(top):
        medal = medals[i] if i < 3 else f"{i + 1}."
        text += f"{medal} {data['name']} — ⭐ {data['rating']}\n"
    return text

@bot.message_handler(commands=['addassistant'])
def cmd_add_assistant(message):
    if not is_owner(message.from_user.id):
        bot.reply_to(message, "🚫 هذا الأمر للمالك فقط.")
        return
    parts = message.text.split()
    if len(parts) != 2 or not parts[1].isdigit():
        bot.reply_to(message, "الاستخدام: /addassistant [آيدي المستخدم]")
        return
    new_id = int(parts[1])
    if add_assistant(new_id):
        bot.reply_to(message, f"✅ تم إضافة {new_id} كمساعد بنجاح.")
    else:
        bot.reply_to(message, "⚠️ هذا المستخدم مساعد بالفعل.")

@bot.message_handler(commands=['removeassistant'])
def cmd_remove_assistant(message):
    if not is_owner(message.from_user.id):
        bot.reply_to(message, "🚫 هذا الأمر للمالك فقط.")
        return
    parts = message.text.split()
    if len(parts) != 2 or not parts[1].isdigit():
        bot.reply_to(message, "الاستخدام: /removeassistant [آيدي المستخدم]")
        return
    rem_id = int(parts[1])
    if remove_assistant(rem_id):
        bot.reply_to(message, f"✅ تم إزالة {rem_id} من المساعدين.")
    else:
        bot.reply_to(message, "⚠️ هذا المستخدم ليس مساعداً.")

@bot.message_handler(commands=['assistants'])
def cmd_list_assistants(message):
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "🚫 هذا الأمر للمالك والمساعدين فقط.")
        return
    assistants = get_assistants()
    if not assistants:
        bot.reply_to(message, "لا يوجد مساعدون حالياً.")
        return
    text = "👥 <b>قائمة المساعدين:</b>\n\n" + "\n".join(f"• <code>{a}</code>" for a in assistants)
    bot.reply_to(message, text)

@bot.message_handler(commands=['stats'])
def cmd_stats(message):
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "🚫 هذا الأمر للمالك والمساعدين فقط.")
        return
    total_users = len(all_user_ids())
    total_assistants = len(get_assistants())
    active_games = len(games)
    text = (
        "📈 <b>إحصائيات البوت</b>\n\n"
        f"👤 عدد المستخدمين المسجلين: {total_users}\n"
        f"👥 عدد المساعدين: {total_assistants}\n"
        f"🎮 عدد المباريات النشطة الآن: {active_games}"
    )
    bot.reply_to(message, text)

@bot.message_handler(commands=['broadcast'])
def cmd_broadcast(message):
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "🚫 هذا الأمر للمالك والمساعدين فقط.")
        return
    parts = message.text.split(maxsplit=1)
    if len(parts) != 2:
        bot.reply_to(message, "الاستخدام: /broadcast [نص الرسالة]")
        return
    text = parts[1]
    ids = all_user_ids()
    sent, failed = 0, 0
    status_msg = bot.reply_to(message, f"⏳ جاري إرسال الرسالة إلى {len(ids)} مستخدم...")
    for uid in ids:
        try:
            bot.send_message(uid, f"📢 <b>إشعار من إدارة البوت:</b>\n\n{text}")
            sent += 1
        except Exception:
            failed += 1
    bot.edit_message_text(
        chat_id=status_msg.chat.id,
        message_id=status_msg.message_id,
        text=f"✅ تم الإرسال بنجاح إلى {sent} مستخدم.\n❌ فشل الإرسال إلى {failed} مستخدم.",
    )

@bot.callback_query_handler(func=lambda call: call.data == "check_sub")
def cb_check_sub(call):
    user_id = call.from_user.id
    missing = get_missing_channels(bot, user_id, REQUIRED_CHANNELS)
    if missing:
        bot.answer_callback_query(call.id, "❌ ما زلت غير مشترك في كل القنوات المطلوبة.", show_alert=True)
        return
    bot.answer_callback_query(call.id, "✅ تم التحقق بنجاح!")
    name = call.from_user.first_name or "لاعب"
    get_user(user_id, name)
    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text=f"♟️ <b>أهلاً بك {name}!</b> تم التحقق من اشتراكك بنجاح ✅\n\nاختر من القائمة تحت 👇",
        reply_markup=main_menu_markup(),
    )

@bot.callback_query_handler(func=lambda call: call.data == "new_ai")
def cb_new_ai(call):
    chat_id = call.message.chat.id
    user_id = call.from_user.id
    name = call.from_user.first_name or "لاعب"

    if not require_subscription(user_id):
        bot.answer_callback_query(call.id, "يجب الاشتراك في القنوات أولاً!", show_alert=True)
        send_subscription_prompt(chat_id)
        return

    if chat_id in games:
        bot.answer_callback_query(call.id, "⚠️ توجد مباراة قائمة بالفعل هنا، أنهِها أولاً بـ /resign", show_alert=True)
        return

    bot.answer_callback_query(call.id, "🎮 لعبة جديدة!")
    start_ai_game(chat_id, user_id, name)

@bot.callback_query_handler(func=lambda call: call.data == "show_leaderboard")
def cb_leaderboard(call):
    bot.answer_callback_query(call.id)
    bot.send_message(call.message.chat.id, build_leaderboard_text())

@bot.callback_query_handler(func=lambda call: call.data == "show_rating")
def cb_rating(call):
    bot.answer_callback_query(call.id)
    user_id = call.from_user.id
    name = call.from_user.first_name or "لاعب"
    u = get_user(user_id, name)
    text = (
        f"📊 <b>تصنيف {u['name']}</b>\n\n"
        f"⭐ التصنيف (Elo): <b>{u['rating']}</b>\n"
        f"✅ انتصارات: {u['wins']}\n"
        f"❌ خسائر: {u['losses']}\n"
        f"🤝 تعادلات: {u['draws']}\n"
        f"🎮 مجموع المباريات: {u['games']}"
    )
    bot.send_message(call.message.chat.id, text)

@bot.callback_query_handler(func=lambda call: call.data.startswith('sq_'))
def cb_square(call):
    chat_id = call.message.chat.id
    user_id = call.from_user.id

    g = games.get(chat_id)
    if not g:
        bot.answer_callback_query(call.id, "لا توجد لعبة قائمة. أرسل /newgame لبدء لعبة جديدة.")
        return

    board = g["board"]
    is_white_turn = board.turn == chess.WHITE
    expected_player = g["white_id"] if is_white_turn else g["black_id"]

    if expected_player == 0:
        bot.answer_callback_query(call.id, "⏳ انتظر، دور الذكاء الاصطناعي الآن...")
        return

    if user_id != expected_player:
        bot.answer_callback_query(call.id, "🚫 ليس دورك الآن!", show_alert=True)
        return

    square_clicked = call.data.split('_')[1]

    if g["selected"] is None:
        piece = board.piece_at(chess.parse_square(square_clicked))
        if piece is None or piece.color != board.turn:
            bot.answer_callback_query(call.id, "اختر إحدى قطعك أولاً!")
            return
        g["selected"] = square_clicked
        bot.answer_callback_query(call.id, f"تم تحديد: {square_clicked}")
        send_board(chat_id, edit_message_id=call.message.message_id)
        return

    if g["selected"] == square_clicked:
        g["selected"] = None
        bot.answer_callback_query(call.id, "تم إلغاء التحديد.")
        send_board(chat_id, edit_message_id=call.message.message_id)
        return

    move_uci = f"{g['selected']}{square_clicked}"
    move = try_build_move(board, move_uci)

    if move is None or move not in board.legal_moves:
        g["selected"] = None
        bot.answer_callback_query(call.id, "❌ نقلة غير قانونية! اختر مجدداً.", show_alert=True)
        send_board(chat_id, edit_message_id=call.message.message_id)
        return

    board.push(move)
    g["selected"] = None
    bot.answer_callback_query(call.id, "✅ نقلة صحيحة!")
    send_board(chat_id, header=f"♟️ نقلة: <code>{move_uci}</code>", edit_message_id=call.message.message_id)

    if finish_game_if_over(chat_id):
        return

    if g["mode"] == "ai" and board.turn == chess.BLACK:
        ai_move = pick_ai_move(board)
        if ai_move:
            board.push(ai_move)
            send_board(chat_id, header=f"🤖 نقلة الذكاء الاصطناعي: <code>{ai_move.uci()}</code>")
        finish_game_if_over(chat_id)

def try_build_move(board: chess.Board, move_uci: str):
    try:
        move = chess.Move.from_uci(move_uci)
        if move in board.legal_moves:
            return move
    except ValueError:
        pass
    try:
        move = chess.Move.from_uci(move_uci + "q")
        if move in board.legal_moves:
            return move
    except ValueError:
        pass
    return None

if __name__ == "__main__":
    print("♟️ البوت يعمل بنجاح...")
    bot.infinity_polling(skip_pending=True)
