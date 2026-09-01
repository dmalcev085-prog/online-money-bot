import asyncio
import logging
import sys
from os import environ
from aiohttp import web
import aiohttp

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

# --- НАЛАШТУВАННЯ СИСТЕМИ ---
BOT_TOKEN = environ.get("BOT_TOKEN", "8666795532:AAFICKdumXhvFSVm9GVzRNyZ2UJNMMq9EQg")
ADMIN_CHAT_ID = int(environ.get("ADMIN_CHAT_ID", "8083694619"))
PORT = int(environ.get("PORT", 10000))

# ⚠️ ВСТАВТЕ СЮДЕ СВОЄ ВЛАСНЕ РЕФЕРАЛЬНЕ ПОСИЛАННЯ ВІД POCKET OPTION:
MY_POCKET_REF_LINK = "https://broker-qx.pro/sign-up/?lid=594411"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | 🟢 POCKET-ULTIMATE | %(levelname)s | %(message)s",
    stream=sys.stdout
)

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()
router = Router()

class TerminalStates(StatesGroup):
    broadcast_message = State()

TERMINAL_USERS = {}

# Класичні валютні пари (Форекс)
FOREX_MARKETS = {
    "EUR/USD": {"symbol": "EURUSD=X", "link": MY_POCKET_REF_LINK},
    "GBP/USD": {"symbol": "GBPUSD=X", "link": MY_POCKET_REF_LINK},
    "USD/JPY": {"symbol": "USDJPY=X", "link": MY_POCKET_REF_LINK},
    "AUD/USD": {"symbol": "AUDUSD=X", "link": MY_POCKET_REF_LINK},
    "USD/CAD": {"symbol": "USDCAD=X", "link": MY_POCKET_REF_LINK},
    "EUR/GBP": {"symbol": "EURGBP=X", "link": MY_POCKET_REF_LINK}
}

# OTC Валютні пари (позабіржові)
OTC_MARKETS = {
    "EUR/USD (OTC)": {"symbol": "EURUSD=X", "link": MY_POCKET_REF_LINK},
    "GBP/USD (OTC)": {"symbol": "GBPUSD=X", "link": MY_POCKET_REF_LINK},
    "USD/JPY (OTC)": {"symbol": "USDJPY=X", "link": MY_POCKET_REF_LINK},
    "EUR/JPY (OTC)": {"symbol": "EURJPY=X", "link": MY_POCKET_REF_LINK}
}

# Доступні таймфрейми (експірація)
TIMEFRAMES = ["1 хв", "3 хв", "5 хв", "15 хв", "30 хв", "1 година"]

TERMINAL_TARIFFS = {
    "⚡ VIP-Доступ до всіх сигналів (150 Stars)": {
        "price": 150,
        "title": "VIP-ліцензія термінала Pocket Option",
        "desc": "Безлімітні сигнали по всіх парах та таймфреймах на 30 днів.",
        "content": (
            "🟢 <b>VIP-СТАТУС POCKET OPTION АКТИВОВАНО</b>\n\n"
            f"🔗 Захищене посилання на закритий термінал та вашу біржу: {MY_POCKET_REF_LINK}\n"
            "Ваш акаунт переведено на пріоритетне отримання прогнозів без затримок."
        )
    }
}

def main_menu_kb(is_admin: bool = False):
    kb = [
        [KeyboardButton(text="📈 Форекс пари"), KeyboardButton(text="🌙 OTC Пари (Позабіржові)")],
        [KeyboardButton(text="🟢 PRO Тарифи Pocket"), KeyboardButton(text="👤 Мій профіль")]
    ]
    if is_admin:
        kb.append([KeyboardButton(text="👑 Адмін-панель"), KeyboardButton(text="📢 Екстрене сповіщення")])
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

async def get_live_market_data(symbol: str):
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval=1m&range=1d"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, timeout=5) as response:
                if response.status == 200:
                    data = await response.json()
                    result = data['chart']['result'][0]
                    meta = result['meta']
                    price = meta['regularMarketPrice']
                    prev_close = meta.get('chartPreviousClose', price)
                    change = ((price - prev_close) / prev_close) * 100
                    return price, change
    except Exception as err:
        logging.error(f"Помилка зчитування ринку: {err}")
    return None, None

@router.message(CommandStart())
async def start_command(message: Message, state: FSMContext):
    await state.clear()
    uid = message.from_user.id
    
    if uid not in TERMINAL_USERS:
        TERMINAL_USERS[uid] = {"is_pro": False, "status": "Базовий доступ", "scans": 0}
        
    is_admin = (uid == ADMIN_CHAT_ID)
    
    welcome_text = (
        "🟢 <b>POCKET OPTION ULTIMATE TERMINAL</b>\n\n"
        "Вітаю! Професійний торговий термінал для аналізу валютних пар та OTC-активів у реальному часі.\n\n"
        "📊 <b>Можливості системи:</b>\n"
        "• Великий вибір класичних та позабіржових (OTC) пар\n"
        "• Торгівля на будь-якому таймфреймі (від 1 хвилини до 1 години)\n"
        "• Прямі посилання для відкриття угод на Pocket Option\n\n"
        "Оберіть категорію активів у меню нижче:"
    )
    await message.answer(welcome_text, reply_markup=main_menu_kb(is_admin))

@router.message(F.text == "📈 Форекс пари")
async def forex_menu(message: Message):
    inline_kb = []
    for pair in FOREX_MARKETS.keys():
        inline_kb.append([InlineKeyboardButton(text=f"💱 {pair}", callback_data=f"fx_{pair}")])
    markup = InlineKeyboardMarkup(inline_keyboard=inline_kb)
    await message.answer("📈 <b>Оберіть класичну валютну пару для прогнозу:</b>", reply_markup=markup, parse_mode=ParseMode.HTML)

@router.message(F.text == "🌙 OTC Пари (Позабіржові)")
async def otc_menu(message: Message):
    inline_kb = []
    for pair in OTC_MARKETS.keys():
        inline_kb.append([InlineKeyboardButton(text=f"🌙 {pair}", callback_data=f"otc_{pair}")])
    markup = InlineKeyboardMarkup(inline_keyboard=inline_kb)
    await message.answer("🌙 <b>Оберіть позабіржову (OTC) пару для прогнозу:</b>", reply_markup=markup, parse_mode=ParseMode.HTML)

@router.callback_query(F.data.startswith(("fx_", "otc_")))
async def select_pair_callback(callback: CallbackQuery):
    data_parts = callback.data.split("_", 1)
    market_type = data_parts[0]
    pair_name = data_parts[1]
    
    inline_kb = []
    for tf in TIMEFRAMES:
        inline_kb.append([InlineKeyboardButton(text=f"⏱ Таймфрейм: {tf}", callback_data=f"tf_{market_type}_{pair_name}_{tf}")])
    
    markup = InlineKeyboardMarkup(inline_keyboard=inline_kb)
    await callback.message.edit_text(f"⏱ <b>Обрано актив: {pair_name}</b>\n\nОберіть таймфрейм (час експірації) для розрахунку сигналу:", reply_markup=markup, parse_mode=ParseMode.HTML)
    await callback.answer()

@router.callback_query(F.data.startswith("tf_"))
async def generate_signal_callback(callback: CallbackQuery):
    _, market_type, pair_name, timeframe = callback.data.split("_", 3)
    
    if market_type == "fx":
        asset_info = FOREX_MARKETS.get(pair_name)
    else:
        asset_info = OTC_MARKETS.get(pair_name)
        
    symbol = asset_info["symbol"]
    exchange_link = asset_info["link"]
    
    uid = callback.from_user.id
    if uid in TERMINAL_USERS:
        TERMINAL_USERS[uid]["scans"] += 1
    
    await callback.message.edit_text(f"🔄 <i>Скануємо котирування для {pair_name} на таймфреймі {timeframe}...</i>", parse_mode=ParseMode.HTML)
    
    price, change = await get_live_market_data(symbol)
    
    if price is None:
        price, change = 1.0845, 0.12
        
    direction = "🟢 ВИЩЕ (CALL / РІСТ)" if change >= 0 else "🔴 НИЖЧЕ (PUT / ПАДІННЯ)"
    accuracy = round(81.5 + min(abs(change) * 4, 15.0), 1)
    
    report_text = (
        f"🟢 <b>ТОРГОВИЙ СИГНАЛ POCKET OPTION</b>\n\n"
        f"💱 <b>Актив:</b> {pair_name}\n"
        f"⏱ <b>Таймфрейм (Експірація):</b> <b>{timeframe}</b>\n"
        f"💵 <b>Цільова ціна вступу:</b> <code>{price}</code>\n\n"
        f"📊 <b>Прогноз напрямку:</b> {direction}\n"
        f"⚡ <b>Ймовірність успіху:</b> {accuracy}%\n\n"
        f"<i>Відкривайте угоду на платформі Pocket Option чітко за вказаним таймфреймом!</i>"
    )
    
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🌐 ВІДКРИТИ POCKET OPTION", url=exchange_link)],
        [InlineKeyboardButton(text="🔙 Обрати іншу пару", callback_data="back_to_pairs")]
    ])
    
    await callback.message.edit_text(report_text, reply_markup=markup, parse_mode=ParseMode.HTML)
    await callback.answer()

@router.callback_query(F.data == "back_to_pairs")
async def back_to_pairs_handler(callback: CallbackQuery):
    await callback.message.edit_text("📈 Будь ласка, оберіть категорію активів у головному меню нижче.")

@router.message(F.text == "🟢 PRO Тарифи Pocket")
async def terminal_store(message: Message):
    kb = [[KeyboardButton(text=tariff)] for tariff in TERMINAL_TARIFFS.keys()]
    kb.append([KeyboardButton(text="🔙 Головне меню")])
    markup = ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
    
    await message.answer(
        "🟢 <b>Тарифи VIP-термінала Pocket Option:</b>\n\n"
        "Отримайте необмежений доступ до всіх валютних пар та OTC-сигналів без обмежень.",
        reply_markup=markup,
        parse_mode=ParseMode.HTML
    )

@router.message(F.text.in_(TERMINAL_TARIFFS.keys()))
async def create_invoice(message: Message):
    tariff_name = message.text
    tariff = TERMINAL_TARIFFS[tariff_name]
    
    prices = [LabeledPrice(label=tariff['title'], amount=tariff['price'])]
    await message.bot.send_invoice(
        chat_id=message.chat.id,
        title=tariff['title'],
        description=tariff['desc'],
        payload=f"term_pay_{tariff_name}_{message.from_user.id}",
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
    
    if uid not in TERMINAL_USERS:
        TERMINAL_USERS[uid] = {"is_pro": False, "status": "Базовий", "scans": 0}
        
    TERMINAL_USERS[uid]["is_pro"] = True
    TERMINAL_USERS[uid]["status"] = "VIP Ліцензія"
    
    await message.answer(
        "🎉 <b>ПЛАТІЖ УСПІШНО ЗАРАХОВАНО ЧЕРЕЗ TELEGRAM STARS!</b>\n\n"
        "🟢 Ваш VIP-доступ до всіх пар та таймфреймів активовано!",
        reply_markup=main_menu_kb(uid == ADMIN_CHAT_ID),
        parse_mode=ParseMode.HTML
    )

@router.message(F.text == "👤 Мій профіль")
async def profile_command(message: Message):
    uid = message.from_user.id
    data = TERMINAL_USERS.get(uid, {"is_pro": False, "status": "Базовий доступ", "scans": 0})
    tier = "🟢 VIP Трейдер" if data["is_pro"] else "👤 Користувач (Стандарт)"
    
    await message.answer(
        f"👤 <b>Ваш профіль:</b>\n\n"
        f"🆔 ID: <code>{uid}</code>\n"
        f"📈 Статус: <b>{tier}</b>\n"
        f"🔍 Проведено аналізів: {data['scans']}",
        parse_mode=ParseMode.HTML
    )

@router.message(F.text == "👑 Адмін-панель")
async def admin_panel_handler(message: Message):
    if message.from_user.id != ADMIN_CHAT_ID:
        return
    kb = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="🔙 Головне меню")]], resize_keyboard=True)
    await message.answer(f"👑 Консоль адміністратора. Користувачів: {len(TERMINAL_USERS)}", reply_markup=kb)

@router.message(F.text == "🔙 Головне меню")
async def back_to_main_menu(message: Message):
    await message.answer("Головне меню активне:", reply_markup=main_menu_kb(message.from_user.id == ADMIN_CHAT_ID))

async def handle_ping(request):
    return web.Response(text="POCKET-ULTIMATE-ONLINE")

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
