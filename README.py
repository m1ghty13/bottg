import asyncio
from aiocryptopay import AioCryptoPay, Networks
import aiosqlite
from aiogram import Bot, Dispatcher, types, Router
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.exceptions import TelegramBadRequest
from aiogram import F
from aiogram.types import Update
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext


# ---------- Состояния FSM ----------
class TopUpState(StatesGroup):
    waiting_for_crypto_amount = State()
    waiting_for_card_amount = State()


banks = {
    "🇷🇺 Сбербанк": {"price": 40, "stock": 2},
    "🇷🇺 Тинькофф": {"price": 40, "stock": 3},
    "🇷🇺 ВТБ": {"price": 35, "stock": 1},
    "🇷🇺 Альфа-Банк": {"price": 35, "stock": 1},
    "🇷🇺 Газпромбанк": {"price": 35, "stock": 1},
    "🇷🇺 МТС Банк": {"price": 30, "stock": 2},
    "🇷🇺 Почта Банк": {"price": 30, "stock": 1},
    "🇷🇺 Озон Банк": {"price": 30, "stock": 2},
    "🇺🇦 Monobank": {"price": 40, "stock": 2},
    "🇰🇿 Kaspi Bank": {"price": 40, "stock": 1}
}

avito_accounts = {
    "Avito 2016": {
        "price": 25,
        "stock": 1,
        "link": "https://t.me/avitoaccsshop/11"
    },
    "Avito 2023 #1": {
        "price": 15,
        "stock": 1,
        "link": "https://t.me/avitoaccsshop/8"
    },
    "Avito 2023 #2": {
        "price": 15,
        "stock": 1,
        "link": "https://t.me/avitoaccsshop/7"
    }
}



BOT_TOKEN = "8599155215:AAE7umCggsC0chyE5-FjAmeHPzcfi2NqSws"
CRYPTOBOT_TOKEN = "485714:AAOdLcHdbEjKgkJsPY9AJwzuxUdntgCnJXA"
crypto = AioCryptoPay(token=CRYPTOBOT_TOKEN, network=Networks.MAIN_NET)


user_balances = {}
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
router = Router()
dp.include_router(router)

RUB_TO_USD_RATE = 79  # 1$ = 79₽


DB_PATH = "users.db"

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                balance REAL DEFAULT 0
            )
        """)
        await db.commit()

async def get_balance(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            if row:
                return row[0]
            else:
                await db.execute("INSERT INTO users (user_id, balance) VALUES (?, 0)", (user_id,))
                await db.commit()
                return 0

async def update_balance(user_id: int, amount: float):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (amount, user_id))
        await db.commit()

async def show_start(message_or_callback, edit: bool = False):
    start_text = (
        f"👋 Привет, {message_or_callback.from_user.first_name}!\n\n"
        "Это магазин готовых верифицированных аккаунтов крипто-бирж и ЛК банков, добро пожаловать!\n\n"
        "Канал: https://t.me/avitoaccsshop\n"
        "Перед покупкой рекомендуем ознакомиться с FAQ."
    )

    if edit:
        try:
            await message_or_callback.message.edit_text(
                start_text,
                reply_markup=main_menu()
            )
        except TelegramBadRequest:
            # если нельзя отредактировать — отправляем новое
            await message_or_callback.message.answer(
                start_text,
                reply_markup=main_menu()
            )
    else:
        await message_or_callback.answer(
            start_text,
            reply_markup=main_menu()
        )


# ---------- Главное меню ----------
def main_menu():
    kb = InlineKeyboardBuilder()
    kb.button(text="📦 Каталог", callback_data="catalog")
    kb.button(text="ℹ️ Инфо", callback_data="info")
    kb.button(text="👤 Кабинет", callback_data="cabinet")
    kb.adjust(1, 2)
    return kb.as_markup()

# ---------- /start ----------
@router.message(Command("start"))
async def cmd_start(message: types.Message):
    await show_start(message, edit=False)






# ---------- Каталог ----------
def catalog_menu():
    kb = InlineKeyboardBuilder()
    kb.button(text="💰 Крипто-биржи", callback_data="crypto_exchanges")
    kb.button(text="🏦 ЛК банков", callback_data="bank_accounts")
    kb.button(text="❤ Авито", callback_data="neo_banks")
    kb.button(text="⬅️ Назад", callback_data="main_menu")
    kb.adjust(1)  # каждая кнопка на своем ряду
    return kb.as_markup()

def catalog_submenu():
    kb = InlineKeyboardBuilder()
    kb.button(text="⬅️ Назад", callback_data="catalog")
    kb.button(text="🏠 В меню", callback_data="main_menu")
    kb.adjust(2)  # две кнопки в одном ряду
    return kb.as_markup()


@router.callback_query(lambda c: c.data == "catalog")
async def catalog_handler(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "📦 Каталог товаров:\n\nВыберите категорию:",
        reply_markup=catalog_menu()
    )
    await callback.answer()




# ---------- Меню информации ----------
def info_menu():
    kb = InlineKeyboardBuilder()
    kb.button(text="💬 Поддержка", callback_data="support")
    kb.button(text="📄 FAQ", callback_data="faq")
    kb.button(text="ℹ️ О нас", callback_data="about")
    kb.button(text="🏠 В главное меню", callback_data="main_menu")  # ← Назад теперь ведет в главное меню
    kb.adjust(1)
    return kb.as_markup()

# ---------- Подменю информации ----------
def info_submenu():
    kb = InlineKeyboardBuilder()
    kb.button(text="⬅️ Назад", callback_data="back_to_info")
    kb.button(text="🏠 В главное меню", callback_data="main_menu")
    kb.adjust(2)
    return kb.as_markup()


# ---------- Меню личного кабинета ----------
def cabinet_menu():
    kb = InlineKeyboardBuilder()
    kb.button(text="📦 Заказы", callback_data="orders")
    kb.button(text="💳 Пополнить баланс", callback_data="topup")
    kb.button(text="⬅️ Назад", callback_data="main_menu")
    kb.adjust(1)
    return kb.as_markup()



# ---------- Инфо ----------
@router.callback_query(lambda c: c.data == "info")
async def info_handler(callback: types.CallbackQuery):
    await callback.message.edit_text("ℹ️ Информация:", reply_markup=info_menu())
    await callback.answer()

# ---------- Поддержка ----------
@router.callback_query(lambda c: c.data == "support")
async def support_handler(callback: types.CallbackQuery):
    support_text = (
        "🆘 *Поддержка*\n\n"
        "При возникновении вопросов или проблем — пишите администратору: @x2ndgf\n\n"
        "⚠️ *Но перед этим убедитесь, что вашего вопроса нет в FAQ ⬇️*"
    )

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📄 FAQ", callback_data="faq")],
        [
            InlineKeyboardButton(text="⬅️ Назад", callback_data="info_back"),
            InlineKeyboardButton(text="🏠 В главное меню", callback_data="main_menu")
        ]
    ])

    await callback.message.edit_text(
        support_text,
        parse_mode="Markdown",
        reply_markup=keyboard,
    )
    await callback.answer()


# ---------- FAQ ----------
@router.callback_query(lambda c: c.data == "faq")
async def faq_handler(callback: types.CallbackQuery):
    faq_text = (
        "📄 *Часто задаваемые вопросы (FAQ)*\n\n"
        "1. *Не прошла оплата?* — Предоставьте хэш транзакции.\n\n"
        "2. *Не нашли нужную биржу или банк?* — Напишите в поддержку, и мы постараемся выполнить ваш заказ.\n\n"
        "3. *Могу ли я сделать возврат?* — Да, если аккаунт оказался нерабочим.\n\n"
        "4. *Могу ли я получить скидку?* — Да, при заказе от 10 штук.\n\n"
        "5. *Почему нет определённых гео?* — Если не нашли нужную страну, обратитесь в поддержку.\n\n"
        "6. *Есть гарантии на аккаунты?* — Да, 30 дней с момента покупки.\n\n"
        "7. *Что входит в комплект?* — В зависимости от позиции: почта, виртуальный номер, авторизованный аккаунт в эмуляторе, документы дропа, селфи с документом и отдельно селфи.\n\n"
        "8. *Что делать, если не работают прокси?* — Попробуйте использовать VPN или сменить DNS.\n\n"
        "9. *Прокси выдаются только в одни руки?* — Да, по информации от поставщиков.\n\n"
        "10. *Можно ли продлить прокси и номер телефона?* — Да, в личном кабинете.\n\n"
        "️️️11. *Как получить доступ к номеру после покупки?* — В разделе 'Заказы' можно получать коды и менять номер. Срок аренды — 10 дней (входит в стоимость), далее 0.5$ в день.\n\n"
        "12. *Как войти в аккаунт через эмулятор DuoPlus?* — После покупки вы получите данные для входа. Пример: https://t.me/DuoPlus/4.\n\n"
        "13. *Как получить пластиковую карту от ЛК банка?* — После покупки напишите саппорту с номером заказа и адресом доставки. Карта отправляется в течение 24 часов, с трек-номером.\n\n"
        "14. *Какой возраст дропов?* — Все дропы 18+, средний возраст — 30+.\n\n"
        "15. *Что делать, если банк заблокировал счёт или запросил видео/фото проверку?* — Напишите саппорту, укажите номер заказа. Мы поможем восстановить доступ. "
        "Стоимость услуги — 20% от застрявшей суммы, но не менее 20$."
    )

    await callback.message.edit_text(
        faq_text,
        parse_mode="Markdown",
        reply_markup=info_submenu(),
    )
    await callback.answer()


# ---------- О нас ----------
@router.callback_query(lambda c: c.data == "about")
async def about_handler(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "ℹ️ О нас:\nЭто магазин готовых верифицированных аккаунтов крипто-бирж и ЛК банков.",
        reply_markup=info_submenu(),
    )
    await callback.answer()


# ---------- Возврат назад в Инфо ----------
@router.callback_query(lambda c: c.data == "back_to_info")
async def back_to_info_handler(callback: types.CallbackQuery):
    try:
        await callback.message.edit_text("ℹ️ Информация:", reply_markup=info_menu())
    except TelegramBadRequest as e:
        if "message is not modified" in str(e):
            pass
        else:
            raise
    await callback.answer()


# ---------- Категория: Крипто-биржи ----------
@router.callback_query(lambda c: c.data == "crypto_exchanges")
async def crypto_exchanges_handler(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "💰 Крипто-биржи:\n\nСкоро тут будут товары!",
        reply_markup=catalog_submenu()
    )
    await callback.answer()

# ---------- Категория: ЛК банков ----------
@router.callback_query(lambda c: c.data == "bank_accounts")
async def bank_accounts_handler(callback: types.CallbackQuery):
    text = "🏦 Выберите банк для покупки личного кабинета:\n\n"

    # создаём кнопки по 2 в ряд
    bank_buttons = []
    temp_row = []
    for i, name in enumerate(banks.keys(), 1):
        cb = f"bank_info_{i}"
        temp_row.append(InlineKeyboardButton(text=name, callback_data=cb))
        if i % 2 == 0 or i == len(banks):
            bank_buttons.append(temp_row)
            temp_row = []

    bank_buttons.append([
        InlineKeyboardButton(text="⬅️ Назад", callback_data="catalog"),
        InlineKeyboardButton(text="🏠 В меню", callback_data="main_menu")
    ])

    keyboard = InlineKeyboardMarkup(inline_keyboard=bank_buttons)

    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()


@router.callback_query(lambda c: c.data.startswith("bank_info_"))
async def bank_info_handler(callback: types.CallbackQuery):
    index = int(callback.data.split("_")[2]) - 1
    bank_name = list(banks.keys())[index]
    bank_data = banks[bank_name]
    price_usd = bank_data["price"]
    price_rub = price_usd * RUB_TO_USD_RATE

    text = (
    f"{bank_name}\n\n"
    f"💰 Цена: *{price_usd}$* (~*{price_rub:.0f}₽*)\n"
    f"📦 В наличии: *{bank_data['stock']} шт.*\n\n"
    "Вы можете приобрести этот аккаунт прямо сейчас 👇"
    )

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🛒 Купить", callback_data=f"buy_bank_{index}")],
        [
            InlineKeyboardButton(text="⬅️ Назад", callback_data="bank_accounts"),
            InlineKeyboardButton(text="🏠 В меню", callback_data="main_menu")
        ]
    ])

    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=keyboard)
    await callback.answer()






@router.callback_query(lambda c: c.data.startswith("bank_"))
async def bank_selected_handler(callback: types.CallbackQuery):
    bank_name = callback.data.replace("bank_", "").capitalize()
    await callback.message.edit_text(
        f"🏦 Вы выбрали банк: *{bank_name}*\n\n"
        f"Скоро тут появятся товары и цены!",
        parse_mode="Markdown",
        reply_markup=catalog_submenu()
    )
    await callback.answer()


# ---------- Категория: Нео банки ----------
@router.callback_query(lambda c: c.data == "neo_banks")
async def neo_banks_handler(callback: types.CallbackQuery):
    text = "❤ Аккаунты Avito:\n\nВыберите нужный аккаунт:"

    buttons = []
    temp = []

    for i, name in enumerate(avito_accounts.keys(), 1):
        temp.append(
            InlineKeyboardButton(
                text=name,
                callback_data=f"avito_info_{i}"
            )
        )
        if i % 2 == 0 or i == len(avito_accounts):
            buttons.append(temp)
            temp = []

    buttons.append([
        InlineKeyboardButton(text="⬅️ Назад", callback_data="catalog"),
        InlineKeyboardButton(text="🏠 В меню", callback_data="main_menu")
    ])

    await callback.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
    )
    await callback.answer()


@router.callback_query(lambda c: c.data.startswith("avito_info_"))
async def avito_info_handler(callback: types.CallbackQuery):
    index = int(callback.data.split("_")[2]) - 1
    name = list(avito_accounts.keys())[index]
    data = avito_accounts[name]

    price_usd = data["price"]
    price_rub = price_usd * RUB_TO_USD_RATE

    text = (
        f"❤ *{name}*\n\n"
        f"💰 Цена: *{price_usd}$* (~*{price_rub:.0f}₽*)\n"
        f"📦 В наличии: *{data['stock']} шт.*\n\n"
        "📄 *Описание и условия:*\n"
        f"{data['link']}\n\n"
        "Вы можете приобрести этот аккаунт прямо сейчас 👇"
    )

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🛒 Купить", callback_data=f"buy_avito_{index}")],
        [
            InlineKeyboardButton(text="⬅️ Назад", callback_data="neo_banks"),
            InlineKeyboardButton(text="🏠 В меню", callback_data="main_menu")
        ]
    ])

    await callback.message.edit_text(
        text,
        parse_mode="Markdown",
        reply_markup=keyboard,
        disable_web_page_preview=False
    )
    await callback.answer()





@router.callback_query(lambda c: c.data.startswith("buy_avito_"))
async def buy_avito_handler(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    index = int(callback.data.split("_")[2])

    name = list(avito_accounts.keys())[index]
    data = avito_accounts[name]
    price = data["price"]

    balance = await get_balance(user_id)

    if data["stock"] <= 0:
        await callback.message.edit_text("❌ Аккаунт уже продан.")
        await callback.answer()
        return

    if balance < price:
        await callback.message.edit_text(
            (
                f"⚠️ *Недостаточно средств!*\n\n"
                f"💰 Баланс: *{balance}$*\n"
                f"💵 Цена: *{price}$*"
            ),
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="💳 Пополнить баланс", callback_data="topup")],
                [InlineKeyboardButton(text="⬅️ Назад", callback_data=f"avito_info_{index+1}")]
            ])
        )
        await callback.answer()
        return

    # списываем и уменьшаем наличие
    await update_balance(user_id, -float(price))
    avito_accounts[name]["stock"] -= 1

    new_balance = await get_balance(user_id)

    await callback.message.edit_text(
        (
            f"✅ *Покупка успешна!*\n\n"
            f"❤ Аккаунт: *{name}*\n"
            f"💵 Цена: *{price}$*\n"
            f"💰 Баланс: *{new_balance}$*\n\n"
            "Данные аккаунта будут выданы в ближайшее время."
        ),
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🏠 В меню", callback_data="main_menu")]
        ])
    )
    await callback.answer()






# ---------- Главное меню ----------
@router.callback_query(lambda c: c.data == "main_menu")
async def main_menu_handler(callback: types.CallbackQuery):
    await show_start(callback, edit=True)
    await callback.answer()



# ---------- Подменю кабинета ----------
def cabinet_submenu():
    kb = InlineKeyboardBuilder()
    kb.button(text="⬅️ Назад", callback_data="cabinet")
    kb.button(text="🏠 В меню", callback_data="main_menu")
    kb.adjust(2)
    return kb.as_markup()

@router.callback_query(lambda c: c.data.startswith("buy_bank_"))
async def buy_bank_handler(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    # buy callback uses zero-based index in your previous flow
    index = int(callback.data.split("_")[2])
    bank_name = list(banks.keys())[index]
    bank_data = banks[bank_name]

    # Получаем баланс из вашей БД (примерно так у тебя реализован get_balance)
    # Если у тебя баланс в sqlite, вызови асинхронную функцию get_balance(user_id).
    # Здесь использую ту функцию, что у тебя в коде:
    balance = await get_balance(user_id)  # ← если ты используешь get_balance как выше

    price = bank_data["price"]

    # Проверка наличия товара
    if bank_data["stock"] <= 0:
        await callback.message.edit_text("❌ Товар закончился, попробуйте выбрать другой банк.")
        await callback.answer()
        return

    # Проверка баланса
    if balance < price:
        # кнопка пополнить должна ссылаться на существующий callback_data "topup"
        # и кнопка назад должна вернуть на карточку товара: bank_info_{index+1}
        await callback.message.edit_text(
            (
                f"⚠️ *Недостаточно средств на балансе!*\n\n"
                f"💰 Ваш баланс: *{balance}$*\n"
                f"💵 Стоимость: *{price}$*\n\n"
                "Пополните баланс в личном кабинете, чтобы совершить покупку."
            ),
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="💳 Пополнить баланс", callback_data="topup")],
                [InlineKeyboardButton(text="⬅️ Назад", callback_data=f"bank_info_{index+1}")]
            ])
        )
        await callback.answer()
        return

    # Если хватает — списываем (через update_balance) и уменьшаем количество
    # Используем твою функцию update_balance (которая прибавляет значение),
    # поэтому для списания передаём отрицательное значение.
    await update_balance(user_id, -float(price))
    banks[bank_name]["stock"] -= 1

    # Обновим баланс для вывода
    new_balance = await get_balance(user_id)

    await callback.message.edit_text(
        (
            f"✅ Покупка успешно завершена!\n\n"
            f"🏦 Вы приобрели: *{bank_name}*\n"
            f"💵 Цена: *{price}$*\n"
            f"💰 Новый баланс: *{new_balance}$*\n\n"
            "Данные аккаунта будут выданы в ближайшее время."
        ),
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🏠 В меню", callback_data="main_menu")]
        ])
    )
    await callback.answer()


# ---------- Заказы ----------
@router.callback_query(lambda c: c.data == "orders")
async def orders_handler(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "📦 Заказы:\n\nСкоро тут появится история ваших покупок.",
        reply_markup=cabinet_submenu()
    )
    await callback.answer()

# ---------- Пополнить баланс ----------
@router.callback_query(lambda c: c.data == "topup")
async def topup_handler(callback: types.CallbackQuery):
    kb = InlineKeyboardBuilder()
    kb.button(text="💸 Пополнить через CryptoBot", callback_data="topup_crypto")
    kb.button(text="🏦 Пополнить через карту РФ", callback_data="topup_card")
    kb.button(text="⬅️ Назад", callback_data="cabinet")
    kb.adjust(1)
    await callback.message.edit_text(
        "💳 Пополнить баланс:\n\nВыберите способ оплаты:",
        reply_markup=kb.as_markup()
    )
    await callback.answer()

@router.callback_query(lambda c: c.data == "topup_card")
async def topup_card_handler(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "💰 Введите сумму пополнения через карту РФ:\n\n"
        f"💱 Курс: *1$ = {RUB_TO_USD_RATE}₽*\n"
        f"💵 Минимум: *{RUB_TO_USD_RATE}₽ (1$)*\n\n"
        "Например: `1500` — чтобы пополнить на 1500₽.",
        parse_mode="Markdown"
    )
    await state.set_state(TopUpState.waiting_for_card_amount)
    await callback.answer()



@router.callback_query(lambda c: c.data == "topup_crypto")
async def topup_crypto_handler(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "💵 Введите сумму пополнения (от 1 USDT):\n\n"
        "Например: `10` — чтобы пополнить на 10 USDT.",
        parse_mode="Markdown"
    )
    await state.set_state(TopUpState.waiting_for_crypto_amount)
    await callback.answer()

@router.message(TopUpState.waiting_for_crypto_amount)
async def process_topup_amount(message: types.Message, state: FSMContext):
    try:
        amount = float(message.text.replace(",", "."))
    except ValueError:
        await message.answer("❌ Введите корректное число, например: 5.5")
        return

    if amount < 1:
        await message.answer("⚠️ Минимальная сумма пополнения — 1 USDT.")
        return

    user_id = message.from_user.id

    try:
        invoice = await crypto.create_invoice(
            asset="USDT",
            amount=amount,
            description=f"Пополнение баланса пользователя {user_id}",
        )
    except Exception as e:
        await message.answer(f"⚠️ Ошибка при создании платежа: {e}")
        return

    pay_url = invoice.bot_invoice_url
    kb = InlineKeyboardBuilder()
    kb.button(text="💰 Оплатить через CryptoBot", url=pay_url)
    kb.button(text="✅ Проверить оплату", callback_data=f"check_payment:{invoice.invoice_id}")
    kb.button(text="⬅️ Назад", callback_data="topup")
    kb.adjust(1)

    await message.answer(
        f"💳 Пополнение через CryptoBot:\n\n"
        f"Сумма: {amount:.2f} USDT\n\n"
        f"После оплаты нажмите «Проверить оплату».",
        reply_markup=kb.as_markup()
    )

    await state.clear()

@router.message(TopUpState.waiting_for_card_amount)
async def process_card_topup(message: types.Message, state: FSMContext):
    try:
        rub_amount = float(message.text.replace(",", "."))
    except ValueError:
        await message.answer("❌ Введите корректное число, например: 1000")
        return

    if rub_amount < RUB_TO_USD_RATE:
        await message.answer("⚠️ Минимальная сумма — 79₽ (1$).")
        return

    usd_amount = rub_amount / RUB_TO_USD_RATE

    text = (
        f"💳 Пополнение через карту РФ\n\n"
        f"💰 Сумма: {rub_amount:.2f}₽\n"
        f"💵 Будет зачислено: {usd_amount:.2f}$\n\n"
        f"Для получения реквизитов напишите менеджеру @x2ndgf\n\n"
        f"⚠️ Курс фиксированный: 1$ = {RUB_TO_USD_RATE}₽"
    )

    kb = InlineKeyboardBuilder()
    kb.button(text="⬅️ Назад", callback_data="topup")
    kb.button(text="🏠 В меню", callback_data="main_menu")
    kb.adjust(2)

    await message.answer(text, reply_markup=kb.as_markup())
    await state.clear()



@router.callback_query(lambda c: c.data.startswith("check_payment:"))
async def check_payment_handler(callback: types.CallbackQuery):
    invoice_id = int(callback.data.split(":")[1])
    user_id = callback.from_user.id

    invoices = await crypto.get_invoices(invoice_ids=[invoice_id])

    if not invoices:
        await callback.answer("❌ Счёт не найден", show_alert=True)
        return

    invoice = invoices[0]

    if invoice.status == "paid":
        await update_balance(user_id, float(invoice.amount))
        await callback.message.edit_text(
            f"✅ Оплата прошла успешно!\n\n"
            f"На ваш баланс зачислено {invoice.amount} USDT.",
            reply_markup=cabinet_submenu(),
        )
    else:
        await callback.answer(
            f"⏳ Статус платежа: {invoice.status}",
            show_alert=True
        )






# ---------- Кабинет ----------
@router.callback_query(lambda c: c.data == "cabinet")
async def cabinet_handler(callback: types.CallbackQuery):
    user_balance = await get_balance(callback.from_user.id)
    text = f"Личный кабинет 🏠\n\n💰 Текущий баланс: {user_balance:.2f}$"

    # Если предыдущее сообщение было медиа, edit_text не сработает
    try:
        await callback.message.edit_text(text, reply_markup=cabinet_menu())
    except TelegramBadRequest as e:
        if "message is not modified" in str(e):
            pass
        elif "there is no text in the message to edit" in str(e):
            await callback.message.answer(text, reply_markup=cabinet_menu())
        else:
            raise

    await callback.answer()





# ---------- Глобальный обработчик ошибок ----------
@dp.error()
async def global_error_handler(error: Exception):
    print(f"⚠️ Ошибка при обработке апдейта: {error}")
    return True



# ---------- Запуск ----------
async def main():
    print("Бот запущен 🚀")
    try:
        await init_db()
        await dp.start_polling(bot)
    except Exception as e:
        print(f"⚠️ Ошибка при запуске бота: {e}")
    finally:
        await bot.session.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("❌ Бот остановлен вручную.")
