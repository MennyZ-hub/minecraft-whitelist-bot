import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from mcrcon import MCRcon

BOT_TOKEN = os.getenv('BOT_TOKEN')
ADMIN_ID = int(os.getenv('ADMIN_ID'))

RCON_HOST = os.getenv('RCON_HOST')
RCON_PORT = int(os.getenv('RCON_PORT'))
RCON_PASSWORD = os.getenv('RCON_PASSWORD')


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        'Бот белого списка Minecraft работает!\n'
        'Игроки могут подать заявку командой:\n'
        '/join Ник'
    )


async def join(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 1:
        await update.message.reply_text('Использование: /join Ник')
        return

    nickname = context.args[0]
    applicant = update.effective_user

    keyboard = [
        [
            InlineKeyboardButton(
                'Одобрить',
                callback_data=f'approve:{nickname}:{applicant.id}'
            ),
            InlineKeyboardButton(
                'Отклонить',
                callback_data=f'reject:{nickname}:{applicant.id}'
            ),
        ]
    ]

    text = (
        'Новая заявка на сервер\n\n'
        f'Ник: {nickname}\n'
        f'Telegram: @{applicant.username or "без username"}\n'
        f'ID: {applicant.id}'
    )

    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

    await update.message.reply_text(
        'Заявка отправлена администрации. Ожидайте одобрения.'
    )


def add_to_whitelist(nickname: str):
    with MCRcon(RCON_HOST, RCON_PASSWORD, port=RCON_PORT) as mcr:
        mcr.command(f'whitelist add {nickname}')
        mcr.command('whitelist reload')


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    action, nickname, applicant_id = query.data.split(':')
    applicant_id = int(applicant_id)

    if query.from_user.id != ADMIN_ID:
        await query.edit_message_text('У вас нет прав для этого действия.')
        return

    if action == 'approve':
        try:
            add_to_whitelist(nickname)

            await context.bot.send_message(
                chat_id=applicant_id,
                text=(
                    f'Ваша заявка одобрена!\n'
                    f'Вы добавлены в whitelist под ником: {nickname}'
                )
            )

            await query.edit_message_text(
                f'Заявка одобрена\n'
                f'Ник: {nickname}\n'
                f'Игрок автоматически добавлен в whitelist.'
            )

        except Exception as e:
            await query.edit_message_text(
                f'Ошибка при добавлении в whitelist:\n{e}'
            )

    else:
        await context.bot.send_message(
            chat_id=applicant_id,
            text=f'Ваша заявка на ник {nickname} была отклонена.'
        )

        await query.edit_message_text(
            f'Заявка отклонена\n'
            f'Ник: {nickname}'
        )


def main():
    if not BOT_TOKEN:
        raise ValueError('BOT_TOKEN не задан')

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler('start', start))
    app.add_handler(CommandHandler('join', join))
    app.add_handler(CallbackQueryHandler(button_handler))

    print('Бот запущен')
    app.run_polling()


if __name__ == '__main__':
    main()
