import os
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

HOSTING_API_TOKEN = os.getenv("HOSTING_API_TOKEN")
SERVER_ID = os.getenv("SERVER_ID")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Бот белого списка Minecraft работает!\n"
        "Игроки могут подать заявку командой:\n"
        "/join Ник"
    )


async def join(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 1:
        await update.message.reply_text("Использование: /join Ник")
        return

    nickname = context.args[0]
    applicant = update.effective_user

    keyboard = [
        [
            InlineKeyboardButton(
                "Одобрить",
                callback_data=f"approve:{nickname}:{applicant.id}"
            ),
            InlineKeyboardButton(
                "Отклонить",
                callback_data=f"reject:{nickname}:{applicant.id}"
            ),
        ]
    ]

    text = (
        "Новая заявка на сервер\n\n"
        f"Ник: {nickname}\n"
        f"Telegram: @{applicant.username or 'без username'}\n"
        f"ID: {applicant.id}"
    )

    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

    await update.message.reply_text(
        "Заявка отправлена администрации. Ожидайте одобрения."
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
        raise Exception(
            f"API ошибка {response.status_code}: {response.text}"
        )


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    action, nickname, applicant_id = query.data.split(":")
    applicant_id = int(applicant_id)

    if query.from_user.id != ADMIN_ID:
        await query.edit_message_text(
            "У вас нет прав для этого действия."
        )
        return

    if action == "approve":
        try:
            add_to_whitelist(nickname)

            await context.bot.send_message(
                chat_id=applicant_id,
                text=(
                    f"Ваша заявка одобрена!\n"
                    f"Вы добавлены в whitelist под ником: {nickname}"
                )
            )

            await query.edit_message_text(
                f"Заявка одобрена\n"
                f"Ник: {nickname}\n"
                f"Игрок автоматически добавлен в whitelist."
            )

        except Exception as e:
            await query.edit_message_text(
                f"Ошибка при добавлении в whitelist:\n{e}"
            )

    else:
        await context.bot.send_message(
            chat_id=applicant_id,
            text=f"Ваша заявка на ник {nickname} была отклонена."
        )

        await query.edit_message_text(
            f"Заявка отклонена\n"
            f"Ник: {nickname}"
        )


def main():
    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN не задан")

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("join", join))
    app.add_handler(CallbackQueryHandler(button_handler))

    print("Бот запущен")
    app.run_polling()


if __name__ == "__main__":
    main()
