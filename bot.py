#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Telegram-бот-справочник для КГП «Поликлиника №2 города Темиртау»
Версия: 10.0 — полное приветствие, все FAQ, все врачи с фамилиями и временем
"""

import os
import logging
from threading import Thread
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    ConversationHandler,
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

MENU, SUB_MENU, DOCTOR_SUB_MENU = range(3)

CONTACTS = {
    "address": "ул. Абая, д. 53/3, г. Темиртау (остановка «Роддом»)",
    "phone_register": "+7 (7213) 44-78-88",
    "phone_whatsapp": "+7 771 313 3654",
    "phone_support": "44-75-83",
    "phone_reception": "44-77-29",
    "schedule_weekdays": "Пн–Пт: 08:00 – 20:00",
    "schedule_saturday": "Сб: 09:00 – 15:00 (дежурные врачи)",
    "schedule_sunday": "Вс: 09:00 – 12:00 (фильтр)",
    "website": "https://pol2temirtau.kz/",
}

DEPARTMENTS = {
    "adult": "🏥 **Взрослое отделение**\n📍 1–2 этаж (каб. 101–232)\n\nПервичная медико-санитарная помощь взрослому населению.",
    "children": "🏥 **Детское отделение**\n📍 1–2 этаж (каб. 109–128, 203, 209, 215–217, 221–223, 238, 302)\n\n8 педиатрических участков.",
    "gynecology": "🏥 **Женская консультация**\n📍 4 этаж (каб. 401–403)\n\nАкушерско-гинекологическая помощь.",
    "day_hospital": "🏥 **Дневной стационар**\n📍 2–3 этаж\n\n22 терапевтические + 3 хирургических койки.",
    "diagnostics": "🫀 **Диагностика**\n📍 2 этаж (каб. 302)\n\nУЗИ, ЭКГ, ЭхоКГ, холтер, СМАД, тредмил, ФГДС, спирография, рентген, маммография, флюорография.",
    "laboratory": "🧪 **Лаборатория**\n📍 1 этаж\n\nОбщеклинические, гематологические, биохимические исследования.",
    "prevention": "📋 **Отделение профилактики**\n📍 3 этаж\n\nПсихолог, соцработник, профосмотры, лекции по ЗОЖ.",
    "emergency": "🚑 **Скорая неотложная помощь**\n📍 1 этаж\n\nЭкстренная помощь.",
    "dentistry": "🦷 **Стоматология**\n📍 2–3 этаж (каб. 215)\n\n🕐 Пн–Пт: 9:00–16:00\n🆓 Бесплатно: дети до 18 лет, беременные, инвалиды, пенсионеры.",
}

# Взрослые терапевты
ADULT_DOCTORS = {
    "Дюсупова Г.М.": "Терапевт, уч. №3, каб. 106\n🕐 Пн–Пт: 8:00–16:00",
    "Куандыкова Г.Б.": "Терапевт, уч. №4, каб. 103\n🕐 Пн–Пт: 8:00–16:00",
    "Шамиева Г.Р.": "Терапевт, уч. №5, каб. 108\n🕐 Пн–Пт: 8:00–16:00",
    "Гатин Р.Ф.": "ВОП (зам.директора), уч. №6, каб. 107\n🕐 Пн–Пт: 8:00–16:00",
}

# Взрослые узкие специалисты
ADULT_SPECIALISTS = {
    "Аллерголог": {"doctor": "Цхай О.А.", "info": "каб. 238\n🕐 Пн, Чт: 8:00–10:40"},
    "Гастроэнтеролог": {"doctor": "Бейсенова А.К.", "info": "каб. 112\n🕐 Пн–Пт: 8:00–14:00"},
    "Дерматовенеролог": {"doctor": "Коджебаш В.Н.", "info": "Зам. директора по МЧ, каб. 304\n🕐 Пн–Пт: 8:00–16:00"},
    "Инфекционист": {"doctor": "Жумабаева Н.С.", "info": "каб. 115\n🕐 Вт, Чт: 9:00–15:00"},
    "Кардиолог": {"doctor": "Кемпирбаева М.Т.", "info": "каб. 101\n🕐 Пн–Пт: 8:00–16:00"},
    "ЛОР": {"doctor": "Сыздикова А.Е.", "info": "каб. 123\n🕐 Пн–Пт: 8:00–13:00"},
    "Маммолог": {"doctor": "Аманжолова Г.Т.", "info": "каб. 118\n🕐 Ср: 14:00–17:00"},
    "Невропатолог": {"doctor": "Терехина О.Ф.", "info": "каб. 119\n🕐 Пн: 8:00–10:00, Ср: 14:00–16:00, Пт: 14:00–16:00"},
    "Онколог": {"doctor": "Мухамеджанова Д.К.", "info": "каб. 120\n🕐 Вт, Чт: 9:00–15:00"},
    "Офтальмолог": {"doctor": "Яблонская А.З.", "info": "каб. 109\n🕐 Пн–Пт: 8:00–16:00"},
    "Проктолог": {"doctor": "Ермекова Г.Н.", "info": "каб. 116\n🕐 Пн, Ср, Пт: 10:00–14:00"},
    "Профпатолог": {"doctor": "Шарипова Н.Н.", "info": "каб. 304\n🕐 Пн–Пт: 8:00–16:00"},
    "Пульмонолог": {"doctor": "Рахметова Л.Т.", "info": "каб. 117\n🕐 Пн–Пт: 8:00–14:00"},
    "Ревматолог": {"doctor": "Садыкова Г.А.", "info": "каб. 114\n🕐 Вт, Чт: 9:00–15:00"},
    "Травматолог": {"doctor": "Ахмедов У.Г.", "info": "каб. 128\n🕐 Пн, Ср, Пт: 8:00–13:00"},
    "Уролог": {"doctor": "Маликов Т.Р.", "info": "каб. 111\n🕐 Пн, Ср, Пт: 9:00–15:00"},
    "Хирург": {"doctor": "Ельцова В.Н.", "info": "каб. 105\n🕐 Пн–Пт: 8:00–16:00"},
    "Эндокринолог": {"doctor": "Сабирова Р.М.", "info": "каб. 113\n🕐 Пн–Пт: 8:00–14:00"},
    "Эндоскопист": {"doctor": "Жакенов Б.К.", "info": "каб. 130\n🕐 Пн–Пт: 8:00–15:00"},
    "Психолог": {"doctor": "Сейтказинова М.Е.", "info": "каб. 302\n🕐 Пн–Пт: 9:00–17:00"},
}

# Гинекологи
GYNECOLOGISTS = {
    "Исмайлова К.К.": "Гинеколог, уч. №1 и №3, каб. 402 (только беременные)\n🕐 Пн–Пт: 8:00–14:00",
    "Гоцадзе М.В.": "Гинеколог, уч. №2, каб. 401\n🕐 Пн–Пт: 8:00–14:00",
    "Литвинов Е.А.": "Гинеколог, уч. №1 и №3, каб. 403\n🕐 Пн–Пт: 10:00–13:00 (Чт: 10:00–12:00)",
}

# Педиатры
PEDIATRICIANS = {
    "Борисова Е.Л.": "Педиатр, каб. 110\n🕐 Пн: 8:00–11:00 | Пт: 14:00–17:00 | Ср: 15:00–18:00 | Чт: 14:00–17:00",
    "Терехина О.Ф.": "Педиатр, каб. 110\n🕐 Пн: 14:00–18:00 | Пт: 8:00–12:00 | Ср: 8:00–12:00 | Чт: 12:00–16:00",
    "Аймахан Э.": "Педиатр, каб. 217\n🕐 Пн: 11:00–14:00 | Пт: 13:00–16:00 | Ср: 11:00–14:00 | Чт: 8:00–11:00",
    "Самыш Б.": "Педиатр, каб. 216\n🕐 Пн: 13:00–15:00 | Пт: 12:00–15:00 | Ср: 14:00–17:00 | Чт: 10:00–14:00",
    "Синельникова Е.П.": "Педиатр, каб. 216\n🕐 Пн: 8:00–11:00 | Пт: 8:00–12:00 | Ср: 8:00–12:00 | Чт: 8:00–12:00",
    "Журавлева М.Г.": "Педиатр, каб. 113\n🕐 Пн: 13:00–19:00 | Пт: 12:00–17:00 | Ср: 8:00–14:00 | Чт: 8:00–14:00",
    "Бек М.": "Педиатр, каб. 223\n🕐 Пн: 16:30–19:30 | Пт: 13:30–16:30 | Ср: 16:30–19:30 | Чт: 13:30–16:30",
    "Абенова А.С.": "Педиатр, каб. 222/221\n🕐 Пн: 13:30–16:30 | Пт: 11:00–14:00 | Ср: 13:30–16:30 | Чт: 11:00–14:00",
    "Ибрагимов Э.": "Педиатр, каб. 221\n🕐 Пн: 8:00–11:00 | Пт: 11:00–14:00 | Ср: 8:00–11:00 | Чт: 8:00–11:00",
    "Бакулиаркина Д.Т.": "Педиатр, каб. 216\n🕐 Пн: 8:00–11:00 | Пт: 11:00–14:00 | Ср: 14:00–17:00 | Чт: 11:00–14:00",
    "Бегманова Д.Т.": "Педиатр, каб. 216\n🕐 Пн: 17:00–20:00 | Пт: 17:00–20:00 | Ср: 17:00–20:00 | Чт: 17:00–20:00",
    "Оспанов А.": "Педиатр, каб. 221\n🕐 Пн: 14:00–17:00 | Пт: 8:00–11:00 | Ср: 8:00–11:00 | Чт: 17:00–20:00",
    "Ахметжанова М.Е.": "Педиатр, каб. 221\n🕐 Пн: 14:00–17:00 | Пт: 8:00–11:00 | Ср: 8:00–11:00 | Чт: 17:00–20:00",
}

# Детские узкие специалисты
CHILD_SPECIALISTS = {
    "Отоларинголог (ЛОР)": {"doctor": "Солодухина П.В.", "info": "каб. 405\n🕐 Пн–Пт: 8:00–16:30"},
    "ЭКГ": {"doctor": "Абдираманова С.Д.", "info": "каб. 122\n🕐 Пн–Пт: 8:00–12:00"},
    "Ортопед": {"doctor": "Кошанова А.А.", "info": "каб. 128\n🕐 Пт: 14:00–16:45"},
    "Окулист": {"doctor": "Яблонская А.З.", "info": "каб. 109\n🕐 Пн–Пт: 8:00–16:00"},
    "Аллерголог": {"doctor": "Цхай О.А.", "info": "каб. 238\n🕐 Пн, Чт: 8:00–10:40"},
    "УЗИ": {"doctor": "Парикожа Л.В.", "info": "каб. 209\n🕐 9:30–10:30 (ежедневно)"},
    "Рентген": {"doctor": "Шуховцов В.В.", "info": "каб. 302\n🕐 8:00–10:00 (ежедневно)"},
    "Аудиология": {"doctor": "Васильева Л.М.", "info": "каб. 121\n🕐 14:00–16:00 (ежедневно)"},
    "Травматолог": {"doctor": "Ахмедов У.Г.", "info": "каб. 128\n🕐 Пн, Ср, Пт: 8:00–13:00"},
    "Невропатолог": {"doctor": "Терехина О.Ф.", "info": "каб. 119\n🕐 Пн: 8:00–10:00 | Ср: 14:00–16:00 | Пт: 14:00–16:00"},
    "ЛОР / Хирург": {"doctor": "Сыздиков Н.Е.", "info": "каб. 123\n🕐 ЛОР: 8:00–13:00 (ежедн.)\n🕐 Хирург: 13:30–16:30 (ежедн.)"},
    "Стоматолог": {"doctor": "Борисов Р.О.", "info": "каб. 215\n🕐 Вт, Чт: 9:00–13:00"},
    "Фтизиатр": {"doctor": "Пономарев Д.В.", "info": "каб. 203\n🕐 Чт: 9:00–13:00"},
    "Массаж": {"doctor": "Ордабаева Д.", "info": "каб. 503\n🕐 9:30–16:30 (Пн–Пт)"},
}

PRICES = [
    ("Прием: Терапевт", "2 470 ₸"),
    ("Прием: Педиатр", "2 470 ₸"),
    ("Прием: ВОП", "2 868 ₸"),
    ("Консультация: Гинеколог", "4 296 ₸"),
    ("Консультация: Хирург", "4 357 ₸"),
    ("Консультация: Кардиолог", "4 111 ₸"),
    ("Консультация: Невролог", "4 068 ₸"),
    ("Консультация: Офтальмолог", "4 068 ₸"),
    ("Консультация: Эндокринолог", "4 068 ₸"),
    ("Консультация: Уролог", "4 068 ₸"),
    ("Консультация: ЛОР", "4 068 ₸"),
    ("Анализ мочи по Нечипоренко", "593 ₸"),
    ("Копрограмма", "731 ₸"),
    ("Общий анализ крови", "1 744 ₸"),
    ("ЭКГ (12 отведений)", "1 711 ₸"),
    ("Эхокардиография", "4 498 ₸"),
    ("УЗИ: печень, желчный пузырь, ПЖ, селезенка", "6 017 ₸"),
    ("УЗИ: Почки", "3 084 ₸"),
    ("УЗИ: Щитовидная железа", "3 894 ₸"),
    ("УЗИ: Молочные железы", "3 873 ₸"),
    ("ФГДС", "6 072 ₸"),
    ("Рентгенография: органов грудной клетки", "1 853 ₸"),
    ("Мамография (4 снимка)", "7 506 ₸"),
    ("Флюорография", "863 ₸"),
    ("Массаж: Воротниковой зоны", "992 ₸"),
    ("Массаж: Пояснично-крестцовой области", "1 171 ₸"),
]

def make_main_keyboard():
    keyboard = [
        [InlineKeyboardButton("👨‍⚕️ Наши врачи", callback_data="doctors_main")],
        [InlineKeyboardButton("🏥 Отделения", callback_data="departments")],
        [InlineKeyboardButton("📞 Контакты и график", callback_data="contacts")],
        [InlineKeyboardButton("💰 Услуги и цены", callback_data="prices")],
        [InlineKeyboardButton("❓ Частые вопросы", callback_data="faq")],
    ]
    return InlineKeyboardMarkup(keyboard)

def make_doctors_main_keyboard():
    keyboard = [
        [InlineKeyboardButton("👨 Взрослые терапевты", callback_data="doctors_adult")],
        [InlineKeyboardButton("👨‍⚕️ Взрослые узкие специалисты", callback_data="doctors_adult_specialists")],
        [InlineKeyboardButton("👩 Гинекологи", callback_data="doctors_gynecology")],
        [InlineKeyboardButton("👶 Детские педиатры", callback_data="doctors_pediatricians")],
        [InlineKeyboardButton("🧸 Детские узкие специалисты", callback_data="doctors_child_specialists")],
        [InlineKeyboardButton("🔙 Назад", callback_data="back_main")],
    ]
    return InlineKeyboardMarkup(keyboard)

def make_doctor_list_keyboard(doctors_dict, callback_prefix):
    keyboard = []
    names = list(doctors_dict.keys())
    for i in range(0, len(names), 2):
        row = []
        row.append(InlineKeyboardButton(names[i], callback_data=f"{callback_prefix}_{i}"))
        if i + 1 < len(names):
            row.append(InlineKeyboardButton(names[i+1], callback_data=f"{callback_prefix}_{i+1}"))
        keyboard.append(row)
    keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="doctors_back")])
    return InlineKeyboardMarkup(keyboard)

def make_departments_keyboard():
    keyboard = [
        [InlineKeyboardButton("👨‍⚕️ Взрослое отделение", callback_data="dep_adult")],
        [InlineKeyboardButton("👶 Детское отделение", callback_data="dep_children")],
        [InlineKeyboardButton("👩 Женская консультация", callback_data="dep_gynecology")],
        [InlineKeyboardButton("🏨 Дневной стационар", callback_data="dep_day_hospital")],
        [InlineKeyboardButton("🫀 Диагностика", callback_data="dep_diagnostics")],
        [InlineKeyboardButton("🧪 Лаборатория", callback_data="dep_laboratory")],
        [InlineKeyboardButton("📋 Отделение профилактики", callback_data="dep_prevention")],
        [InlineKeyboardButton("🚑 Скорая помощь", callback_data="dep_emergency")],
        [InlineKeyboardButton("🦷 Стоматология", callback_data="dep_dentistry")],
        [InlineKeyboardButton("🔙 Назад", callback_data="back_main")],
    ]
    return InlineKeyboardMarkup(keyboard)

def make_back_keyboard():
    return InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Главное меню", callback_data="back_main")]])

def make_prices_keyboard():
    keyboard = [
        [InlineKeyboardButton("✅ Да, я прикреплен", callback_data="price_attached")],
        [InlineKeyboardButton("❌ Нет, не прикреплен", callback_data="price_not_attached")],
        [InlineKeyboardButton("🔙 Назад", callback_data="back_main")],
    ]
    return InlineKeyboardMarkup(keyboard)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.effective_user
    welcome_text = (
        f"👋 Здравствуйте, {user.first_name}!\n\n"
        "🏥 Добро пожаловать в справочный бот\n"
        "**КГП «Поликлиника №2 города Темиртау»**\n\n"
        "Я помогу вам быстро найти информацию о работе поликлиники.\n"
        "Выберите нужный раздел в меню ниже:"
    )
    await update.message.reply_text(
        welcome_text,
        reply_markup=make_main_keyboard(),
        parse_mode="Markdown"
    )
    return MENU

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "doctors_main":
        await query.edit_message_text(
            "👨‍⚕️ **Выберите категорию врачей:**\n\n"
            "_Данные из актуальных графиков приема на июнь 2026 года_",
            reply_markup=make_doctors_main_keyboard(),
            parse_mode="Markdown"
        )
        return SUB_MENU

    if data == "departments":
        await query.edit_message_text(
            "🏥 **Выберите отделение поликлиники:**\n\n"
            "_Информация об этажах и кабинетах указана в описании каждого отделения_",
            reply_markup=make_departments_keyboard(),
            parse_mode="Markdown"
        )
        return SUB_MENU

    if data == "contacts":
        contacts_text = (
            "📞 **Контакты поликлиники №2 г. Темиртау**\n\n"
            f"🏛 **Адрес:** {CONTACTS['address']}\n\n"
            f"📞 **Регистратура:** {CONTACTS['phone_register']}\n"
            f"💬 **WhatsApp:** {CONTACTS['phone_whatsapp']}\n"
            f"🔧 **Служба поддержки пациентов:** {CONTACTS['phone_support']}\n"
            f"🏢 **Приемная директора:** {CONTACTS['phone_reception']} (каб. 304)\n\n"
            "🕐 **График работы:**\n"
            f"• {CONTACTS['schedule_weekdays']}\n"
            f"• {CONTACTS['schedule_saturday']}\n"
            f"• {CONTACTS['schedule_sunday']}\n\n"
            f"🌐 **Официальный сайт:** {CONTACTS['website']}"
        )
        await query.edit_message_text(
            contacts_text,
            reply_markup=make_back_keyboard(),
            parse_mode="Markdown"
        )
        return SUB_MENU

    if data == "prices":
        await query.edit_message_text(
            "💰 **Услуги и цены**\n\n"
            "Прежде чем показать прейскурант, уточните, пожалуйста:\n"
            "Вы являетесь **прикрепленным пациентом** нашей поликлиники?\n\n"
            "_Для прикрепленных пациентов все услуги в рамках ГОБМП и ОСМС — бесплатны._",
            reply_markup=make_prices_keyboard(),
            parse_mode="Markdown"
        )
        return SUB_MENU

    if data == "faq":
        faq_text = (
            "❓ **Частые вопросы:**\n\n"
            "**Как записаться к врачу?**\n"
            "По телефону регистратуры +7 (7213) 44-78-88 или через инфомат в холле поликлиники.\n\n"
            "**Как вызвать врача на дом?**\n"
            "По телефону регистратуры +7 (7213) 44-78-88.\n\n"
            "**Как прикрепиться к поликлинике?**\n"
            "Онлайн через портал egov.kz или лично в регистратуре.\n\n"
            "**Нужен ли полис для приема?**\n"
            "В Казахстане действует система ОСМС. Статус застрахованности можно проверить на fms.kz, в приложении Qoldau 24/7 или в Telegram-боте @SaqtandyryBot.\n\n"
            "**Как оплачивать взносы в ОСМС, работая в двух местах?**\n"
            "Совокупный доход не должен превышать 10 МЗП (850 000 тенге в 2024 г.). Взносы (2% от дохода) и отчисления (3%) рассчитываются с учетом выплат с первого места работы.\n\n"
            "**Как добраться до поликлиники?**\n"
            "Маршрутное транспортное средство (МТС) № 01, 05 до остановки «Роддом»."
        )
        await query.edit_message_text(
            faq_text,
            reply_markup=make_back_keyboard(),
            parse_mode="Markdown"
        )
        return SUB_MENU

    if data == "doctors_adult":
        await query.edit_message_text(
            "👨 **Взрослые терапевты:**",
            reply_markup=make_doctor_list_keyboard(ADULT_DOCTORS, "adult_doc"),
            parse_mode="Markdown"
        )
        return DOCTOR_SUB_MENU

    if data == "doctors_adult_specialists":
        await query.edit_message_text(
            "👨‍⚕️ **Взрослые узкие специалисты:**\n\n"
            "Выберите специальность:",
            reply_markup=make_doctor_list_keyboard(ADULT_SPECIALISTS, "adult_spec"),
            parse_mode="Markdown"
        )
        return DOCTOR_SUB_MENU

    if data == "doctors_gynecology":
        await query.edit_message_text(
            "👩 **Гинекологи:**",
            reply_markup=make_doctor_list_keyboard(GYNECOLOGISTS, "gyn_doc"),
            parse_mode="Markdown"
        )
        return DOCTOR_SUB_MENU

    if data == "doctors_pediatricians":
        await query.edit_message_text(
            "👶 **Участковые педиатры:**",
            reply_markup=make_doctor_list_keyboard(PEDIATRICIANS, "ped_doc"),
            parse_mode="Markdown"
        )
        return DOCTOR_SUB_MENU

    if data == "doctors_child_specialists":
        await query.edit_message_text(
            "🧸 **Детские узкие специалисты:**\n\n"
            "Выберите специальность:",
            reply_markup=make_doctor_list_keyboard(CHILD_SPECIALISTS, "child_spec"),
            parse_mode="Markdown"
        )
        return DOCTOR_SUB_MENU

    if data == "doctors_back":
        await query.edit_message_text(
            "👨‍⚕️ **Выберите категорию врачей:**",
            reply_markup=make_doctors_main_keyboard(),
            parse_mode="Markdown"
        )
        return SUB_MENU

    if data.startswith("adult_doc_"):
        index = int(data.split("_")[2])
        names = list(ADULT_DOCTORS.keys())
        if 0 <= index < len(names):
            name = names[index]
            info = ADULT_DOCTORS[name]
            await query.edit_message_text(
                f"👨 **{name}**\n\n{info}\n\n"
                f"📞 Запись: {CONTACTS['phone_register']}",
                reply_markup=make_doctor_list_keyboard(ADULT_DOCTORS, "adult_doc"),
                parse_mode="Markdown"
            )
        return DOCTOR_SUB_MENU

    if data.startswith("adult_spec_"):
        index = int(data.split("_")[2])
        names = list(ADULT_SPECIALISTS.keys())
        if 0 <= index < len(names):
            spec_name = names[index]
            spec_data = ADULT_SPECIALISTS[spec_name]
            doctor_name = spec_data["doctor"]
            info = spec_data["info"]
            await query.edit_message_text(
                f"👨‍⚕️ **{spec_name}**\n\n👤 Врач: {doctor_name}\n{info}\n\n"
                f"📞 Запись: {CONTACTS['phone_register']}",
                reply_markup=make_doctor_list_keyboard(ADULT_SPECIALISTS, "adult_spec"),
                parse_mode="Markdown"
            )
        return DOCTOR_SUB_MENU

    if data.startswith("gyn_doc_"):
        index = int(data.split("_")[2])
        names = list(GYNECOLOGISTS.keys())
        if 0 <= index < len(names):
            name = names[index]
            info = GYNECOLOGISTS[name]
            await query.edit_message_text(
                f"👩 **{name}**\n\n{info}\n\n"
                f"📞 Запись: {CONTACTS['phone_register']}",
                reply_markup=make_doctor_list_keyboard(GYNECOLOGISTS, "gyn_doc"),
                parse_mode="Markdown"
            )
        return DOCTOR_SUB_MENU

    if data.startswith("ped_doc_"):
        index = int(data.split("_")[2])
        names = list(PEDIATRICIANS.keys())
        if 0 <= index < len(names):
            name = names[index]
            info = PEDIATRICIANS[name]
            await query.edit_message_text(
                f"👶 **{name}**\n\n{info}\n\n"
                f"📞 Запись: {CONTACTS['phone_register']}",
                reply_markup=make_doctor_list_keyboard(PEDIATRICIANS, "ped_doc"),
                parse_mode="Markdown"
            )
        return DOCTOR_SUB_MENU

    if data.startswith("child_spec_"):
        index = int(data.split("_")[2])
        names = list(CHILD_SPECIALISTS.keys())
        if 0 <= index < len(names):
            spec_name = names[index]
            spec_data = CHILD_SPECIALISTS[spec_name]
            doctor_name = spec_data["doctor"]
            info = spec_data["info"]
            await query.edit_message_text(
                f"🧸 **{spec_name}**\n\n👤 Врач: {doctor_name}\n{info}\n\n"
                f"📞 Запись: {CONTACTS['phone_register']}",
                reply_markup=make_doctor_list_keyboard(CHILD_SPECIALISTS, "child_spec"),
                parse_mode="Markdown"
            )
        return DOCTOR_SUB_MENU

    if data.startswith("dep_"):
        dep_key = data.split("_")[1]
        dep_info = DEPARTMENTS.get(dep_key, "Информация временно отсутствует.")
        await query.edit_message_text(
            dep_info,
            reply_markup=make_departments_keyboard(),
            parse_mode="Markdown"
        )
        return SUB_MENU

    if data == "price_attached":
        await query.edit_message_text(
            "✅ **Отлично!**\n\n"
            "Для вас, как для прикрепленного пациента, "
            "все услуги в рамках ГОБМП и ОСМС оказываются **бесплатно**.\n\n"
            f"📞 Запись: {CONTACTS['phone_register']}\n\n"
            "ℹ️ Платные услуги (по прейскуранту) предназначены для:\n"
            "• Неприкрепленных пациентов\n"
            "• Иностранных граждан\n"
            "• Услуг, не входящих в ГОБМП",
            reply_markup=make_back_keyboard(),
            parse_mode="Markdown"
        )
        return SUB_MENU

    if data == "price_not_attached":
        text = "ℹ️ **Прейскурант платных услуг (выборочно) на 2026 год:**\n\n"
        for name, price in PRICES:
            text += f"• {name} — {price}\n"
        text += f"\n🌐 Полный перечень: {CONTACTS['website']}"
        await query.edit_message_text(
            text,
            reply_markup=make_back_keyboard(),
            parse_mode="Markdown"
        )
        return SUB_MENU

    if data == "back_main":
        await query.edit_message_text(
            "🏥 **Главное меню**\n\nВыберите нужный раздел:",
            reply_markup=make_main_keyboard(),
            parse_mode="Markdown"
        )
        return MENU

    await query.edit_message_text(
        "⚠️ Что-то пошло не так. Попробуйте снова.",
        reply_markup=make_back_keyboard()
    )
    return MENU

def main() -> None:
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        raise ValueError("TELEGRAM_BOT_TOKEN не найден! Установите переменную окружения.")

    application = Application.builder().token(token).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            MENU: [CallbackQueryHandler(button_handler)],
            SUB_MENU: [CallbackQueryHandler(button_handler)],
            DOCTOR_SUB_MENU: [CallbackQueryHandler(button_handler)],
        },
        fallbacks=[CommandHandler("start", start)],
    )

    application.add_handler(conv_handler)
    print("🤖 Бот запущен!")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

# ============================================================
# ВЕБ-СЕРВЕР ДЛЯ "СЕРДЦЕБИЕНИЯ"
# ============================================================

app = Flask(__name__)

@app.route('/')
def health_check():
    return "I'm alive!", 200

def run_web_server():
    app.run(host="0.0.0.0", port=8080)

# Запускаем веб-сервер в отдельном потоке (чтобы он не мешал боту)
Thread(target=run_web_server).start()

if __name__ == "__main__":
    main()
