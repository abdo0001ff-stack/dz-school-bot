import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

# تفعيل تسجيل الأخطاء والملاحظات (Logging)
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# ==========================================
# 🔑 الإعدادات الخاصة بك
# ==========================================

# 1. التوكين الخاص بك من BotFather
TOKEN = "8647094829:AAGod0gFDj9zmDVO2kiuDT2ynL68HBBUZjY"

# 2. قائمة آيديات المديرين (يمكنك إضافة أي آيدي جديد هنا مفصولاً بفاصلة)
ADMIN_IDS = [
    6985307484,  # الآيدي الخاص بك
    # 123456789, # آيدي مدير ثاني (اكتب الآيدي هنا عند الحاجة)
]

# ==========================================
# 📚 البيانات التعليمية للمنصة
# ==========================================
EDUCATIONAL_DATA = {
    "1as": {
        "title": "السنة الأولى ثانوي 🏫",
        "streams": {
            "common_sci": "جذع مشترك علوم وتكنولوجيا 🔬",
            "common_lit": "جذع مشترك أدب 📖"
        }
    },
    "2as": {
        "title": "السنة الثانية ثانوي 🏫",
        "streams": {
            "exp_sci": "شعبة علوم تجريبية 🧪",
            "math": "شعبة رياضيات 📐",
            "math_tech": "شعبة تقني رياضي ⚙️",
            "mgt": "شعبة تسيير واقتصاد 📊",
            "lit_phil": "شعبة آداب وفلسفة 📜",
            "lang": "شعبة لغات أجنبية 🌐"
        }
    },
    "3as": {
        "title": "السنة الثالثة ثانوي (بكالوريا) 🎓",
        "streams": {
            "exp_sci": "شعبة علوم تجريبية 🧪",
            "math": "شعبة رياضيات 📐",
            "math_tech": "شعبة تقني رياضي ⚙️",
            "mgt": "شعبة تسيير واقتصاد 📊",
            "lit_phil": "شعبة آداب وفلسفة 📜",
            "lang": "شعبة لغات أجنبية 🌐"
        }
    }
}

# أمر البداية /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_first_name = update.effective_user.first_name
    
    # التحقق مما إذا كان المستخدم مديراً
    is_admin = user_id in ADMIN_IDS

    keyboard = [
        [InlineKeyboardButton("السنة الأولى ثانوي 🏫", callback_data="year_1as")],
        [InlineKeyboardButton("السنة الثانية ثانوي 🏫", callback_data="year_2as")],
        [InlineKeyboardButton("السنة الثالثة ثانوي 🎓", callback_data="year_3as")],
    ]
    
    # إضافة زر لوحة التحكم إذا كان المستخدم مديراً
    if is_admin:
        keyboard.append([InlineKeyboardButton("⚙️ لوحة تحكم المدير", callback_data="admin_panel")])

    reply_markup = InlineKeyboardMarkup(keyboard)
    welcome_text = (
        f"مرحباً بك يا {user_first_name} في **المنصة التعليمية** 📚✨\n\n"
        "اختر مستواك الدراسي لمشاهدة المواد والدروس المتاحة:"
    )
    
    if update.message:
        await update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode="Markdown")
    elif update.callback_query:
        await update.callback_query.edit_message_text(welcome_text, reply_markup=reply_markup, parse_mode="Markdown")

# معالجة تفاعلات الأزرار
async def handle_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    user_id = query.from_user.id

    # العودة للقائمة الرئيسية
    if data == "main_menu":
        await start(update, context)
        return

    # لوحة تحكم المدير
    elif data == "admin_panel":
        if user_id in ADMIN_IDS:
            keyboard = [[InlineKeyboardButton("⬅️ العودة للقائمة الرئيسية", callback_data="main_menu")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                "👑 **أهلاً بك في لوحة تحكم المدير**\n\nأنت تملك صلاحيات إدارة البوت والمنصة.",
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )
        else:
            await query.answer("عذراً، هذه اللوحة مخصصة للمديرين فقط!", show_alert=True)

    # اختيار السنة الدراسية
    elif data.startswith("year_"):
        year_key = data.replace("year_", "")
        year_info = EDUCATIONAL_DATA.get(year_key)
        
        if year_info:
            keyboard = []
            for stream_key, stream_name in year_info["streams"].items():
                keyboard.append([InlineKeyboardButton(stream_name, callback_data=f"stream_{year_key}_{stream_key}")])
            
            keyboard.append([InlineKeyboardButton("⬅️ العودة للقائمة الرئيسية", callback_data="main_menu")])
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                f"اختر الشعبة الخاصة بـ **{year_info['title']}**:",
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )

    # اختيار الشعبة وعرض الدروس
    elif data.startswith("stream_"):
        parts = data.split("_")
        year_key = parts[1]
        stream_key = parts[2]
        
        year_title = EDUCATIONAL_DATA[year_key]["title"]
        stream_title = EDUCATIONAL_DATA[year_key]["streams"][stream_key]

        keyboard = [
            [InlineKeyboardButton("⬅️ العودة لتحديد السنة", callback_data="main_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        message_content = (
            f"📚 **{year_title}**\n"
            f"🎯 **{stream_title}**\n\n"
            "مرحباً بك! يتم تحضير الدروس والملخصات الخاصة بهذه الشعبة قريباً.\n"
            "تأكد من متابعة القناة والتحديثات أولاً بأول! 🚀"
        )
        
        await query.edit_message_text(message_content, reply_markup=reply_markup, parse_mode="Markdown")

# التشغيل الرئيسي للبوت
if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_buttons))
    
    print("🚀 البوت يعمل الآن بنجاح على السيرفر...")
    app.run_polling()


