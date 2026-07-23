import os
import re
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))
HOSTING_API_TOKEN = os.getenv("HOSTING_API_TOKEN")
SERVER_ID = os.getenv("SERVER_ID")

waiting_for_nick = set()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🎮 Подать заявку на вход", callback_data="start_application")]
    ]

    await update.message.reply_text(
        "🎮 Добро пожаловать на сервер Menny!\n\nДля получения доступа к серверу нажмите кнопку ниже.",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "start_application":
        waiting_for_nick.add(query.from_user.id)

        await query.message.reply_text(
            "✍️ Введите ваш Minecraft-ник.\n\nТребования:\n• от 3 до 16 символов\n• только английские буквы, цифры и _"
        )
        return

    action, nickname, applicant_id = query.data.split(":")
    applicant_id = int(applicant_id)

    if query.from_user.id != ADMIN_ID:
        await query.edit_message_text("❌ У вас нет прав для этого действия.")
        return

    if action == "approve":
        try:
            add_to_whitelist(nickname)

            await context.bot.send_message(
                chat_id=applicant_id,
                text=(
                    f"✅ Ваша заявка одобрена!\n"
                    f"Вы добавлены в whitelist под ником: {nickname}\n\n"
                    f"Теперь можете зайти на сервер:\n"
                    f"menny.skuf.club\n"
                    f"Резервный IP: d41.joinserver.xyz:25696 (Порт для ПК)\n"
                    f"Порт для телефона: 25715\n"
                    f"Telegram с чатом: https://t.me/+_1Xw0btf8zNhYTIy \n"
                )
            )

            await query.edit_message_text(
                f"✅ Заявка одобрена\n"
                f"Ник: {nickname}\n"
                f"Игрок автоматически добавлен в whitelist."
            )

        except Exception as e:
            await query.edit_message_text(
                f"❌ Ошибка при добавлении в whitelist:\n{e}"
            )

    else:
        await context.bot.send_message(
            chat_id=applicant_id,
            text=f"❌ Ваша заявка на ник {nickname} была отклонена."
        )

        await query.edit_message_text(
            f"❌ Заявка отклонена\nНик: {nickname}"
        )


async def handle_nickname(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if user_id not in waiting_for_nick:
        return

    nickname = update.message.text.strip()

    if not re.fullmatch(r"[A-Za-z0-9_]{3,16}", nickname):
        await update.message.reply_text(
            "❌ Неверный ник!\n\nНик должен содержать:\n• 3–16 символов\n• английские буквы\n• цифры\n• символ _"
        )
        return

    waiting_for_nick.remove(user_id)

    applicant = update.effective_user

    keyboard = [
        [
            InlineKeyboardButton(
                "✅ Одобрить",
                callback_data=f"approve:{nickname}:{applicant.id}"
            ),
            InlineKeyboardButton(
                "❌ Отклонить",
                callback_data=f"reject:{nickname}:{applicant.id}"
            ),
        ]
    ]

    text = (
        "🆕 Новая заявка на сервер\n\n"
        f"🎮 Ник: {nickname}\n"
        f"👤 Telegram: @{applicant.username or 'без username'}\n"
        f"🆔 ID: {applicant.id}"
    )

    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

    await update.message.reply_text(
        "📨 Заявка отправлена администрации!\n\nОжидайте одобрения. Обычно это занимает несколько минут."
    )


def add_to_whitelist(nickname: str):
    url = f"https://mgr.hosting-minecraft.pro/api/client/servers/{SERVER_ID}/command"

    headers = {
        "Authorization": f"Bearer {HOSTING_API_TOKEN}",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

    payload = {
        "command": f"whitelist add {nickname}"
    }

    response = requests.post(
        url,
        headers=headers,
        json=payload,
        timeout=10
    )

    if response.status_code not in (200, 204):
        raise Exception(f"API ошибка {response.status_code}: {response.text}")


def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_nickname)
    )

    print("Бот запущен")
    app.run_polling()


if __name__ == "__main__":
    main()
