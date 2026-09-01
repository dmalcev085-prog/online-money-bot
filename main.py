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
    format="%(asctime)s | 🚀 CRYPTO-SIGNALS | %(levelname)s | %(message)s",
    stream=sys.stdout
)

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()
router = Router()

class CryptoStates(StatesGroup):
    broadcast_message = State()

# Сховище користувачів та підписок у пам'яті
CRYPTO_USERS = {}

# Пакети крипто-сигналів за зірки (Telegram Stars)
CRYPTO_PACKAGES = {
    "📈 VIP Сигнали на день (75 Stars)": {
        "price": 75,
        "title": "Доступ до VIP-сигналів на 24 години",
        "desc": "Точні точки входу (Long/Short), плечі та цілі фіксації прибутку по топ-монетах.",
        "content": "🚀 <b>Ваш актуальний VIP-сигнал на сьогодні:</b>\n\n🪙 <b>Монета:</b> BTC/USDT (LONG)\n📍 <b>Точка входу:</b> $64,200 - $64,500\n🎯 <b>Цілі (Take-Profit):</b> 1) $65,500 | 2) $67,000 | 3) $69,500\n🛑 <b>Стоп-лосс:</b> $63,100\n⚡ <b>Рекомендоване плече:</b> x10"
    },
    "💎 Преміум Клуб на місяць (300 Stars)": {
        "price": 300,
        "title": "Місячна підписка на закритий крипто-канал",
        "desc": "Цілодобова аналітика, сповіщення про рухи китів та щоденні сигнали з прохідністю 85%.",
        "content": "💎 <b>Вітаємо у Преміум Клубі!</b>\n\nПосилання на закритий Telegram-канал із сигналами у реальному часі: https://t.me/+crypto_signals_vip_channel_link\nНе забудьте закріпити канал, щоб не пропускати термінові угоди!"
    }
}

def main_menu_kb(is_admin: bool = False):
    kb = [
        [KeyboardButton(text="📊 Безплатний огляд ринку"), KeyboardButton(text="🚀 VIP Сигнали (Stars)")],
        [KeyboardButton(text="👤 Мій профіль"), KeyboardButton(text="👥 Запросити трейдерів")]
    ]
    if is_admin:
        kb.append([KeyboardButton(text="👑 Адмін-панель"), KeyboardButton(text="📢 Розсилка сигналу")])
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

@router.message(CommandStart())
async def start_command(message: Message, state: FSMContext):
    await state.clear()
    uid = message.from_user.id
    
    if uid not in CRYPTO_USERS:
        CRYPTO_USERS[uid] = {
            "is_vip": False,
            "vip_package": "Немає підписки",
            "signals_viewed": 0
        }
        
    is_admin = (uid == ADMIN_CHAT_ID)
    
    welcome_text = (
        "🚀 <b>Ласкаво просимо в Crypto Signals UA!</b>\n\n"
        "📉 Професійна аналітика крипторинку, точні точки входу та інсайдерські стратегії для прибуткового трейдингу.\n\n"
        "• Отримуйте безплатні огляди\n"
        "• Купуйте VIP-сигнали за зірки Telegram ⭐\n"
        "• Заробляйте на падінні та рості ринку разом із нами!\n\n"
        "Оберіть потрібний розділ у меню нижче:"
    )
    await message.answer(welcome_text, reply_markup=main_menu_kb(is_admin))

@router.message(F.text == "📊 Безплатний огляд ринку")
async def free_market_overview(message: Message):
    uid = message.from_user.id
    if uid in CRYPTO_USERS:
        CRYPTO_USERS[uid]["signals_viewed"] += 1
        
    overview_text = (
        "📊 <b>Аналіз ринку на сьогодні:</b>\n\n"
        "BTC демонструє стабільність у районі ключових рівнів підтримки. На ринку спостерігається висока волатильність через макроекономічні новини.\n\n"
        "💡 <i>Порада:</i> Не торгуйте без стоп-лосів і дотримуйтесь ризик-менеджменту.\n\n"
        "⭐ Хочете отримувати готові точки входу з високою точністю? Відкрийте розділ <b>«🚀 VIP Сигнали (Stars)»</b>!"
    )
    await message.answer(overview_text, parse_mode=ParseMode.HTML)

@router.message(F.text == "🚀 VIP Сигнали (Stars)")
async def vip_store_menu(message: Message):
    kb = [[KeyboardButton(text=pkg)] for pkg in CRYPTO_PACKAGES.keys()]
    kb.append([KeyboardButton(text="🔙 Головне меню")])
    markup = ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
    
    await message.answer(
        "🚀 <b>Ексклюзивний маркетплейс сигналів:</b>\n\n"
        "Обирайте пакет, оплачуйте офіційними зірками Telegram Stars в один клік і отримуйте миттєвий доступ до прибуткових угод!",
        reply_markup=markup,
        parse_mode=ParseMode.HTML
    )

@router.message(F.text.in_(CRYPTO_PACKAGES.keys()))
async def send_crypto_invoice(message: Message):
    pkg_name = message.text
    product = CRYPTO_PACKAGES[pkg_name]
    
    desc_text = (
        f"🎯 <b>{pkg_name}</b>\n\n"
        f"📌 <i>Опис:</i> {product['desc']}\n\n"
        f"Інвестуйте в якісну аналітику та заробляйте на криптовалюті!"
    )
    await message.answer(desc_text, parse_mode=ParseMode.HTML)
    
    prices = [LabeledPrice(label=product['title'], amount=product['price'])]
    
    await message.bot.send_invoice(
        chat_id=message.chat.id,
        title=product['title'],
        description=product['desc'],
        payload=f"crypto_pay_{pkg_name}_{message.from_user.id}",
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
    
    if uid not in CRYPTO_USERS:
        CRYPTO_USERS[uid] = {"is_vip": False, "vip_package": "Немає підписки", "signals_viewed": 0}
        
    bought_pkg = None
    for name, prod in CRYPTO_PACKAGES.items():
        if prod["price"] == amount:
            bought_pkg = prod
            CRYPTO_USERS[uid]["is_vip"] = True
            CRYPTO_USERS[uid]["vip_package"] = name
            break
            
    content = bought_pkg["content"] if bought_pkg else "🎉 Оплату успішно зараховано! Доступ активовано."
    
    await message.answer(
        f"🎉 <b>ОПЛАТУ ЧЕРЕЗ TELEGRAM STARS УСПІШНО ПРОЙДЕНО!</b>\n\n"
        f"Сплачено: {amount} ⭐.\n\n"
        f"{content}",
        reply_markup=main_menu_kb(uid == ADMIN_CHAT_ID),
        parse_mode=ParseMode.HTML
    )
    
    if ADMIN_CHAT_ID:
        try:
            await bot.send_message(
                ADMIN_CHAT_ID,
                f"💎 <b>ХТОСЬ КУПИВ КРИПТО-СИГНАЛИ!</b>\n\n"
                f"👤 ID: <code>{uid}</code>\n"
                f"⭐ Сума: {amount} XTR",
                parse_mode=ParseMode.HTML
            )
        except Exception:
            pass

@router.message(F.text == "👤 Мій профіль")
async def profile_command(message: Message):
    uid = message.from_user.id
    data = CRYPTO_USERS.get(uid, {"is_vip": False, "vip_package": "Немає", "signals_viewed": 0})
    
    status = "💎 VIP Трейдер" if data["is_vip"] else "👤 Безплатний аккаунт"
    
    profile_text = (
        f"👤 <b>Ваш профіль трейдера:</b>\n\n"
        f"🆔 ID: <code>{uid}</code>\n"
        f"📈 Статус: <b>{status}</b>\n"
        f"⭐ Активний пакет: <i>{data['vip_package']}</i>\n"
        f"👀 Переглянуто оглядів: {data['signals_viewed']}"
    )
    await message.answer(profile_text, parse_mode=ParseMode.HTML)

@router.message(F.text == "👥 Запросити трейдерів")
async def referral_command(message: Message):
    me = await message.bot.get_me()
    ref_link = f"https://t.me/{me.username}?start=ref_{message.from_user.id}"
    
    text = (
        "👥 <b>Партнерська програма:</b>\n\n"
        "Запрошуйте друзів-трейдерів за своїм посиланням і отримуйте безплатні бонуси до сигналів!\n\n"
        f"🔗 <b>Ваше посилання:</b>\n<code>{ref_link}</code>"
    )
    await message.answer(text, parse_mode=ParseMode.HTML)

@router.message(F.text == "👑 Адмін-панель")
async def admin_panel_handler(message: Message):
    if message.from_user.id != ADMIN_CHAT_ID:
        return
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📊 Статистика крипто-бота"), KeyboardButton(text="🔙 Головне меню")]
        ],
        resize_keyboard=True
    )
    await message.answer("👑 Адмін-панель крипто-бота:", reply_markup=kb)

@router.message(F.text == "📊 Статистика крипто-бота")
async def admin_statistics(message: Message):
    if message.from_user.id != ADMIN_CHAT_ID:
        return
    total_users = len(CRYPTO_USERS)
    vip_users = sum(1 for d in CRYPTO_USERS.values() if d["is_vip"])
    await message.answer(f"📊 Всього трейдерів у базі: {total_users}\n💎 VIP-підписників: {vip_users}")

@router.message(F.text == "📢 Розсилка сигналу")
async def broadcast_start_handler(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_CHAT_ID:
        return
    await message.answer("Введіть текст нового крипто-сигналу для розсилки всім користувачам:", reply_markup=ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="❌ Скасувати")]], resize_keyboard=True))
    await state.set_state(CryptoStates.broadcast_message)

@router.message(CryptoStates.broadcast_message)
async def broadcast_execute_handler(message: Message, state: FSMContext):
    if message.text == "❌ Скасувати":
        await state.clear()
        return await message.answer("Скасовано.", reply_markup=main_menu_kb(True))
    text = message.text
    await state.clear()
    sent = 0
    for uid in CRYPTO_USERS.keys():
        try:
            await bot.send_message(uid, f"🚨 <b>ТЕРМІНОВИЙ КРИПТО-СИГНАЛ:</b>\n\n{text}", parse_mode=ParseMode.HTML)
            sent += 1
        except Exception:
            pass
    await message.answer(f"✅ Сигнал успішно розіслано! Доставлено: {sent}", reply_markup=main_menu_kb(True))

@router.message(F.text == "🔙 Головне меню")
async def back_to_main_menu(message: Message):
    await message.answer("Головне меню:", reply_markup=main_menu_kb(message.from_user.id == ADMIN_CHAT_ID))

async def handle_ping(request):
    return web.Response(text="CRYPTO-BOT-ACTIVE")

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
