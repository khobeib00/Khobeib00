# translations.py

TEXTS = {
    'ar': {
        'welcome': (
            "↳︎𝟔𝟒 𝐒𝐪𝐮𝐚𝐫𝐞𝐬... 𝐄𝐧𝐝𝐥𝐞𝐬𝐬 𝐏𝐨𝐬𝐬𝐢𝐛𝐢𝐥𝐢𝐭𝐢𝐞𝐬! ✨•\n"
            "↳︎𝐄𝐯𝐞𝐫𝐲 𝐦𝐨𝐯𝐞 𝐢𝐬 𝐚 𝐝𝐞𝐜𝐢𝐬𝐢𝐨𝐧, 𝐞𝐯𝐞𝐫𝐲 𝐦𝐚𝐭𝐜𝐡 𝐚 𝐛𝐚𝐭𝐭𝐥𝐞 𝐨𝐟 𝐦𝐢𝐧𝐝𝐬•\n"
            "↳︎𝐅𝐫𝐨𝐦 𝐭𝐡𝐞 𝐟𝐢𝐫𝐬𝐭 𝐦𝐨𝐯𝐞 𝐭𝐨 𝐭𝐡𝐞 𝐟𝐢𝐧𝐚𝐥 𝐜𝐡𝐞𝐜𝐤𝐦𝐚𝐭𝐞... 𝐰𝐫𝐢𝐭𝐞 𝐲𝐨𝐮𝐫 𝐨𝐰𝐧 𝐥𝐞𝐠𝐞𝐧𝐝•\n"
            "↳︎𝐀𝐫𝐞 𝐲𝐨𝐮 𝐭𝐡𝐞 𝐧𝐞𝐱𝐭 𝐜𝐡𝐚𝐦𝐩𝐢𝐨𝐧?!!•\n\n"
            "↳︎𝐃𝐞𝐯 @hihi_jl | @khobeib00 🎖"
        ),
        'admin_panel': (
            "\n\n⚙️ **قائمة أوامر المسؤولين:**\n"
            "• `/addadmin <ID>` - إضافة مساعد جديد (المالك فقط)\n"
            "• `/removeadmin <ID>` - إزالة مساعد (المالك فقط)\n"
            "• `/admins` - عرض قائمة المساعدين والمالك\n"
            "• `/id` - معرفة المعرف الخاص بك"
        ),
        'sub_required': "⚠️ عذراً، يجب عليك الاشتراك في القنوات التالية أولاً لاستخدام البوت:",
        'check_sub_btn': "✅ تحقق من الاشتراك",
        'not_subbed_toast': "❌ ما زلت غير مشترك في كافة القنوات المطلوبة!",
        'sub_verified': "✅ تم التحقق من اشتراكك بنجاح! يمكنك البدء الآن.",
        'start_chess_prompt': "🎮 **من سيشارك في لعبة الشطرنج؟**",
        'btn_i_will_play': "⚔️ أنا سألعب",
        'btn_vs_bot': "🤖 العب ضد البوت",
        'btn_accept_invite': "🤝 قبول الدعوة",
        'invite_sent': "✉️ {inviter} يدعو {invited} للعب مباراة شطرنج خاصة!",
        'invite_need_reply': "⚠️ يجب استخدام هذا الأمر بالرد على رسالة الشخص الذي تريد دعوته!",
        'invite_not_for_you': "❌ هذه الدعوة ليست مخصصة لك!",
        'game_already_running': "⚠️ هناك لعبة شطرنج شغال حالياً في هذه المحادثة!",
        'places_full': "❌ الأماكن ممتلئة لهذه اللعبة بالفعل!",
        'no_active_game': "⚠️ لا توجد لعبة شطرنج جارية الآن لإنهائها.",
        'not_authorized_end': "❌ لا يمكنك إنهاء اللعبة! فقط مشرفو المجموعة أو اللاعب نفسه ضد البوت يمكنهم ذلك.",
        'game_ended_manual': "🛑 تم إنهاء اللعبة يدوياً بواسطة {user}.",
        'not_your_turn': "❌ ليس دورك الآن!",
        'not_a_player': "❌ أنت لست مشاركاً في هذه اللعبة!",
        'time_out': "⏳ انتهى وقت {loser}! الفائز هو {winner} بسبب نفاد الوقت 🎉",
        'checkmate': "♚ كش مات! الفائز هو {winner} 🎉",
        'stalemate': "🤝 انتهت اللعبة بالتعادل (Stalemate)!",
        'draw': "🤝 انتهت اللعبة بالتعادل!",
        'capture_msg': "⚔️ {player} أكل قطعة في الخانة `{square}`!",
        'lang_selected': "🌐 تم تغيير لغة البوت في هذه المحادثة إلى: العربية",
        'choose_lang': "🌐 اختر لغة البوت لهذه المحادثة:",
        'no_permission': "❌ ليس لديك صلاحية لاستخدام هذا الأمر.",
        'only_owner': "❌ هذا الأمر مخصص للمالك فقط.",
    },
    'en': {
        'welcome': (
            "↳︎𝟔𝟒 𝐒𝐪𝐮𝐚𝐫𝐞𝐬... 𝐄𝐧𝐝𝐥𝐞𝐬𝐬 𝐏𝐨𝐬𝐬𝐢𝐛𝐢𝐥𝐢𝐭𝐢𝐞𝐬! ✨•\n"
            "↳︎𝐄𝐯𝐞𝐫𝐲 𝐦𝐨𝐯𝐞 𝐢𝐬 𝐚 𝐝𝐞𝐜𝐢𝐬𝐢𝐨𝐧, 𝐞𝐯𝐞𝐫𝐲 𝐦𝐚𝐭𝐜𝐡 𝐚 𝐛𝐚𝐭𝐭𝐥𝐞 𝐨𝐟 𝐦𝐢𝐧𝐝𝐬•\n"
            "↳︎𝐅𝐫𝐨𝐦 𝐭𝐡𝐞 𝐟𝐢𝐫𝐬𝐭 𝐦𝐨𝐯𝐞 𝐭𝐨 𝐭𝐡𝐞 𝐟𝐢𝐧𝐚𝐥 𝐜𝐡𝐞𝐜𝐤𝐦𝐚𝐭𝐞... 𝐰𝐫𝐢𝐭𝐞 𝐲𝐨𝐮𝐫 𝐨𝐰𝐧 𝐥𝐞𝐠𝐞𝐧𝐝•\n"
            "↳︎𝐀𝐫𝐞 𝐲𝐨𝐮 𝐭𝐡𝐞 𝐧𝐞𝐱𝐭 𝐜𝐡𝐚𝐦𝐩𝐢𝐨𝐧?!!•\n\n"
            "↳︎𝐃𝐞𝐯 @hihi_jl | @khobeib00 🎖"
        ),
        'admin_panel': (
            "\n\n⚙️ **Admin Commands Panel:**\n"
            "• `/addadmin <ID>` - Add new admin (Owner only)\n"
            "• `/removeadmin <ID>` - Remove admin (Owner only)\n"
            "• `/admins` - List all admins & owner\n"
            "• `/id` - Show your Telegram User ID"
        ),
        'sub_required': "⚠️ Sorry, you must subscribe to the following channels first:",
        'check_sub_btn': "✅ Verify Subscription",
        'not_subbed_toast': "❌ You are still not subscribed to all channels!",
        'sub_verified': "✅ Subscription verified! You can start now.",
        'start_chess_prompt': "🎮 **Who will join the Chess game?**",
        'btn_i_will_play': "⚔️ I will play",
        'btn_vs_bot': "🤖 Play vs Bot",
        'btn_accept_invite': "🤝 Accept Invite",
        'invite_sent': "✉️ {inviter} invites {invited} for a private Chess match!",
        'invite_need_reply': "⚠️ You must use this command by replying to the user you want to invite!",
        'invite_not_for_you': "❌ This invitation is not for you!",
        'game_already_running': "⚠️ There is already an active game in this chat!",
        'places_full': "❌ All player slots are full for this game!",
        'no_active_game': "⚠️ No active game to end in this chat.",
        'not_authorized_end': "❌ You are not authorized to end this game!",
        'game_ended_manual': "🛑 Game manually ended by {user}.",
        'not_your_turn': "❌ It is not your turn!",
        'not_a_player': "❌ You are not a player in this match!",
        'time_out': "⏳ Time out for {loser}! {winner} wins on time 🎉",
        'checkmate': "♚ Checkmate! {winner} wins 🎉",
        'stalemate': "🤝 Game ended in a Stalemate!",
        'draw': "🤝 Game ended in a Draw!",
        'capture_msg': "⚔️ {player} captured a piece on `{square}`!",
        'lang_selected': "🌐 Language changed to English for this chat.",
        'choose_lang': "🌐 Select bot language for this chat:",
        'no_permission': "❌ You do not have permission to use this command.",
        'only_owner': "❌ This command is strictly reserved for the Owner.",
    }
}

def get_text(lang, key, **kwargs):
    text = TEXTS.get(lang, TEXTS['ar']).get(key, TEXTS['ar'].get(key, ""))
    if kwargs:
        return text.format(**kwargs)
    return text
