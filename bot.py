import os
import telebot
from telebot import types
import chess
from flask import Flask
from threading import Thread

# -------------------------------------------------------------
# 1. خادم الويب الأساسي لمنع توقف Render (0% أخطاء)
# -------------------------------------------------------------
app = Flask('')

@app.route('/')
def home():
    return "Chess Bot is Running 24/7 Safely!"

def run_web_server():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

Thread(target=run_web_server, daemon=True).start()

# -------------------------------------------------------------
# 2. إعداد البوت وألعاب المستخدمين
# -------------------------------------------------------------
BOT_TOKEN = os.environ.get("BOT_TOKEN")
bot = telebot.TeleBot(BOT_TOKEN)

games = {}

def create_board_text(board):
    pieces_map = {
        'r': '♜', 'n': '♞', 'b': '♝', 'q': '♛', 'k': '♚', 'p': '♟',
        'R': '♖', 'N': '♘', 'B': '♗', 'Q': '♕', 'K': '♔', 'P': '♙',
        '.': '▪️'
    }
    board_str = str(board)
    for k, v in pieces_map.items():
        board_str = board_str.replace(k, v)
    
    fen_lines = board_str.split('\n')
    formatted_board = "<b>  a  b  c  d  e  f  g  h</b>\n"
    for idx, line in enumerate(fen_lines):
        formatted_board += f"<b>{8 - idx}</b> {line} <b>{8 - idx}</b>\n"
    formatted_board += "<b>  a  b  c  d  e  f  g  h</b>"
    return formatted_board

def create_board_markup(board):
    markup = types.InlineKeyboardMarkup(row_width=8)
    buttons = []
    
    for square in chess.SQUARES_180:
        piece = board.piece_at(square)
        label = piece.unicode_symbol() if piece else " "
        sq_name = chess.square_name(square)
        buttons.append(types.InlineKeyboardButton(text=label, callback_data=f"sq_{sq_name}"))
        
        if len(buttons) == 8:
            markup.row(*buttons)
            buttons = []
            
    return markup

# -------------------------------------------------------------
# 3. الأوامر والتفاعل بالأزرار
# -------------------------------------------------------------
@bot.message_handler(commands=['start', 'newgame'])
def start_game(message):
    chat_id = message.chat.id
    games[chat_id] = {
        'board': chess.Board(),
        'selected': None
    }
    
    board = games[chat_id]['board']
    text = f"♟️ <b>بدأت لعبة جديدة!</b>\n\n{create_board_text(board)}\n\n👇 <b>اضغط على القطعة ثم على المربع المراد التحريك إليه:</b>"
    markup = create_board_markup(board)
    
    bot.send_message(chat_id, text, parse_mode='HTML', reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('sq_'))
def handle_square_click(call):
    chat_id = call.message.chat.id
    if chat_id not in games:
        bot.answer_callback_query(call.id, "لا توجد لعبة قائمة. أرسل /start لبدء لعبة جديدة.")
        return

    square_clicked = call.data.split('_')[1]
    game = games[chat_id]
    board = game['board']

    if game['selected'] is None:
        game['selected'] = square_clicked
        bot.answer_callback_query(call.id, f"تم تحديد: {square_clicked}. اختر مربع الهدف الآن.")
    else:
        move_uci = f"{game['selected']}{square_clicked}"
        move = chess.Move.from_uci(move_uci)

        if move in board.legal_moves:
            board.push(move)
            game['selected'] = None
            
            text = f"✅ <b>تم ملعوبة: {move_uci}</b>\n\n{create_board_text(board)}\n\n👇 <b>دورك الآن:</b>"
            markup = create_board_markup(board)
            
            bot.edit_message_text(
                chat_id=chat_id,
                message_id=call.message.message_id,
                text=text,
                parse_mode='HTML',
                reply_markup=markup
            )
            bot.answer_callback_query(call.id, "نقلة صحيحة!")
        else:
            game['selected'] = None
            bot.answer_callback_query(call.id, "نقلة غير قانونية! اختر مجدداً.", show_alert=True)

if __name__ == "__main__":
    print("البوت يعمل بنجاح...")
    bot.infinity_polling()
