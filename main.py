Import asyncio
import logging
import sys
from os import environ
from aiohttp import web

from aiogram import Bot, Dispatcher, F, Router
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.client.default import DefaultBotProperties

# --- КОНФІГУРАЦІЯ ТА НАЛАШТУВАННЯ ---
BOT_TOKEN = environ.get("BOT_TOKEN", "8666795532:AAFICKdumXhvFSVm9GVzRNyZ2UJNMMq9EQg")
ADMIN_CHAT_ID = int(environ.get("ADMIN_CHAT_ID", "8083694619"))
PORT = int(environ.get("PORT", 10000))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | 🇺🇦 ONLINE-MONEY-UA | %(levelname)s | %(message)s",
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

def main_menu_kb(is_admin: bool = False):
    kb = [
        [KeyboardButton(text="⚡ Заробити кошти (Тап)"), KeyboardButton(text="👤 Мій профіль")],
        [KeyboardButton(text="👥 Партнерська програма"), KeyboardButton(text="💳 Вивести кошти")]
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
            "referrals": 0
        }
        
    is_admin = (uid == ADMIN_CHAT_ID)
    
    welcome_text = (
        "🇺🇦 <b>Вітаємо у проєкті Гроші Онлайн UA!</b>\n\n"
        "📈 Це офіційний сервіс цифрового заробітку та бонусних винагород у Telegram.\n"
        "• Виконуйте активність (тапи)\n"
        "• Запрошуйте друзів за посиланням\n"
        "• Замовляйте виплати на банківські карти та гаманці\n\n"
        "Оберіть потрібний розділ у меню нижче:"
    )
    await message.answer(welcome_text, reply_markup=main_menu_kb(is_admin))

@router.message(F.text == "⚡ Заробити кошти (Тап)")
async def earn_taps(message: Message):
    uid = message.from_user.id
    if uid not in USERS_DATA:
        USERS_DATA[uid] = {"balance": 0.0, "taps_count": 0, "wallet": "Не вказано", "referrals": 0}
        
    USERS_DATA[uid]["balance"] += 0.50  # 0.50 грн за клік або бал
    USERS_DATA[uid]["taps_count"] += 1
    
    balance = USERS_DATA[uid]["balance"]
    
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🚀 НАТИСНУТИ ЩЕ (+0.50 грн)", callback_data="do_tap_action")]
    ])
    
    await message.answer(
        f"⚡ <b>Активність зараховано!</b>\n\n"
        f"💰 Ваш баланс: <b>{balance:.2f} UAH</b>\n"
        f"📊 Всього кліків: {USERS_DATA[uid]['taps_count']}",
        reply_markup=markup,
        parse_mode=ParseMode.HTML
    )

@router.callback_query(F.data == "do_tap_action")
async def callback_tap_handler(callback: CallbackQuery):
    uid = callback.from_user.id
    if uid not in USERS_DATA:
        USERS_DATA[uid] = {"balance": 0.0, "taps_count": 0, "wallet": "Не вказано", "referrals": 0}
        
    USERS_DATA[uid]["balance"] += 0.50
    USERS_DATA[uid]["taps_count"] += 1
    
    balance = USERS_DATA[uid]["balance"]
    
    try:
        await callback.message.edit_text(
            f"⚡ <b>Активність зараховано!</b>\n\n"
            f"💰 Ваш баланс: <b>{balance:.2f} UAH</b>\n"
            f"📊 Всього кліків: {USERS_DATA[uid]['taps_count']}",
            reply_markup=callback.message.reply_markup,
            parse_mode=ParseMode.HTML
        )
    except Exception:
        pass
    await callback.answer("+0.50 UAH зараховано на баланс!")

@router.message(F.text == "👤 Мій профіль")
async def profile_command(message: Message):
    uid = message.from_user.id
    data = USERS_DATA.get(uid, {"balance": 0.0, "taps_count": 0, "wallet": "Не вказано", "referrals": 0})
    
    profile_text = (
        f"👤 <b>Ваш особистий кабінет:</b>\n\n"
        f"🆔 ID користувача: <code>{uid}</code>\n"
        f"💰 Доступний баланс: <b>{data['balance']:.2f} UAH</b>\n"
        f"⚡ Успішних активностей: {data['taps_count']}\n"
        f"👥 Запрошено партнерів: {data['referrals']}\n"
        f"💳 Реквізити для виплат: <code>{data['wallet']}</code>"
    )
    await message.answer(profile_text, parse_mode=ParseMode.HTML)

@router.message(F.text == "👥 Партнерська програма")
async def referral_command(message: Message):
    me = await message.bot.get_me()
    ref_link = f"https://t.me/{me.username}?start=ref_{message.from_user.id}"
    
    text = (
        "👥 <b>Партнерська програма (Реферали):</b>\n\n"
        "Запрошуйте друзів, знайомих або діліться посиланням у соцмережах. За кожного активного користувача ви отримуєте бонусні кошти на свій баланс!\n\n"
        f"🔗 <b>Ваше індивідуальне посилання:</b>\n<code>{ref_link}</code>"
    )
    await message.answer(text, parse_mode=ParseMode.HTML)

@router.message(F.text == "💳 Вивести кошти")
async def payout_request(message: Message, state: FSMContext):
    uid = message.from_user.id
    data = USERS_DATA.get(uid, {"balance": 0.0})
    
    min_limit = 200.0
    if data["balance"] < min_limit:
        return await message.answer(
            f"⚠️ <b>Мінімальна сума для виводу коштів — {min_limit} UAH.</b>\n"
            f"Наразі на вашому балансі: {data['balance']:.2f} UAH.\n"
            f"Продовжуйте заробляти та запрошувати друзів!",
            parse_mode=ParseMode.HTML
        )
        
    await message.answer(
        "💳 <b>Оформлення заявки на виплату:</b>\n\n"
        "Будь ласка, введіть номер вашої банківської картки (приват / моно) або USDT-гаманець:",
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
    
    # Скидаємо баланс після подачі заявки
    USERS_DATA[uid]["balance"] = 0.0
    await state.clear()
    
    await message.answer(
        "✅ <b>Заявку на виплату успішно зареєстровано!</b>\n"
        "Кошти надійдуть на вказані реквізити після перевірки адміністратором (протягом 24 годин).",
        reply_markup=main_menu_kb(uid == ADMIN_CHAT_ID),
        parse_mode=ParseMode.HTML
    )
    
    if ADMIN_CHAT_ID:
        try:
            await bot.send_message(
                ADMIN_CHAT_ID,
                f"🚨 <b>НОВА ЗАЯВКА НА ВИПЛАТУ!</b>\n\n"
                f"👤 ID гравця: <code>{uid}</code>\n"
                f"💰 Сума: <b>{amount:.2f} UAH</b>\n"
                f"💳 Картка/Гаманець: {wallet}",
                parse_mode=ParseMode.HTML
            )
        except Exception:
            pass

# --- АДМІНІСТРАТИВНА ПАНЕЛЬ ---
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
    await message.answer("👑 Панель управління адміністратора:", reply_markup=kb)

@router.message(F.text == "📊 Статистика платформи")
async def admin_statistics(message: Message):
    if message.from_user.id != ADMIN_CHAT_ID:
        return
    total_users = len(USERS_DATA)
    total_money = sum(d["balance"] for d in USERS_DATA.values())
    
    await message.answer(
        f"📊 <b>Статистика сервісу:</b>\n\n"
        f"👥 Всього користувачів у базі: <b>{total_users}</b>\n"
        f"💰 Загальний невиплачений баланс гравців: <b>{total_money:.2f} UAH</b>",
        parse_mode=ParseMode.HTML
    )

@router.message(F.text == "📢 Масова розсилка")
async def broadcast_start_handler(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_CHAT_ID:
        return
    await message.answer(
        "📢 Введіть текст повідомлення для розсилки всім користувачам:",
        reply_markup=ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="❌ Скасувати")]], resize_keyboard=True)
    )
    await state.set_state(UserState.broadcast_message)

@router.message(UserState.broadcast_message)
async def broadcast_execute_handler(message: Message, state: FSMContext):
    if message.text == "❌ Скасувати":
        await state.clear()
        return await message.answer("Розсилку скасовано.", reply_markup=main_menu_kb(True))
        
    text = message.text
    await state.clear()
    
    sent_count = 0
    for uid in USERS_DATA.keys():
        try:
            await bot.send_message(uid, f"📢 <b>ІНФОРМАЦІЯ ВІД СЕРВІСУ:</b>\n\n{text}", parse_mode=ParseMode.HTML)
            sent_count += 1
        except Exception:
            pass
            
    await message.answer(f"✅ Розсилку успішно завершено! Доставлено: {sent_count}/{len(USERS_DATA)}", reply_markup=main_menu_kb(True))

@router.message(F.text == "🔙 Головне меню")
async def back_to_main_menu(message: Message):
    await message.answer("Головне меню активне:", reply_markup=main_menu_kb(message.from_user.id == ADMIN_CHAT_ID))

# --- ВЕБ-СЕРВЕР ДЛЯ ПІДТРИМКИ AKTИBHOCTI НА RENDER ---
async def handle_ping(request):
    return web.Response(text="ONLINE-MONEY-UA-ACTIVE")

async def start_web_server():
    app = web.Application()
    app.router.add_get("/", handle_ping)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()
    logging.info(f"Web server started on port {PORT}")

# --- ЗАПУСК СИСТЕМИ ---
async def main():
    dp.include_router(router)
    asyncio.create_task(start_web_server())
    
    logging.info("BOT STARTED SUCCESSFULLY IN UKRAINE.")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Bot stopped.")
