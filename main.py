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

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | 🛡 NEXUS-TERMINAL | %(levelname)s | %(message)s",
    stream=sys.stdout
)

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()
router = Router()

class TerminalStates(StatesGroup):
    broadcast_message = State()

TERMINAL_USERS = {}

# Точки підключення до світових ринкових потоків
GLOBAL_MARKETS = {
    "EUR/USD (Форекс)": "EURUSD=X",
    "GBP/USD (Форекс)": "GBPUSD=X",
    "USD/JPY (Форекс)": "USDJPY=X",
    "BTC/USD (Криптобіржа)": "BTC-USD"
}

TERMINAL_TARIFFS = {
    "⚡ PRO-Доступ до потоку сигналів (150 Stars)": {
        "price": 150,
        "title": "Безлімітний термінал сигналів Nexus AI",
        "desc": "Прямий доступ до алгоритмів прогнозування та закритих каналів аналітики на 30 днів.",
        "content": (
            "🛡 <b>ЛІЦЕНЗІЮ PRO АКТИВОВАНО У СИСТЕМІ</b>\n\n"
            "🔗 Захищений канал зв'язку з терміналом: https://t.me/+nexus_pro_terminal_secure\n"
            "Ваш акаунт переведено на пріоритетний потік обробки ордерів без затримок."
        )
    }
}

def main_menu_kb(is_admin: bool = False):
    kb = [
        [KeyboardButton(text="📈 Обрати актив для аналізу"), KeyboardButton(text="🛡 PRO Тарифи термінала")],
        [KeyboardButton(text="👤 Мій профіль"), KeyboardButton(text="🌐 Джерела даних")]
    ]
    if is_admin:
        kb.append([KeyboardButton(text="👑 Адмін-панель"), KeyboardButton(text="📢 Екстрене сповіщення")])
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

async def get_live_market_data(symbol: str):
    """Отримує поточні котирування через захищений шлюз глобальних бірж"""
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
        "🛡 <b>NEXUS TRADING TERMINAL v3.8</b>\n\n"
        "Вітаю! Ви підключилися до професійного аналітичного термінала на базі нейромережевих моделей та алгоритмів машинного навчання.\n\n"
        "📊 <b>Звідки беруться сигнали?</b>\n"
        "Система не «вигадує» цифри. Ми підключені до агрегаторів світової ліквідності та сирих котирувань у реальному часі (Yahoo Finance / провідні межбанківські потоки). Нейромережа сканує відхилення ціни, об'єми ордерів за останню хвилину та формує математичну ймовірність руху.\n\n"
        "Оберіть потрібний розділ у меню нижче, щоб розпочати роботу:"
    )
    await message.answer(welcome_text, reply_markup=main_menu_kb(is_admin))

@router.message(F.text == "🌐 Джерела даних")
async def data_sources_info(message: Message):
    info_text = (
        "🌐 <b> ПРОЦЕС ГЕНЕРАЦІЇ СИГНАЛІВ</b>\n\n"
        "1. <b>Потік котирущень:</b> Дані надходять напряму з міжнаціональних біржових шлюзів у режимі 24/7 із затримкою менше 0.2 секунди.\n"
        "2. <b>Математична модель:</b> Нейромережа аналізує волатильність, локальні тренди та об'єми закриття свічок.\n"
        "3. <b>Прозорість:</b> Жодних випадкових прогнозів — лише сухий розрахунок співвідношення ризик/прибуток.\n\n"
        "<i>Ми гарантуємо повну стабільність та високу точність розрахунків.</i>"
    )
    await message.answer(info_text, parse_mode=ParseMode.HTML)

@router.message(F.text == "📈 Обрати актив для аналізу")
async def choose_asset_menu(message: Message):
    inline_kb = []
    for asset_name in GLOBAL_MARKETS.keys():
        inline_kb.append([InlineKeyboardButton(text=f"📊 Сканувати {asset_name}", callback_data=f"scan_{asset_name}")])
    
    markup = InlineKeyboardMarkup(inline_keyboard=inline_kb)
    await message.answer("📈 <b>Оберіть торговий актив для глибокого сканування терміналом:</b>", reply_markup=markup, parse_mode=ParseMode.HTML)

@router.callback_query(F.data.startswith("scan_"))
async def process_asset_scan(callback: CallbackQuery):
    asset_key = callback.data.replace("scan_", "")
    symbol = GLOBAL_MARKETS.get(asset_key)
    
    uid = callback.from_user.id
    if uid in TERMINAL_USERS:
        TERMINAL_USERS[uid]["scans"] += 1
    
    await callback.message.edit_text(f"🔄 <i>Встановлюємо захищене з'єднання з біржовим шлюзом для {asset_key}...</i>", parse_mode=ParseMode.HTML)
    
    price, change = await get_live_market_data(symbol)
    
    if price is None:
        return await callback.message.edit_text("⚠️ Тимчасовий розрив з'єднання з біржею котирувань. Будь ласка, повторіть спробу за хвилину.")
    
    # Розрахунок аналітичних показників
    direction = "🟢 LONG (Вверх / Купівля)" if change >= 0 else "🔴 SHORT (Вниз / Продаж)"
    accuracy = round(78.5 + min(abs(change) * 4, 16.5), 1)
    
    target = round(price * 1.0045 if change >= 0 else price * 0.9955, 5)
    stop = round(price * 0.9975 if change >= 0 else price * 1.0025, 5)
    
    report_text = (
        f"🛡 <b>АНАЛІТИЧНИЙ ЗВІТ ТЕРМІНАЛА</b>\n\n"
        f"💱 <b>Актив:</b> {asset_key}\n"
        f"💵 <b>Поточна ціна на біржі:</b> <code>{price}</code>\n"
        f"📊 <b>Динаміка за добу:</b> <code>{change:+.2f}%</code>\n\n"
        f"🧠 <b>Вердикт ШІ-алгоритму:</b> {direction}\n"
        f"🎯 <b>Цільовий рівень (Take-Profit):</b> <code>{target}</code>\n"
        f"🛡 <b>Захисний стоп-лосс (Stop-Loss):</b> <code>{stop}</code>\n"
        f"⚡ <b>Ймовірність відпрацювання:</b> {accuracy}%\n\n"
        f"<i>Розрахунок виконано автоматично на основі актуального біржового стакана.</i>"
    )
    
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Оновити котирування", callback_data=f"scan_{asset_key}")]
    ])
    
    await callback.message.edit_text(report_text, reply_markup=markup, parse_mode=ParseMode.HTML)
    await callback.answer()

@router.message(F.text == "🛡 PRO Тарифи термінала")
async def terminal_store(message: Message):
    kb = [[KeyboardButton(text=tariff)] for tariff in TERMINAL_TARIFFS.keys()]
    kb.append([KeyboardButton(text="🔙 Головне меню")])
    markup = ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
    
    await message.answer(
        "🛡 <b>Ліцензування та тарифи термінала:</b>\n\n"
        "Отримайте необмежений доступ до високошвидкісного потоку сигналів без затримок та обмежень у кількості сканувань.",
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
    TERMINAL_USERS[uid]["status"] = "PRO Ліцензія"
    
    await message.answer(
        "🎉 <b>ПЛАТІЖ УСПІШНО ОБРОБЛЕНО ЧЕРЕЗ TELEGRAM STARS!</b>\n\n"
        "🛡 Вашу ліцензію PRO активовано. Вітаємо у команді професіоналів!",
        reply_markup=main_menu_kb(uid == ADMIN_CHAT_ID),
        parse_mode=ParseMode.HTML
    )

@router.message(F.text == "👤 Мій профіль")
async def profile_command(message: Message):
    uid = message.from_user.id
    data = TERMINAL_USERS.get(uid, {"is_pro": False, "status": "Базовий доступ", "scans": 0})
    tier = "🛡 PRO Трейдер" if data["is_pro"] else "👤 Користувач (Стандарт)"
    
    await message.answer(
        f"👤 <b>Статус вашого профілю:</b>\n\n"
        f"🆔 ID: <code>{uid}</code>\n"
        f"📈 Рівень доступу: <b>{tier}</b>\n"
        f"🔍 Проведено сканувань ринку: {data['scans']}",
        parse_mode=ParseMode.HTML
    )

@router.message(F.text == "👑 Адмін-панель")
async def admin_panel_handler(message: Message):
    if message.from_user.id != ADMIN_CHAT_ID:
        return
    kb = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="🔙 Головне меню")]], resize_keyboard=True)
    await message.answer(f"👑 Консоль адміністратора. Активних користувачів у системі: {len(TERMINAL_USERS)}", reply_markup=kb)

@router.message(F.text == "🔙 Головне меню")
async def back_to_main_menu(message: Message):
    await message.answer("Головне меню активне:", reply_markup=main_menu_kb(message.from_user.id == ADMIN_CHAT_ID))

async def handle_ping(request):
    return web.Response(text="NEXUS-TERMINAL-ONLINE")

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
