import json
import os
import secrets
import logging
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

logging.basicConfig(level=logging.INFO)

# === التوكن الخاص بك ===
BOT_TOKEN = "8673709137:AAHHeT3uVc17MaXJyvTX4GlAtA8si7V6bVc"
MY_USER_ID = 6985307484  # الآيدي الخاص بك للتجربة الكاملة

DATA_FILE = "school_system_data.json"

# حالات المحادثات التفاعلية
(
    ADD_TEACHER_TYPE, ADD_TEACHER_YEAR, ADD_TEACHER_SUB,
    CHANGE_PASS_SELECT, CHANGE_PASS_NEW, LOGIN_PASS,
    ADD_CONTENT_STAGE, ADD_CONTENT_YEAR, ADD_CONTENT_SUB, ADD_CONTENT_TYPE, ADD_CONTENT_TITLE, ADD_CONTENT_FILE
) = range(12)

# === الهيكلية الأساسية للنظام التعليمي الجزائري ===
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
        str(MY_USER_ID): {"role": "super_admin", "name": "المدير العام والتنفيذي"}
    },
    "passwords": {
        "admin123": {"role": "super_admin", "name": "المدير العام"}
    },
    "content": {}
}

def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if "passwords" not in data:
                    data["passwords"] = {}
                data["passwords"]["admin123"] = {"role": "super_admin", "name": "المدير العام"}
                data["users"][str(MY_USER_ID)] = {"role": "super_admin", "name": "المدير العام والتنفيذي"}
                return data
        except Exception:
            pass
    return DEFAULT_STRUCTURE

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

db = load_data()

# === تحديد الصلاحية تلقائياً للـ ID الخاص بك ===
def get_user_role(user_id):
    if str(user_id) == str(MY_USER_ID):
        return "super_admin", {"name": "المدير العام"}
    user = db["users"].get(str(user_id))
    if user:
        return user.get("role"), user
    return "student", None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    role, user_info = get_user_role(user_id)

    keyboard = [
        [InlineKeyboardButton("📚 التصفح حسب الطور والسنوات", callback_data="select_stage")],
        [InlineKeyboardButton("🔑 تسجيل الدخول بكلمة السر", callback_data="login_by_pass")]
    ]

    # إتاحة لوحة الإدارة للـ ID الخاص بك ولجميع المدراء والمدرسين
    if role in ["super_admin", "stage_manager", "primary_teacher", "middle_teacher"]:
        keyboard.append([InlineKeyboardButton("⚙️ لوحة تحكم الإدارة والأستاذ", callback_data="admin_panel")])

    reply_markup = InlineKeyboardMarkup(keyboard)
    text = f"🇩🇿 **مرحباً بك في منصة التعليم الجزائرية الشاملة** 🏫\n\nحسابك الحالي: **{role}**\nاختر من القائمة أدناه:"

    if update.callback_query:
        await update.callback_query.message.edit_text(text, reply_markup=reply_markup, parse_mode="Markdown")
    else:
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode="Markdown")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    user_id = query.from_user.id
    role, user_info = get_user_role(user_id)

    if data == "main_menu":
        await start(update, context)

    elif data == "select_stage":
        keyboard = [
            [InlineKeyboardButton("🏫 الطور الابتدائي", callback_data="stage_primary")],
            [InlineKeyboardButton("🏫 الطور المتوسط", callback_data="stage_middle")],
            [InlineKeyboardButton("🔙 العودة للقائمة الرئيسية", callback_data="main_menu")]
        ]
        await query.message.edit_text("🎓 **اختر الطور التعليمي:**", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

    elif data.startswith("stage_"):
        stage_key = data.replace("stage_", "")
        stage = db["stages"][stage_key]
        keyboard = [[InlineKeyboardButton(y_info["name"], callback_data=f"year_{stage_key}_{y_key}")] for y_key, y_info in stage["years"].items()]
        keyboard.append([InlineKeyboardButton("🔙 العودة للأطوار", callback_data="select_stage")])
        await query.message.edit_text(f"📌 **{stage['name']}**\nاختر السنة الدراسية:", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

    elif data.startswith("year_"):
        _, stage_key, year_key = data.split("_")
        year_info = db["stages"][stage_key]["years"][year_key]
        keyboard = [[InlineKeyboardButton(sub, callback_data=f"sub_{stage_key}_{year_key}_{sub}")] for sub in year_info["subjects"]]
        keyboard.append([InlineKeyboardButton("🔙 العودة للسنوات", callback_data=f"stage_{stage_key}")])
        await query.message.edit_text(f"📖 **{year_info['name']}**\nاختر المادة الدراسية:", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

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

    elif data.startswith("show_cat_"):
        parts = data.replace("show_cat_", "").split("_")
        stage_key, year_key, c_type = parts[0], parts[1], parts[-1]
        sub_name = "_".join(parts[2:-1])
        full_key = f"{stage_key}_{year_key}_{sub_name}"

        items = [i for i in db["content"].get(full_key, []) if i.get("type") == c_type]
        keyboard = [[InlineKeyboardButton(f"📄 {item['title']}", callback_data=f"view_item_{full_key}_{item['id']}")] for item in items]
        keyboard.append([InlineKeyboardButton("🔙 العودة لأقسام المادة", callback_data=f"sub_{stage_key}_{year_key}_{sub_name}")])
        
        type_str = {"video": "الفيديوهات", "photo": "الصور", "text": "الشروحات النصية", "doc": "الكتب/PDF"}.get(c_type, "")
        msg_text = f"📂 **{type_str} لمادة {sub_name}:**" if items else f"⚠️ لا توجد محتويات مضافة حالياً."
        await query.message.edit_text(msg_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

    # لوحة الإدارة (متاحة لجميع أدواره والإدارة)
    elif data == "admin_panel":
        if role == "student":
            return
        
        keyboard = []
        # السماح لجميع أجهزة الإدارة بإضافة أستاذ وعرض كلمات السر
        if role in ["super_admin", "stage_manager"]:
            keyboard.append([InlineKeyboardButton("➕ إضافة معلم / أستاذ جديد (توليد كلمة سر)", callback_data="add_teacher_start")])
            keyboard.append([InlineKeyboardButton("🔑 عرض جميع كلمات السر المولدة", callback_data="show_all_passwords")])
        
        keyboard.append([InlineKeyboardButton("➕ نشر درس / محتوى جديد", callback_data="add_content_start")])
        keyboard.append([InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data="main_menu")])

        text = f"⚙️ **لوحة تسيير النظام والتحكم ({role}):**"
        await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

    elif data == "show_all_passwords":
        if role not in ["super_admin", "stage_manager"]:
            return
        
        if not db["passwords"]:
            msg_text = "🔑 لا توجد كلمات سر مسجلة حالياً."
        else:
            msg_text = "🔑 **قائمة كلمات السر العشوائية المسجلة للأساتذة:**\n\n"
            for code, u_info in db["passwords"].items():
                role_name = u_info.get("role", "أستاذ")
                sub = u_info.get("sub", "جميع المواد")
                year = u_info.get("year", "")
                msg_text += f"• **كلمة السر:** `{code}` | {role_name} ({year} - {sub})\n"

        keyboard = [[InlineKeyboardButton("🔙 العودة للوحة الإدارة", callback_data="admin_panel")]]
        await query.message.edit_text(msg_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

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
        await update.message.reply_text(f"✅ تم التعرف عليك بنجاح! تم منحك صلاحية: **{info['role']}**\n\nاضغط /start للبدء.")
    else:
        await update.message.reply_text("❌ كلمة السر غير صحيحة!")
    return ConversationHandler.END

# === إضافة أستاذ مع توليد كلمة سر عشوائية فورية ===
async def add_teacher_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    keyboard = [
        [InlineKeyboardButton("معلم ابتدائي (سنة كاملة)", callback_data="type_primary_teacher")],
        [InlineKeyboardButton("أستاذ متوسط (مادة معينة)", callback_data="type_middle_teacher")]
    ]
    await query.message.edit_text("اختر نوع رتبة المؤطر للإنشاء وتوليد كلمة السر له:", reply_markup=InlineKeyboardMarkup(keyboard))
    return ADD_TEACHER_TYPE

async def add_teacher_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    t_type = query.data.replace("type_", "")
    context.user_data["t_type"] = t_type

    if t_type == "primary_teacher":
        keyboard = [[InlineKeyboardButton(y_info["name"], callback_data=f"tyear_primary_{y_key}")] for y_key, y_info in db["stages"]["primary"]["years"].items()]
        await query.message.edit_text("اختر السنة الدراسية لمعلم الابتدائي:", reply_markup=InlineKeyboardMarkup(keyboard))
        return ADD_TEACHER_YEAR
    else:
        keyboard = [[InlineKeyboardButton(y_info["name"], callback_data=f"tyear_middle_{y_key}")] for y_key, y_info in db["stages"]["middle"]["years"].items()]
        await query.message.edit_text("اختر السنة الدراسية بالطور المتوسط:", reply_markup=InlineKeyboardMarkup(keyboard))
        return ADD_TEACHER_YEAR

async def add_teacher_year(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    _, stg, y_key = query.data.split("_")
    context.user_data["t_stage"] = stg
    context.user_data["t_year"] = y_key

    if context.user_data["t_type"] == "middle_teacher":
        subjects = db["stages"]["middle"]["years"][y_key]["subjects"]
        keyboard = [[InlineKeyboardButton(sub, callback_data=f"tsub_{sub}")] for sub in subjects]
        await query.message.edit_text("اختر المادة الدراسية لتحديد النصاب:", reply_markup=InlineKeyboardMarkup(keyboard))
        return ADD_TEACHER_SUB
    else:
        # توليد كلمة سر عشوائية لمعلم الابتدائي
        random_pass = secrets.token_hex(3)
        user_info = {"role": "primary_teacher", "stage": "primary", "year": y_key}
        db["passwords"][random_pass] = user_info
        save_data(db)
        
        msg_text = (
            f"✅ **تم إنشاء حساب معلم ابتدائي جديد بنجاح!**\n\n"
            f"📌 **السنة الدراسية:** {y_key}\n"
            f"🔑 **كلمة السر العشوائية الخاصة به:** `{random_pass}`\n\n"
            f"اعط كلمة السر هذه للمعلم ليدخل بها من خيار تسجيل الدخول."
        )
        await query.message.edit_text(msg_text, parse_mode="Markdown")
        return ConversationHandler.END

async def add_teacher_sub(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    sub_name = query.data.replace("tsub_", "")
    
    # توليد كلمة سر عشوائية لأستاذ المتوسط
    random_pass = secrets.token_hex(3)
    user_info = {"role": "middle_teacher", "stage": "middle", "year": context.user_data["t_year"], "sub": sub_name}
    db["passwords"][random_pass] = user_info
    save_data(db)

    msg_text = (
        f"✅ **تم إنشاء حساب أستاذ متوسط جديد بنجاح!**\n\n"
        f"📖 **المادة:** {sub_name}\n"
        f"📌 **السنة:** {context.user_data['t_year']}\n"
        f"🔑 **كلمة السر العشوائية الخاصة به:** `{random_pass}`\n\n"
        f"اعط كلمة السر هذه للأستاذ ليدخل بها من خيار تسجيل الدخول."
    )
    await query.message.edit_text(msg_text, parse_mode="Markdown")
    return ConversationHandler.END

async def add_content_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    keyboard = [
        [InlineKeyboardButton("الطور الابتدائي", callback_data="cstg_primary")],
        [InlineKeyboardButton("الطور المتوسط", callback_data="cstg_middle")]
    ]
    await query.message.edit_text("اختر الطور التعليمي لنشر المحتوى:", reply_markup=InlineKeyboardMarkup(keyboard))
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
    await query.message.edit_text("اختر نوع المحتوى:", reply_markup=InlineKeyboardMarkup(keyboard))
    return ADD_CONTENT_TYPE

async def add_content_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["c_type"] = query.data.replace("ctype_", "")
    await query.message.edit_text("أرسل الآن **عنوان الدرس / المحتوى**:")
    return ADD_CONTENT_TITLE

async def add_content_title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["c_title"] = update.message.text
    await update.message.reply_text("أرسل الآن **ملف الدرس أو النص**:")
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

    await update.message.reply_text("✅ تم نشر الدرس بنجاح!")
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("تم إلغاء العملية.")
    return ConversationHandler.END

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    login_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(login_start, pattern="^login_by_pass$")],
        states={
            LOGIN_PASS: [MessageHandler(filters.TEXT & ~filters.COMMAND, login_process)]
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        per_message=False
    )

    add_teacher_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(add_teacher_start, pattern="^add_teacher_start$")],
        states={
            ADD_TEACHER_TYPE: [CallbackQueryHandler(add_teacher_type, pattern="^type_")],
            ADD_TEACHER_YEAR: [CallbackQueryHandler(add_teacher_year, pattern="^tyear_")],
            ADD_TEACHER_SUB: [CallbackQueryHandler(add_teacher_sub, pattern="^tsub_")]
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        per_message=False
    )

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

    print("🚀 البوت جاهز للتجربة الكاملة بجميع المميزات...")
    app.run_polling()

if __name__ == "__main__":
    main()
