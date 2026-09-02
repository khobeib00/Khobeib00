import os
import json
import logging
import io
import chess
import chess.svg
import cairosvg
from PIL import Image
from telebot import TeleBot, types

# 1. إعداد نظام سجلات الأخطاء
logging.basicConfig(level=logging.INFO)

# 2. قراءة متغيرات البيئة من Render
BOT_TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID_ENV = os.getenv("OWNER_ID")

if not BOT_TOKEN or not OWNER_ID_ENV:
    raise ValueError("خطأ: يرجى إدخال BOT_TOKEN و OWNER_ID في متغيرات البيئة بـ Render!")

OWNER_ID = int(OWNER_ID_ENV)
bot = TeleBot(BOT_TOKEN)

# 3. قواعد البيانات البسيطة وتخزين الألعاب
ADMINS_FILE = "admins.json"
LANGS_FILE = "languages.json"

# تخزين الألعاب النشطة في الذاكرة: {user_id: chess.Board()}
user_games = {}

def load_json(filepath, default):
    if os.path.exists(filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logging.error(f"خطأ في تحميل {filepath}: {e}")
    return default

def save_json(filepath, data):
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

admins_list = load_json(ADMINS_FILE, [])
user_languages = load_json(LANGS_FILE, {})

def is_admin(user_id):
    return user_id == OWNER_ID or user_id in admins_list

def log_admin_action(text):
    """إرسال سجل الإدارة للمطور بنص عادي لتجنب أخطاء Markdown"""
    try:
        bot.send_message(OWNER_ID, f"🔔 [سجل الإدارة]\n{text}")
    except Exception as e:
        logging.error(f"فشل إرسال سجل الإدارة: {e}")

# 4. دالة توليد صورة رقعة الشطرنج (PNG)
def generate_board_image(board):
    svg_data = chess.svg.board(board=board, size=400)
    png_bytes = cairosvg.svg2png(bytestring=svg_data.encode('utf-8'))
    image_stream = io.BytesIO(png_bytes)
    image_stream.seek(0)
    return image_stream

# 5. لوحات التحكم والمفاتيح
def get_admin_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=2)
    btn_add = types.InlineKeyboardButton("➕ إضافة مساعد", callback_data="admin_add")
    btn_del = types.InlineKeyboardButton("➖ إزالة مساعد", callback_data="admin_del")
    btn_list = types.InlineKeyboardButton("📜 قائمة المساعدين", callback_data="admin_list")
    btn_stats = types.InlineKeyboardButton("📊 الإحصائيات", callback_data="admin_stats")
    markup.add(btn_add, btn_del)
    markup.add(btn_list, btn_stats)
    return markup

def get_game_keyboard(board):
    markup = types.InlineKeyboardMarkup(row_width=3)
    btn_reset = types.InlineKeyboardButton("🔄 لعبة جديدة", callback_data="start_game")
    btn_resign = types.InlineKeyboardButton("🏳️ استسلام", callback_data="resign_game")
    markup.add(btn_reset, btn_resign)
    return markup

# 6. الأوامر الرئيسية (/start & /admin)
@bot.message_handler(commands=['start'])
def start_command(message):
    markup = types.InlineKeyboardMarkup(row_width=2)
    btn_ar = types.InlineKeyboardButton("العربية 🇸🇦", callback_data="lang_ar")
    btn_en = types.InlineKeyboardButton("English 🇬🇧", callback_data="lang_en")
    markup.add(btn_ar, btn_en)
    
    welcome_msg = (
        "مرحباً بك في بوت الشطرنج الاحترافي! ♟️\n"
        "اختر لغتك للمتابعة:\n\n"
        "Welcome to Professional Chess Bot! ♟️\n"
        "Choose your language:"
    )
    bot.send_message(message.chat.id, welcome_msg, reply_markup=markup)

@bot.message_handler(commands=['admin'])
def admin_panel(message):
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "⚠️ هذه اللوحة مخصصة للإدارة فقط.")
        return
    
    bot.send_message(
        message.chat.id, 
        "🛠 **لوحة تحكم الإدارة**\nاختر الخيار المناسب من الأزرار التالية:", 
        reply_markup=get_admin_keyboard()
    )

# 7. معالجة النقلات النصية (مثل e2e4 أو e4)
@bot.message_handler(func=lambda msg: msg.from_user.id in user_games and not msg.text.startswith('/'))
def handle_move(message):
    user_id = message.from_user.id
    board = user_games[user_id]
    move_text = message.text.strip()

    try:
        move = board.parse_san(move_text)
        board.push(move)

        if board.is_game_over():
            bot.send_message(message.chat.id, f"🎉 انتهت المباراة! النتيجة: {board.result()}")
            del user_games[user_id]
            return

        # رد الذكاء الاصطناعي (أول نقلة قانونية متوفرة)
        ai_move = list(board.legal_moves)[0]
        board.push(ai_move)

        img = generate_board_image(board)
        bot.send_photo(
            message.chat.id,
            photo=img,
            caption=f"✅ لعبت: {move_text}\n🤖 لعب البوت: {ai_move.uci()}\n\nأرسل نقلتك التالية (مثال: e7e5 أو Nf3):",
            reply_markup=get_game_keyboard(board)
        )

        if board.is_game_over():
            bot.send_message(message.chat.id, f"🎉 انتهت المباراة! النتيجة: {board.result()}")
            del user_games[user_id]

    except ValueError:
        bot.reply_to(message, "❌ نقلة غير صحيحة! يرجى إرسال النقلة بصيغة صحيحة (مثل: e4, d4, Nf3, e2e4).")

# 8. معالجة الأزرار التفاعلية (Callback Queries)
@bot.callback_query_handler(func=lambda call: True)
def handle_callbacks(call):
    user_id = call.from_user.id

    if call.data.startswith('lang_'):
        lang = call.data.split('_')[1]
        user_languages[str(user_id)] = lang
        save_json(LANGS_FILE, user_languages)
        
        msg = "تم ضبط اللغة إلى العربية 🇸🇦" if lang == 'ar' else "Language set to English 🇬🇧"
        bot.answer_callback_query(call.id, msg)
        
        game_markup = types.InlineKeyboardMarkup()
        btn_game = types.InlineKeyboardButton("♟️ بدء مباراة جديدة", callback_data="start_game")
        game_markup.add(btn_game)
        
        bot.edit_message_text(
            f"{msg}\n\nاضغط على الزر أدناه لبدء مباراة شطرنج جديدة!",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=game_markup
        )

    elif call.data == "start_game":
        board = chess.Board()
        user_games[user_id] = board
        img = generate_board_image(board)
        
        bot.send_photo(
            call.message.chat.id,
            photo=img,
            caption="♟️ **بدأت المباراة!**\n\nأنت تلعب بالقطع البيضاء. أرسل نقلتك كرسالة نصية (مثال: `e4` أو `e2e4`):",
            parse_mode="Markdown",
            reply_markup=get_game_keyboard(board)
        )
        bot.answer_callback_query(call.id)

    elif call.data == "resign_game":
        if user_id in user_games:
            del user_games[user_id]
            bot.send_message(call.message.chat.id, "🏳️ قمت بالاستسلام. تم إنهاء المباراة.")
        else:
            bot.send_message(call.message.chat.id, "لا توجد مباراة نشطة حالياً.")
        bot.answer_callback_query(call.id)

    elif call.data.startswith('admin_'):
        if not is_admin(user_id):
            bot.answer_callback_query(call.id, "غير مصرح لك!", show_alert=True)
            return

        if call.data == "admin_list":
            text = "📜 قائمة المساعدين:\n" + "\n".join([f"- ID: `{aid}`" for aid in admins_list]) if admins_list else "لا يوجد مساعدين حالياً."
            bot.send_message(call.message.chat.id, text, parse_mode="Markdown")
            
        elif call.data == "admin_add":
            msg = bot.send_message(call.message.chat.id, "أرسل الآيدي (ID) الخاص بالمساعد الجديد:")
            bot.register_next_step_handler(msg, process_add_admin)

        elif call.data == "admin_del":
            msg = bot.send_message(call.message.chat.id, "أرسل الآيدي (ID) الخاص بالمساعد المراد إزالته:")
            bot.register_next_step_handler(msg, process_del_admin)

        elif call.data == "admin_stats":
            stats = f"📊 **إحصائيات البوت**:\n\n👤 المستخدمين: {len(user_languages)}\n🛡️ المساعدين: {len(admins_list)}\n♟️ المباريات النشطة: {len(user_games)}"
            bot.send_message(call.message.chat.id, stats)

        bot.answer_callback_query(call.id)

# 9. دوال إدارة المساعدين
def process_add_admin(message):
    if message.from_user.id != OWNER_ID:
        return
    try:
        new_id = int(message.text.strip())
        if new_id not in admins_list:
            admins_list.append(new_id)
            save_json(ADMINS_FILE, admins_list)
            bot.reply_to(message, f"✅ تم إضافة المساعد `{new_id}` بنجاح.")
            log_admin_action(f"قام المطور بإضافة المساعد: {new_id}")
        else:
            bot.reply_to(message, "⚠️ هذا المستخدم موجود بالفعل في القائمة.")
    except ValueError:
        bot.reply_to(message, "❌ يرجى إرسال آيدي صحيح (أرقام فقط).")

def process_del_admin(message):
    if message.from_user.id != OWNER_ID:
        return
    try:
        target_id = int(message.text.strip())
        if target_id in admins_list:
            admins_list.remove(target_id)
            save_json(ADMINS_FILE, admins_list)
            bot.reply_to(message, f"✅ تم إزالة المساعد `{target_id}` بنجاح.")
            log_admin_action(f"قام المطور بإزالة المساعد: {target_id}")
        else:
            bot.reply_to(message, "⚠️ هذا الآيدي غير موجود.")
    except ValueError:
        bot.reply_to(message, "❌ يرجى إرسال آيدي صحيح (أرقام فقط).")

# 10. التشغيل المباشر
if __name__ == "__main__":
    logging.info("تم تشغيل البوت بنجاح...")
    bot.infinity_polling(skip_pending=True)
