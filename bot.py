import json
import os
import secrets
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

# === الإعدادات الأساسية ===
BOT_TOKEN = "8647094829:AAGod0gFDj9zmDVO2kiuDT2ynL68HBBUZjY"
SUPER_ADMIN_ID = 6985307484  # المدير العام (أنت)

DATA_FILE = "school_system_data.json"

# حالات المحادثات التفاعلية
(
    ADD_TEACHER_TYPE, ADD_TEACHER_STAGE, ADD_TEACHER_YEAR, ADD_TEACHER_SUB, ADD_TEACHER_ID, ADD_TEACHER_PASS,
    LOGIN_PASS,
    ADD_CONTENT_STAGE, ADD_CONTENT_YEAR, ADD_CONTENT_SUB, ADD_CONTENT_TYPE, ADD_CONTENT_TITLE, ADD_CONTENT_FILE,
    STUDENT_MSG
) = range(13)

# === البيانات الأساسية للنظام التعليمي الجزائري ===
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
    "users": {
        str(SUPER_ADMIN_ID): {"role": "super_admin", "name": "المدير العام"}
    },
    "passwords": {}, # word: user_data
    "content": {}    # key: list of items
}

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return DEFAULT_STRUCTURE

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

db = load_data()

# === التحقق من الصلاحيات ===
def get_user_role(user_id):
    user = db["users"].get(str(user_id))
    if user:
        return user.get("role"), user
    if user_id == SUPER_ADMIN_ID:
        return "super_admin", {"name": "المدير العام"}
    return "student", None

async def delete_previous_msg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg_id = context.user_data.get("last_msg_id")
    if msg_id:
        try:
            await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=msg_id)
        except:
            pass
        context.user_data["last_msg_id"] = None

# === الواجهة الرئيسية ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await delete_previous_msg(update, context)
    user_id = update.effective_user.id
    role, user_info = get_user_role(user_id)

    keyboard = [
        [InlineKeyboardButton("📚 التصفح حسب الطور والسنة", callback_data="select_stage")],
        [InlineKeyboardButton("🔑 تسجيل الدخول بكلمة السر", callback_data="login_by_pass")]
    ]

    if role in ["super_admin", "stage_manager", "primary_teacher", "middle_teacher"]:
        keyboard.append([InlineKeyboardButton("⚙️ لوحة تحكم الإدارة والتأطير", callback_data="admin_panel")])

    reply_markup = InlineKeyboardMarkup(keyboard)
    text = f"🇩🇿 **مرحباً بك في منصة التعليم الجزائرية الشاملة** 🏫\n\nحسابك الحالي: **{role}**\nاختر من القائمة أدناه:"

    if update.callback_query:
        try:
            await update.callback_query.message.edit_text(text, reply_markup=reply_markup, parse_mode="Markdown")
        except:
            await update.callback_query.message.delete()
            msg = await context.bot.send_message(chat_id=update.effective_chat.id, text=text, reply_markup=reply_markup, parse_mode="Markdown")
            context.user_data["last_msg_id"] = msg.message_id
    else:
        msg = await update.message.reply_text(text, reply_markup=reply_markup, parse_mode="Markdown")
        context.user_data["last_msg_id"] = msg.message_id

# === معالجة التصفح العادي ===
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    user_id = query.from_user.id
    role, user_info = get_user_role(user_id)

    if data == "main_menu":
        await start(update, context)

    # 1. اختيار الطور
    elif data == "select_stage":
        keyboard = [
            [InlineKeyboardButton("🏫 الطور الابتدائي", callback_data="stage_primary")],
            [InlineKeyboardButton("🏫 الطور المتوسط", callback_data="stage_middle")],
            [InlineKeyboardButton("🔙 العودة للقائمة الرئيسية", callback_data="main_menu")]
        ]
        await query.message.edit_text("🎓 **اختر الطور التعليمي:**", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

    # 2. اختيار السنة
    elif data.startswith("stage_"):
        stage_key = data.replace("stage_", "")
        stage = db["stages"][stage_key]
        keyboard = []
        for y_key, y_info in stage["years"].items():
            keyboard.append([InlineKeyboardButton(y_info["name"], callback_data=f"year_{stage_key}_{y_key}")])
        keyboard.append([InlineKeyboardButton("🔙 العودة للجميع", callback_data="select_stage")])
        await query.message.edit_text(f"📌 **{stage['name']}**\nاختر السنة الدراسية:", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

    # 3. اختيار المادة
    elif data.startswith("year_"):
        _, stage_key, year_key = data.split("_")
        year_info = db["stages"][stage_key]["years"][year_key]
        keyboard = []
        for sub in year_info["subjects"]:
            keyboard.append([InlineKeyboardButton(sub, callback_data=f"sub_{stage_key}_{year_key}_{sub}")])
        keyboard.append([InlineKeyboardButton("🔙 العودة للسنوات", callback_data=f"stage_{stage_key}")])
        await query.message.edit_text(f"📖 **{year_info['name']}**\nاختر المادة الدراسية:", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

    # 4. عرض خيارات المحتوى المخصص (فيديو / صورة / شرح / ملخص)
    elif data.startswith("sub_"):
        parts = data.split("_", 3)
        stage_key, year_key, sub_name = parts[1], parts[2], parts[3]
        full_key = f"{stage_key}_{year_key}_{sub_name}"

        keyboard = [
            [InlineKeyboardButton("🎥 الفيديوهات الشارحة", callback_data=f"show_cat_{full_key}_video")],
            [InlineKeyboardButton("🖼️ الصور والمخططات", callback_data=f"show_cat_{full_key}_photo")],
            [InlineKeyboardButton("📝 الدروس والشروحات النصية", callback_data=f"show_cat_{full_key}_text")],
            [InlineKeyboardButton("📚 الكتب والملخصات PDF", callback_data=f"show_cat_{full_key}_doc")],
            [InlineKeyboardButton("🔙 العودة للمواد", callback_data=f"year_{stage_key}_{year_key}")]
        ]
        await query.message.edit_text(f"📌 **مادة {sub_name}**\nاختر نوع المحتوى المراد تصفحه:", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

    # 5. عرض قائمة المحتوى حسب التصنيف
    elif data.startswith("show_cat_"):
        parts = data.replace("show_cat_", "").split("_")
        stage_key, year_key, c_type = parts[0], parts[1], parts[-1]
        sub_name = "_".join(parts[2:-1])
        full_key = f"{stage_key}_{year_key}_{sub_name}"

        items = [i for i in db["content"].get(full_key, []) if i.get("type") == c_type]
        keyboard = []
        for item in items:
            keyboard.append([InlineKeyboardButton(f"📄 {item['title']}", callback_data=f"view_item_{full_key}_{item['id']}")])
        
        keyboard.append([InlineKeyboardButton("🔙 العودة لأقسام المادة", callback_data=f"sub_{stage_key}_{year_key}_{sub_name}")])
        
        type_str = {"video": "الفيديوهات", "photo": "الصور", "text": "الشروحات النصية", "doc": "الكتب/PDF"}.get(c_type, "")
        msg_text = f"📂 **{type_str} لمادة {sub_name}:**" if items else f"⚠️ لا توجد محتويات مضافة حالياً في هذا القسم."
        await query.message.edit_text(msg_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

    # 6. فتح ومصادقة الدرس
    elif data.startswith("view_item_"):
        parts = data.replace("view_item_", "").split("_")
        item_id = parts[-1]
        stage_key, year_key = parts[0], parts[1]
        sub_name = "_".join(parts[2:-1])
        full_key = f"{stage_key}_{year_key}_{sub_name}"

        items = db["content"].get(full_key, [])
        item = next((i for i in items if str(i["id"]) == item_id), None)

        if item:
            keyboard = [[InlineKeyboardButton("🔙 العودة للقسم", callback_data=f"sub_{stage_key}_{year_key}_{sub_name}")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            caption = f"📌 **{sub_name}**\n📝 **العنوان:** {item['title']}\n\n{item.get('text', '')}"

            await query.message.delete()
            if item["type"] == "photo":
                sent = await context.bot.send_photo(chat_id=query.message.chat_id, photo=item["file_id"], caption=caption, reply_markup=reply_markup, parse_mode="Markdown")
            elif item["type"] == "video":
                sent = await context.bot.send_video(chat_id=query.message.chat_id, video=item["file_id"], caption=caption, reply_markup=reply_markup, parse_mode="Markdown")
            elif item["type"] == "doc":
                sent = await context.bot.send_document(chat_id=query.message.chat_id, document=item["file_id"], caption=caption, reply_markup=reply_markup, parse_mode="Markdown")
            else:
                sent = await context.bot.send_message(chat_id=query.message.chat_id, text=caption, reply_markup=reply_markup, parse_mode="Markdown")
            
            context.user_data["last_msg_id"] = sent.message_id

    # ⚙️ لوحة الإدارة المتقدمة
    elif data == "admin_panel":
        if role == "student":
            return
        
        keyboard = []
        if role in ["super_admin", "stage_manager"]:
            keyboard.append([InlineKeyboardButton("➕ إضافة معلم / أستاذ جديد", callback_data="add_teacher_start")])
        
        keyboard.append([InlineKeyboardButton("➕ نشر درس / محتوى جديد", callback_data="add_content_start")])
        keyboard.append([InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data="main_menu")])

        text = f"⚙️ **لوحة التحكم الخاصة بك ({role}):**\n\nيمكنك إضافة الأساتذة والمعلمين وتسيير المحتوى حسب صلاحياتك."
        await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

# === 🔑 تسجيل الدخول بكلمة السر ===
async def login_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.message.edit_text("🔑 **أدخل كلمة السر الخاصة بك كمعلم / مدير:**")
    return LOGIN_PASS

async def login_process(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pass_code = update.message.text.strip()
    user_id = update.effective_user.id

    if pass_code in db["passwords"]:
        info = db["passwords"][pass_code]
        db["users"][str(user_id)] = info
        save_data(db)
        await update.message.reply_text(f"✅ تم التعرف عليك بنجاح! تم منحك صلاحية: **{info['role']}**\n\nاضغط /start لفتح اللوحة.")
    else:
        await update.message.reply_text("❌ كلمة السر غير صحيحة!")
    return ConversationHandler.END

# === ➕ إضافة معلم / أستاذ (حسب النظام الجزائري) ===
async def add_teacher_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    role, _ = get_user_role(query.from_user.id)
    
    keyboard = []
    if role == "super_admin":
        keyboard.append([InlineKeyboardButton("مدير طور (ابتدائي/متوسط)", callback_data="type_stage_manager")])
    keyboard.append([InlineKeyboardButton("معلم ابتدائي (سنة كاملة)", callback_data="type_primary_teacher")])
    keyboard.append([InlineKeyboardButton("أستاذ متوسط (مادة معينة)", callback_data="type_middle_teacher")])

    await query.message.edit_text("اختر **رتبة/نوع المؤطر** المراد إضافته:", reply_markup=InlineKeyboardMarkup(keyboard))
    return ADD_TEACHER_TYPE

async def add_teacher_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    t_type = query.data.replace("type_", "")
    context.user_data["t_type"] = t_type

    if t_type == "primary_teacher":
        keyboard = []
        for y_key, y_info in db["stages"]["primary"]["years"].items():
            keyboard.append([InlineKeyboardButton(y_info["name"], callback_data=f"tyear_primary_{y_key}")])
        await query.message.edit_text("اختر **السنة الدراسية** التي يدرسها معلم الابتدائي:", reply_markup=InlineKeyboardMarkup(keyboard))
        return ADD_TEACHER_YEAR

    elif t_type == "middle_teacher":
        keyboard = []
        for y_key, y_info in db["stages"]["middle"]["years"].items():
            keyboard.append([InlineKeyboardButton(y_info["name"], callback_data=f"tyear_middle_{y_key}")])
        await query.message.edit_text("اختر **السنة الدراسية** في الطور المتوسط:", reply_markup=InlineKeyboardMarkup(keyboard))
        return ADD_TEACHER_YEAR

    elif t_type == "stage_manager":
        keyboard = [
            [InlineKeyboardButton("الطور الابتدائي", callback_data="tstg_primary")],
            [InlineKeyboardButton("الطور المتوسط", callback_data="tstg_middle")]
        ]
        await query.message.edit_text("اختر الطور التابع لإدارة المدير:", reply_markup=InlineKeyboardMarkup(keyboard))
        return ADD_TEACHER_STAGE

async def add_teacher_year(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    _, stg, y_key = query.data.split("_")
    context.user_data["t_stage"] = stg
    context.user_data["t_year"] = y_key

    if context.user_data["t_type"] == "middle_teacher":
        subjects = db["stages"]["middle"]["years"][y_key]["subjects"]
        keyboard = []
        for sub in subjects:
            keyboard.append([InlineKeyboardButton(sub, callback_data=f"tsub_{sub}")])
        await query.message.edit_text("اختر **المادة الدراسية** التي يدرسها الأستاذ:", reply_markup=InlineKeyboardMarkup(keyboard))
        return ADD_TEACHER_SUB
    else:
        await query.message.edit_text("أرسل الآن **معرف (ID) التلجرام الخاص بالمدرس** (أو اكتب 0 لإنشاء كلمة سر فقط):")
        return ADD_TEACHER_ID

async def add_teacher_sub(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["t_sub"] = query.data.replace("tsub_", "")
    await query.message.edit_text("أرسل الآن **معرف (ID) التلجرام الخاص بالأستاذ** (أو اكتب 0):")
    return ADD_TEACHER_ID

async def add_teacher_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    t_id = update.message.text.strip()
    context.user_data["t_id"] = t_id
    
    # توليد كلمة سر أوتوماتيكية
    random_pass = secrets.token_hex(3)
    context.user_data["t_pass"] = random_pass

    t_type = context.user_data["t_type"]
    user_info = {
        "role": t_type,
        "stage": context.user_data.get("t_stage"),
        "year": context.user_data.get("t_year"),
        "sub": context.user_data.get("t_sub")
    }

    if t_id != "0":
        db["users"][t_id] = user_info
    
    db["passwords"][random_pass] = user_info
    save_data(db)

    msg = (
        f"✅ **تم إنشاء حساب المؤطر بنجاح!**\n\n"
        f"👤 **الرتبة:** {t_type}\n"
        f"🔑 **كلمة السر الخاصة به:** `{random_pass}`\n\n"
        f"قم بإعطاء كلمة السر هذه للمدرس ليقوم بإدخالها في البوت والبدء بالنشر."
    )
    await update.message.reply_text(msg, parse_mode="Markdown")
    return ConversationHandler.END

# === ➕ إضافة درس ومحتوى جديد ===
async def add_content_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    role, info = get_user_role(user_id)

    if role == "primary_teacher":
        context.user_data["c_stage"] = "primary"
        context.user_data["c_year"] = info["year"]
        
        subjects = db["stages"]["primary"]["years"][info["year"]]["subjects"]
        keyboard = [[InlineKeyboardButton(s, callback_data=f"csub_{s}")] for s in subjects]
        await query.message.edit_text("اختر **المادة الدراسية** لرفع الدرس بها:", reply_markup=InlineKeyboardMarkup(keyboard))
        return ADD_CONTENT_SUB

    elif role == "middle_teacher":
        context.user_data["c_stage"] = "middle"
        context.user_data["c_year"] = info["year"]
        context.user_data["c_sub"] = info["sub"]
        
        keyboard = [
            [InlineKeyboardButton("🎥 فيديو", callback_data="ctype_video"), InlineKeyboardButton("🖼️ صورة", callback_data="ctype_photo")],
            [InlineKeyboardButton("📝 شرح نصي", callback_data="ctype_text"), InlineKeyboardButton("📚 PDF / كتاب", callback_data="ctype_doc")]
        ]
        await query.message.edit_text(f"مادة **{info['sub']}** - اختر **نوع المحتوى**:", reply_markup=InlineKeyboardMarkup(keyboard))
        return ADD_CONTENT_TYPE

    else:
        # للمدراء (إمكانية اختيار كل الأطوار)
        keyboard = [
            [InlineKeyboardButton("الطور الابتدائي", callback_data="cstg_primary")],
            [InlineKeyboardButton("الطور المتوسط", callback_data="cstg_middle")]
        ]
        await query.message.edit_text("اختر الطور التعليمي:", reply_markup=InlineKeyboardMarkup(keyboard))
        return ADD_CONTENT_STAGE

async def add_content_stage(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    stg = query.data.replace("cstg_", "")
    context.user_data["c_stage"] = stg

    keyboard = [[InlineKeyboardButton(y["name"], callback_data=f"cyear_{k}")] for k, y in db["stages"][stg]["years"].items()]
    await query.message.edit_text("اختر السنة الدراسية:", reply_markup=InlineKeyboardMarkup(keyboard))
    return ADD_CONTENT_YEAR

async def add_content_year(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    y_key = query.data.replace("cyear_", "")
    context.user_data["c_year"] = y_key
    stg = context.user_data["c_stage"]

    subjects = db["stages"][stg]["years"][y_key]["subjects"]
    keyboard = [[InlineKeyboardButton(s, callback_data=f"csub_{s}")] for s in subjects]
    await query.message.edit_text("اختر المادة الدراسية:", reply_markup=InlineKeyboardMarkup(keyboard))
    return ADD_CONTENT_SUB

async def add_content_sub(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["c_sub"] = query.data.replace("csub_", "")

    keyboard = [
        [InlineKeyboardButton("🎥 فيديو", callback_data="ctype_video"), InlineKeyboardButton("🖼️ صورة", callback_data="ctype_photo")],
        [InlineKeyboardButton("📝 شرح نصي", callback_data="ctype_text"), InlineKeyboardButton("📚 PDF / كتاب", callback_data="ctype_doc")]
    ]
    await query.message.edit_text("اختر **نوع المحتوى** المرفق:", reply_markup=InlineKeyboardMarkup(keyboard))
    return ADD_CONTENT_TYPE

async def add_content_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["c_type"] = query.data.replace("ctype_", "")
    await query.message.edit_text("أرسل الآن **عنوان المحتوى/الدرس**:")
    return ADD_CONTENT_TITLE

async def add_content_title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["c_title"] = update.message.text
    c_type = context.user_data["c_type"]
    
    if c_type == "text":
        await update.message.reply_text("أرسل الآن **نص الشرح الكامل** للدرس:")
    else:
        await update.message.reply_text(f"أرسل الآن **ملف الـ {c_type}** المرفق مع الدرس:")
    return ADD_CONTENT_FILE

async def add_content_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    c_type = context.user_data["c_type"]
    stg, y_key, sub = context.user_data["c_stage"], context.user_data["c_year"], context.user_data["c_sub"]
    
    full_key = f"{stg}_{y_key}_{sub}"
    file_id = None
    text_content = msg.caption or msg.text or ""

    if msg.photo:
        file_id = msg.photo[-1].file_id
    elif msg.video:
        file_id = msg.video.file_id
    elif msg.document:
        file_id = msg.document.file_id

    if full_key not in db["content"]:
        db["content"][full_key] = []

    db["content"][full_key].append({
        "id": int(os.urandom(3).hex(), 16),
        "title": context.user_data["c_title"],
        "type": c_type,
        "file_id": file_id,
        "text": text_content
    })
    save_data(db)

    await update.message.reply_text("✅ تم نشر المحتوى بنجاح في قسم المادة المحدد!")
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("تم إلغاء العملية.")
    return ConversationHandler.END

# === تشغيل النظام ===
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # محادثة تسجيل الدخول
    login_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(login_start, pattern="^login_by_pass$")],
        states={
            LOGIN_PASS: [MessageHandler(filters.TEXT & ~filters.COMMAND, login_process)]
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        per_message=False
    )

    # محادثة إضافة أستاذ
    add_teacher_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(add_teacher_start, pattern="^add_teacher_start$")],
        states={
            ADD_TEACHER_TYPE: [CallbackQueryHandler(add_teacher_type, pattern="^type_")],
            ADD_TEACHER_YEAR: [CallbackQueryHandler(add_teacher_year, pattern="^tyear_")],
            ADD_TEACHER_SUB: [CallbackQueryHandler(add_teacher_sub, pattern="^tsub_")],
            ADD_TEACHER_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_teacher_id)]
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        per_message=False
    )

    # محادثة إضافة محتوى
    add_content_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(add_content_start, pattern="^add_content_start$")],
        states={
            ADD_CONTENT_STAGE: [CallbackQueryHandler(add_content_stage, pattern="^cstg_")],
            ADD_CONTENT_YEAR: [CallbackQueryHandler(add_content_year, pattern="^cyear_")],
            ADD_CONTENT_SUB: [CallbackQueryHandler(add_content_sub, pattern="^csub_")],
            ADD_CONTENT_TYPE: [CallbackQueryHandler(add_content_type, pattern="^ctype_")],
            ADD_CONTENT_TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_content_title)],
            ADD_CONTENT_FILE: [MessageHandler((filters.TEXT | filters.PHOTO | filters.VIDEO | filters.Document.ALL) & ~filters.COMMAND, add_content_file)]
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        per_message=False
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(login_conv)
    app.add_handler(add_teacher_conv)
    app.add_handler(add_content_conv)
    app.add_handler(CallbackQueryHandler(button_handler))

    print("🚀 المنصة التعليمية الجزائرية جاهزة وتعمل الآن...")
    app.run_polling()

if __name__ == "__main__":
    main()
