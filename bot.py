import json
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
    ConversationHandler,
)

# === الإعدادات والتحديثات الخاصة بك ===
BOT_TOKEN = "8647094829:AAGod0gFDj9zmDVO2kiuDT2ynL68HBBUZjY"
ADMIN_IDS = [6985307484, "6985307484"]

DATA_FILE = "school_data.json"

# حالات المحادثات التفاعلية
(
    ADD_LESSON_STAGE, ADD_LESSON_YEAR, ADD_LESSON_SUB, ADD_LESSON_TITLE, ADD_LESSON_CONTENT,
    ADD_BOOK_STAGE, ADD_BOOK_YEAR, ADD_BOOK_SUB, ADD_BOOK_TITLE, ADD_BOOK_CONTENT,
    STUDENT_MESSAGE, ADMIN_REPLY_USER_ID, ADMIN_REPLY_TEXT
) = range(13)

# === الهيكلية الأساسية للأطوار ===
DEFAULT_STRUCTURE = {
    "stages": {
        "primary": {
            "name": "🏫 الطور الابتدائي",
            "years": {
                "y1": {"name": "السنة الأولى ابتدائي 🎒", "subjects": ["اللغة العربية 📚", "الرياضيات 🔢", "التربية الإسلامية 🕌", "التربية المدنية 🏛️"]},
                "y2": {"name": "السنة الثانية ابتدائي 🎒", "subjects": ["اللغة العربية 📚", "الرياضيات 🔢", "التربية الإسلامية 🕌", "التربية المدنية 🏛️", "التربية العلمية 🧪"]},
                "y3": {"name": "السنة الثالثة ابتدائي 🎒", "subjects": ["اللغة العربية 📚", "الرياضيات 🔢", "اللغة الفرنسية 🇫🇷", "التربية الإسلامية 🕌", "التربية المدنية 🏛️", "التاريخ والجغرافيا 🗺️", "التربية العلمية 🧪"]},
                "y4": {"name": "السنة الرابعة ابتدائي 🎒", "subjects": ["اللغة العربية 📚", "الرياضيات 🔢", "اللغة الفرنسية 🇫🇷", "التربية الإسلامية 🕌", "التربية المدنية 🏛️", "التاريخ والجغرافيا 🗺️", "التربية العلمية 🧪"]},
                "y5": {"name": "السنة الخامسة ابتدائي 🎓", "subjects": ["اللغة العربية 📚", "الرياضيات 🔢", "اللغة الفرنسية 🇫🇷", "التربية الإسلامية 🕌", "التربية المدنية 🏛️", "التاريخ والجغرافيا 🗺️", "التربية العلمية 🧪"]}
            }
        },
        "middle": {
            "name": "🏫 الطور المتوسط",
            "years": {
                "y1": {"name": "السنة الأولى متوسط 📐", "subjects": ["اللغة العربية 📚", "الرياضيات 📐", "العلوم الفيزيائية ⚛️", "علوم الطبيعة والحياة 🧬", "الفرنسية 🇫🇷", "الإنجليزية 🇬🇧", "التربية الإسلامية 🕌", "التاريخ والجغرافيا 🗺️", "التربية المدنية 🏛️"]},
                "y2": {"name": "السنة الثانية متوسط 📐", "subjects": ["اللغة العربية 📚", "الرياضيات 📐", "العلوم الفيزيائية ⚛️", "علوم الطبيعة والحياة 🧬", "الفرنسية 🇫🇷", "الإنجليزية 🇬🇧", "التربية الإسلامية 🕌", "التاريخ والجغرافيا 🗺️", "التربية المدنية 🏛️"]},
                "y3": {"name": "السنة الثالثة متوسط 📐", "subjects": ["اللغة العربية 📚", "الرياضيات 📐", "العلوم الفيزيائية ⚛️", "علوم الطبيعة والحياة 🧬", "الفرنسية 🇫🇷", "الإنجليزية 🇬🇧", "التربية الإسلامية 🕌", "التاريخ والجغرافيا 🗺️", "التربية المدنية 🏛️"]},
                "y4": {"name": "السنة الرابعة متوسط (BAM) 🎓", "subjects": ["اللغة العربية 📚", "الرياضيات 📐", "العلوم الفيزيائية ⚛️", "علوم الطبيعة والحياة 🧬", "الفرنسية 🇫🇷", "الإنجليزية 🇬🇧", "التربية الإسلامية 🕌", "التاريخ والجغرافيا 🗺️", "التربية المدنية 🏛️"]}
            }
        }
    },
    "lessons": {},
    "books": {}
}

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if "secondary" in data.get("stages", {}):
                del data["stages"]["secondary"]
            return data
    return DEFAULT_STRUCTURE

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

db = load_data()

def is_admin(user_id):
    return user_id in ADMIN_IDS or str(user_id) in ADMIN_IDS

async def delete_previous_media_msg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """دالة مساعدة لحذف الرسائل السابقة للتنظيف"""
    msg_id = context.user_data.get("last_media_msg_id")
    if msg_id:
        try:
            await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=msg_id)
        except Exception:
            pass
        context.user_data["last_media_msg_id"] = None

# === الواجهة الرئيسية ===

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    await delete_previous_media_msg(update, context)
    
    keyboard = [
        [InlineKeyboardButton("📚 الدروس والكتب حسب الطور والسنوات", callback_data="select_stage")],
        [InlineKeyboardButton("💬 التواصل مع المطور / المعلم", callback_data="contact_developer")]
    ]

    if is_admin(user_id):
        keyboard.append([InlineKeyboardButton("⚙️ لوحة تحكم الأدمين والأستاذ", callback_data="admin_panel")])

    reply_markup = InlineKeyboardMarkup(keyboard)
    text = "🇩🇿 **مرحباً بك في منصة المدرسة الجزائرية الشاملة** 🏫\n\nاختر من القائمة أدناه للوصول إلى الدروس والكتب الخاصة بسنتك الدراسية:"

    if update.callback_query:
        try:
            await update.callback_query.message.edit_text(text, reply_markup=reply_markup, parse_mode="Markdown")
        except Exception:
            await update.callback_query.message.delete()
            await context.bot.send_message(chat_id=update.effective_chat.id, text=text, reply_markup=reply_markup, parse_mode="Markdown")
    else:
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode="Markdown")

# === معالجة التصفح ===

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    user_id = query.from_user.id

    if data == "main_menu":
        await start(update, context)

    # 1. اختيار الطور
    elif data == "select_stage":
        await delete_previous_media_msg(update, context)
        keyboard = []
        for stage_key, stage_info in db["stages"].items():
            keyboard.append([InlineKeyboardButton(stage_info["name"], callback_data=f"stage_{stage_key}")])
        keyboard.append([InlineKeyboardButton("🔙 العودة للقائمة الرئيسية", callback_data="main_menu")])

        try:
            await query.message.edit_text("🎓 **اختر الطور الدراسي:**", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
        except Exception:
            await query.message.delete()
            await context.bot.send_message(chat_id=query.message.chat_id, text="🎓 **اختر الطور الدراسي:**", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

    # 2. اختيار السنة الدراسية
    elif data.startswith("stage_"):
        await delete_previous_media_msg(update, context)
        stage_key = data.split("_")[1]
        stage = db["stages"][stage_key]
        
        keyboard = []
        for year_key, year_info in stage["years"].items():
            keyboard.append([InlineKeyboardButton(year_info["name"], callback_data=f"year_{stage_key}_{year_key}")])

        keyboard.append([InlineKeyboardButton("🔙 اختيار طور آخر", callback_data="select_stage")])
        
        try:
            await query.message.edit_text(f"📌 **{stage['name']}**\nاختر السُنّة الدراسية:", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
        except Exception:
            await query.message.delete()
            await context.bot.send_message(chat_id=query.message.chat_id, text=f"📌 **{stage['name']}**\nاختر السُنّة الدراسية:", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

    # 3. اختيار المادة
    elif data.startswith("year_"):
        await delete_previous_media_msg(update, context)
        _, stage_key, year_key = data.split("_")
        year_info = db["stages"][stage_key]["years"][year_key]

        keyboard = []
        for sub_name in year_info["subjects"]:
            full_key = f"{stage_key}_{year_key}_{sub_name}"
            lessons_cnt = len(db["lessons"].get(full_key, []))
            books_cnt = len(db.get("books", {}).get(full_key, []))
            keyboard.append([InlineKeyboardButton(f"{sub_name} (دروس: {lessons_cnt} | كتب: {books_cnt})", callback_data=f"sub_menu_{full_key}")])

        keyboard.append([InlineKeyboardButton("🔙 العودة للسنوات", callback_data=f"stage_{stage_key}")])
        
        try:
            await query.message.edit_text(f"📖 **{year_info['name']}**\nاختر المادة الدراسية:", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
        except Exception:
            await query.message.delete()
            await context.bot.send_message(chat_id=query.message.chat_id, text=f"📖 **{year_info['name']}**\nاختر المادة الدراسية:", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

    # 4. قائمة خيارات المادة
    elif data.startswith("sub_menu_"):
        await delete_previous_media_msg(update, context)
        full_key = data.replace("sub_menu_", "")
        parts = full_key.split("_", 2)
        stage_key, year_key, sub_name = parts[0], parts[1], parts[2]

        keyboard = [
            [InlineKeyboardButton("📖 الشروحات والدروس", callback_data=f"list_les_{full_key}")],
            [InlineKeyboardButton("📚 الكتب والملخصات PDF", callback_data=f"list_bk_{full_key}")],
            [InlineKeyboardButton("🔙 العودة للمواد", callback_data=f"year_{stage_key}_{year_key}")]
        ]
        
        try:
            await query.message.edit_text(f"📌 **مادة {sub_name}**\nاختر ماذا تريد أن تتصفح:", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
        except Exception:
            await query.message.delete()
            await context.bot.send_message(chat_id=query.message.chat_id, text=f"📌 **مادة {sub_name}**\nاختر ماذا تريد أن تتصفح:", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

    # 5. عرض قائمة الدروس
    elif data.startswith("list_les_"):
        await delete_previous_media_msg(update, context)
        full_key = data.replace("list_les_", "")
        parts = full_key.split("_", 2)
        stage_key, year_key, sub_name = parts[0], parts[1], parts[2]

        lessons = db["lessons"].get(full_key, [])
        keyboard = []
        for l in lessons:
            keyboard.append([InlineKeyboardButton(f"📖 {l['title']}", callback_data=f"view_les_{full_key}_{l['id']}")])
        
        keyboard.append([InlineKeyboardButton("🔙 العودة للمادة", callback_data=f"sub_menu_{full_key}")])
        text_content = f"📌 **دروس {sub_name}:**" if lessons else f"📌 **مادة {sub_name}:**\nلا توجد دروس مضافة حالياً."
        
        try:
            await query.message.edit_text(text_content, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
        except Exception:
            await query.message.delete()
            await context.bot.send_message(chat_id=query.message.chat_id, text=text_content, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

    # 6. عرض قائمة الكتب
    elif data.startswith("list_bk_"):
        await delete_previous_media_msg(update, context)
        full_key = data.replace("list_bk_", "")
        parts = full_key.split("_", 2)
        stage_key, year_key, sub_name = parts[0], parts[1], parts[2]

        books = db.get("books", {}).get(full_key, [])
        keyboard = []
        for b in books:
            keyboard.append([InlineKeyboardButton(f"📚 {b['title']}", callback_data=f"view_bk_{full_key}_{b['id']}")])
        
        keyboard.append([InlineKeyboardButton("🔙 العودة للمادة", callback_data=f"sub_menu_{full_key}")])
        text_content = f"📚 **كتب وملخصات {sub_name}:**" if books else f"📚 **مادة {sub_name}:**\nلا توجد كتب أو ملخصات مضافة حالياً."
        
        try:
            await query.message.edit_text(text_content, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
        except Exception:
            await query.message.delete()
            await context.bot.send_message(chat_id=query.message.chat_id, text=text_content, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

    # 7. عرض الدرس أو الكتاب (حذف الرسالة السابقة وتنظيف الشاشة)
    elif data.startswith("view_les_") or data.startswith("view_bk_"):
        await delete_previous_media_msg(update, context)
        is_lesson = data.startswith("view_les_")
        prefix = "view_les_" if is_lesson else "view_bk_"
        raw_data = data.replace(prefix, "")
        
        parts = raw_data.split("_")
        stage_key, year_key, sub_name, item_id = parts[0], parts[1], parts[2], parts[3]
        full_key = f"{stage_key}_{year_key}_{sub_name}"

        items = db["lessons"].get(full_key, []) if is_lesson else db.get("books", {}).get(full_key, [])
        item = next((i for i in items if str(i["id"]) == item_id), None)

        if item:
            back_callback = f"list_les_{full_key}" if is_lesson else f"list_bk_{full_key}"
            keyboard = [[InlineKeyboardButton("🔙 العودة للقائمة", callback_data=back_callback)]]
            reply_markup = InlineKeyboardMarkup(keyboard)

            tag = "درس" if is_lesson else "كتاب / ملخص"
            caption_text = f"📖 **{sub_name} - ({tag})**\n📝 **العنوان:** {item['title']}\n\n{item.get('content', '')}"

            media_type = item.get("media_type", "text")
            file_id = item.get("file_id")

            # مسح الرسالة القائمة لتنظيف الواجهة
            try:
                await query.message.delete()
            except Exception:
                pass

            sent_msg = None
            if media_type == "photo" and file_id:
                sent_msg = await context.bot.send_photo(chat_id=query.message.chat_id, photo=file_id, caption=caption_text, reply_markup=reply_markup, parse_mode="Markdown")
            elif media_type == "video" and file_id:
                sent_msg = await context.bot.send_video(chat_id=query.message.chat_id, video=file_id, caption=caption_text, reply_markup=reply_markup, parse_mode="Markdown")
            elif media_type == "document" and file_id:
                sent_msg = await context.bot.send_document(chat_id=query.message.chat_id, document=file_id, caption=caption_text, reply_markup=reply_markup, parse_mode="Markdown")
            else:
                sent_msg = await context.bot.send_message(chat_id=query.message.chat_id, text=caption_text, reply_markup=reply_markup, parse_mode="Markdown")

            if sent_msg:
                context.user_data["last_media_msg_id"] = sent_msg.message_id

    # لوحة الأدمين
    elif data == "admin_panel":
        await delete_previous_media_msg(update, context)
        if not is_admin(user_id):
            return
        keyboard = [
            [InlineKeyboardButton("➕ إضافة درس جديد (نص/صورة/فيديو/ملف)", callback_data="add_lesson_start")],
            [InlineKeyboardButton("📚 إضافة كتاب / ملخص لمادة (PDF/وسائط)", callback_data="add_book_start")],
            [InlineKeyboardButton("💬 التواصل والإجابة على تلميذ", callback_data="admin_reply_start")],
            [InlineKeyboardButton("🗑️ إدارة وحذف المحتوى", callback_data="admin_delete_menu")],
            [InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data="main_menu")]
        ]
        
        try:
            await query.message.edit_text("⚙️ **لوحة تسيير الأستاذ والأدمين:**", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
        except Exception:
            await query.message.delete()
            await context.bot.send_message(chat_id=query.message.chat_id, text="⚙️ **لوحة تسيير الأستاذ والأدمين:**", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

    # قائمة الحذف
    elif data == "admin_delete_menu":
        await delete_previous_media_msg(update, context)
        if not is_admin(user_id):
            return
        keyboard = []

        for full_key, lessons in db["lessons"].items():
            for l in lessons:
                keyboard.append([InlineKeyboardButton(f"❌ حذف درس: {l['title']}", callback_data=f"del_les_{full_key}_{l['id']}")])

        for full_key, books in db.get("books", {}).items():
            for b in books:
                keyboard.append([InlineKeyboardButton(f"❌ حذف كتاب: {b['title']}", callback_data=f"del_bk_{full_key}_{b['id']}")])

        keyboard.append([InlineKeyboardButton("🔙 لوحة الأدمين", callback_data="admin_panel")])
        
        try:
            await query.message.edit_text("🗑️ **اختر العنصر المراد حذفه:**", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
        except Exception:
            await query.message.delete()
            await context.bot.send_message(chat_id=query.message.chat_id, text="🗑️ **اختر العنصر المراد حذفه:**", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

    elif data.startswith("del_les_") or data.startswith("del_bk_"):
        is_les = data.startswith("del_les_")
        prefix = "del_les_" if is_les else "del_bk_"
        parts = data.replace(prefix, "").split("_")
        full_key = f"{parts[0]}_{parts[1]}_{parts[2]}"
        item_id = parts[3]

        target_dict = db["lessons"] if is_les else db["books"]
        target_dict[full_key] = [i for i in target_dict.get(full_key, []) if str(i["id"]) != item_id]
        save_data(db)
        await query.answer("تم الحذف بنجاح!", show_alert=True)
        await button_handler(update, context)

# === 💬 التواصل والردود ===

async def contact_developer_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.message.edit_text("💬 **مدخل التواصل المباشر مع المعلم / إدارة المنصة:**\n\nأكتب استفسارك وسوف يتم إرساله فوراً:")
    return STUDENT_MESSAGE

async def student_send_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    student = update.effective_user
    msg_text = update.message.text

    admin_notification = (
        f"📩 **رسالة جديدة من تلميذ!**\n\n"
        f"👤 **الاسم:** {student.full_name}\n"
        f"🆔 **المعرف (ID):** `{student.id}`\n\n"
        f"💬 **الرسالة:**\n{msg_text}"
    )
    
    for admin_id in ADMIN_IDS:
        try:
            await context.bot.send_message(chat_id=admin_id, text=admin_notification, parse_mode="Markdown")
        except Exception:
            pass

    await update.message.reply_text("✅ تم إرسال رسالتك بنجاح! سيصلك الرد هنا قريباً.")
    return ConversationHandler.END

async def admin_reply_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not is_admin(query.from_user.id):
        return ConversationHandler.END
    await query.message.edit_text("أرسل الآن **معرف ID التلميذ** المراد الرد عليه:")
    return ADMIN_REPLY_USER_ID

async def admin_reply_user_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["target_user_id"] = update.message.text
    await update.message.reply_text("أرسل الآن **الرد / الإجابة**:")
    return ADMIN_REPLY_TEXT

async def admin_reply_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    target_id = context.user_data["target_user_id"]
    reply_msg = update.message.text

    try:
        await context.bot.send_message(
            chat_id=target_id,
            text=f"💬 **رد من المعلم / إدارة المنصة:**\n\n{reply_msg}",
            parse_mode="Markdown"
        )
        await update.message.reply_text("✅ تم إرسال الرد بنجاح!")
    except Exception as e:
        await update.message.reply_text(f"❌ متعذر إرسال الرسالة، تحقق من ID: {e}")

    return ConversationHandler.END

# === ➕ إضافة درس جديد ===

async def add_lesson_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not is_admin(query.from_user.id):
        return ConversationHandler.END

    keyboard = []
    for stage_key, stage_info in db["stages"].items():
        keyboard.append([InlineKeyboardButton(stage_info["name"], callback_data=f"addstg_les_{stage_key}")])

    await query.message.edit_text("اختر **الطور التعليمي** للدرس:", reply_markup=InlineKeyboardMarkup(keyboard))
    return ADD_LESSON_STAGE

async def add_lesson_stage(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    stage_key = query.data.replace("addstg_les_", "")
    context.user_data["add_stage"] = stage_key

    keyboard = []
    for year_key, year_info in db["stages"][stage_key]["years"].items():
        keyboard.append([InlineKeyboardButton(year_info["name"], callback_data=f"addyr_les_{year_key}")])

    await query.message.edit_text("اختر **السنة الدراسية**:", reply_markup=InlineKeyboardMarkup(keyboard))
    return ADD_LESSON_YEAR

async def add_lesson_year(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    year_key = query.data.replace("addyr_les_", "")
    context.user_data["add_year"] = year_key

    stage_key = context.user_data["add_stage"]
    subjects = db["stages"][stage_key]["years"][year_key]["subjects"]

    keyboard = []
    for sub in subjects:
        keyboard.append([InlineKeyboardButton(sub, callback_data=f"addsub_les_{sub}")])

    await query.message.edit_text("اختر **المادة الدراسية**:", reply_markup=InlineKeyboardMarkup(keyboard))
    return ADD_LESSON_SUB

async def add_lesson_sub(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["add_sub"] = query.data.replace("addsub_les_", "")

    await query.message.edit_text("أرسل الآن **عنوان الدرس**:")
    return ADD_LESSON_TITLE

async def add_lesson_title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["add_title"] = update.message.text
    await update.message.reply_text("أرسل الآن **الشرح أو الصورة / الفيديو / ملف PDF** الخاص بالدرس:")
    return ADD_LESSON_CONTENT

async def add_lesson_content(update: Update, context: ContextTypes.DEFAULT_TYPE):
    stage_key = context.user_data["add_stage"]
    year_key = context.user_data["add_year"]
    sub_name = context.user_data["add_sub"]
    title = context.user_data["add_title"]
    msg = update.message

    media_type = "text"
    file_id = None
    caption = msg.caption or msg.text or ""

    if msg.photo:
        media_type = "photo"
        file_id = msg.photo[-1].file_id
    elif msg.video:
        media_type = "video"
        file_id = msg.video.file_id
    elif msg.document:
        media_type = "document"
        file_id = msg.document.file_id

    full_key = f"{stage_key}_{year_key}_{sub_name}"

    if full_key not in db["lessons"]:
        db["lessons"][full_key] = []

    db["lessons"][full_key].append({
        "id": int(os.urandom(3).hex(), 16),
        "title": title,
        "media_type": media_type,
        "file_id": file_id,
        "content": caption
    })
    save_data(db)

    await update.message.reply_text("✅ تم نشر الدرس بنجاح للطلاب!")
    return ConversationHandler.END

# === 📚 إضافة كتاب / ملخص للمادة ===

async def add_book_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not is_admin(query.from_user.id):
        return ConversationHandler.END

    keyboard = []
    for stage_key, stage_info in db["stages"].items():
        keyboard.append([InlineKeyboardButton(stage_info["name"], callback_data=f"addstg_bk_{stage_key}")])

    await query.message.edit_text("اختر **الطور التعليمي** للكتاب / الملخص:", reply_markup=InlineKeyboardMarkup(keyboard))
    return ADD_BOOK_STAGE

async def add_book_stage(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    stage_key = query.data.replace("addstg_bk_", "")
    context.user_data["add_bk_stage"] = stage_key

    keyboard = []
    for year_key, year_info in db["stages"][stage_key]["years"].items():
        keyboard.append([InlineKeyboardButton(year_info["name"], callback_data=f"addyr_bk_{year_key}")])

    await query.message.edit_text("اختر **السنة الدراسية**:", reply_markup=InlineKeyboardMarkup(keyboard))
    return ADD_BOOK_YEAR

async def add_book_year(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    year_key = query.data.replace("addyr_bk_", "")
    context.user_data["add_bk_year"] = year_key

    stage_key = context.user_data["add_bk_stage"]
    subjects = db["stages"][stage_key]["years"][year_key]["subjects"]

    keyboard = []
    for sub in subjects:
        keyboard.append([InlineKeyboardButton(sub, callback_data=f"addsub_bk_{sub}")])

    await query.message.edit_text("اختر **المادة الدراسية** لتخصيص الكتاب لها:", reply_markup=InlineKeyboardMarkup(keyboard))
    return ADD_BOOK_SUB

async def add_book_sub(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["add_bk_sub"] = query.data.replace("addsub_bk_", "")

    await query.message.edit_text("أرسل الآن **اسم أو عنوان الكتاب/الملخص**:")
    return ADD_BOOK_TITLE

async def add_book_title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["add_bk_title"] = update.message.text
    await update.message.reply_text("أرسل الآن **ملف الـ PDF الخاص بالكتاب، أو صورته/فيديو الشرح/نص الرابط**:")
    return ADD_BOOK_CONTENT

async def add_book_content(update: Update, context: ContextTypes.DEFAULT_TYPE):
    stage_key = context.user_data["add_bk_stage"]
    year_key = context.user_data["add_bk_year"]
    sub_name = context.user_data["add_bk_sub"]
    title = context.user_data["add_bk_title"]
    msg = update.message

    media_type = "text"
    file_id = None
    caption = msg.caption or msg.text or ""

    if msg.document:
        media_type = "document"
        file_id = msg.document.file_id
    elif msg.photo:
        media_type = "photo"
        file_id = msg.photo[-1].file_id
    elif msg.video:
        media_type = "video"
        file_id = msg.video.file_id

    full_key = f"{stage_key}_{year_key}_{sub_name}"

    if "books" not in db:
        db["books"] = {}

    if full_key not in db["books"]:
        db["books"][full_key] = []

    db["books"][full_key].append({
        "id": int(os.urandom(3).hex(), 16),
        "title": title,
        "media_type": media_type,
        "file_id": file_id,
        "content": caption
    })
    save_data(db)

    await update.message.reply_text("✅ تم إضافة الكتاب/الملخص بنجاح لقسم المادة المخصص!")
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("تم إلغاء العملية.")
    return ConversationHandler.END

# === تشغيل البوت ===
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    student_contact_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(contact_developer_start, pattern="^contact_developer$")],
        states={
            STUDENT_MESSAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, student_send_message)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        per_message=False
    )

    admin_reply_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(admin_reply_start, pattern="^admin_reply_start$")],
        states={
            ADMIN_REPLY_USER_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_reply_user_id)],
            ADMIN_REPLY_TEXT: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_reply_text)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        per_message=False
    )

    add_lesson_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(add_lesson_start, pattern="^add_lesson_start$")],
        states={
            ADD_LESSON_STAGE: [CallbackQueryHandler(add_lesson_stage, pattern="^addstg_les_")],
            ADD_LESSON_YEAR: [CallbackQueryHandler(add_lesson_year, pattern="^addyr_les_")],
            ADD_LESSON_SUB: [CallbackQueryHandler(add_lesson_sub, pattern="^addsub_les_")],
            ADD_LESSON_TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_lesson_title)],
            ADD_LESSON_CONTENT: [MessageHandler((filters.TEXT | filters.PHOTO | filters.VIDEO | filters.Document.ALL) & ~filters.COMMAND, add_lesson_content)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        per_message=False
    )

    add_book_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(add_book_start, pattern="^add_book_start$")],
        states={
            ADD_BOOK_STAGE: [CallbackQueryHandler(add_book_stage, pattern="^addstg_bk_")],
            ADD_BOOK_YEAR: [CallbackQueryHandler(add_book_year, pattern="^addyr_bk_")],
            ADD_BOOK_SUB: [CallbackQueryHandler(add_book_sub, pattern="^addsub_bk_")],
            ADD_BOOK_TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_book_title)],
            ADD_BOOK_CONTENT: [MessageHandler((filters.TEXT | filters.PHOTO | filters.VIDEO | filters.Document.ALL) & ~filters.COMMAND, add_book_content)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        per_message=False
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(student_contact_conv)
    app.add_handler(admin_reply_conv)
    app.add_handler(add_lesson_conv)
    app.add_handler(add_book_conv)
    app.add_handler(CallbackQueryHandler(button_handler))

    print("🚀 البوت يعمل الآن بنجاح وبدون أي أخطاء...")
    app.run_polling()

if __name__ == "__main__":
    main()
