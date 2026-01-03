import logging
import sqlite3
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackQueryHandler

# Включи логи
logging.basicConfig(level=logging.INFO)

# Твой токен и username
BOT_TOKEN = '8332849632:AAGwEgBOJUATZjICBROngFqk07btW_2rkd4'
BOT_USERNAME = 'your_luck_v2_bot'

# Инициализация БД
conn = sqlite3.connect('referrals.db', check_same_thread=False)
cursor = conn.cursor()
cursor.execute(
    '''CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        balance INTEGER DEFAULT 0,
        referrals INTEGER DEFAULT 0,
        referred_by INTEGER
    )'''
)
conn.commit()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    args = context.args
    cursor.execute('INSERT OR IGNORE INTO users (user_id) VALUES (?)', (user_id,))
    conn.commit()

    if args:
        ref_id = int(args[0])
        if ref_id != user_id:  # Не самоприглашение
            cursor.execute('UPDATE users SET referred_by=? WHERE user_id=?', (ref_id, user_id))
            cursor.execute(
                'UPDATE users SET referrals = referrals + 1, balance = balance + 10 WHERE user_id=?',
                (ref_id,),
            )
            conn.commit()
            # уведомление рефереру (обязательно await!)
            await context.bot.send_message(
                ref_id,
                "🎉 *РЕФЕРАЛ УСПЕШНО ЗАРЕГИСТРИРОВАН!*\n\n"
                "💸 *Тебе начислено:* +10 монет\n"
                "👤 *Новый участник* присоединился к твоей сети!\n"
                "📈 *Твой ранг растет!* Продолжай!\n\n"
                f"🔗 *Еще рефералы → еще монет:*\n`https://t.me/{BOT_USERNAME}?start={ref_id}`",
                parse_mode='Markdown',
            )

    cursor.execute('SELECT balance, referrals FROM users WHERE user_id=?', (user_id,))
    data = cursor.fetchone() or (0, 0)

    text = (
        "🚀 *Добро пожаловать в рефералку!*\n\n"
        f"💰 *Твой баланс:* {data[0]} монет | 👥 *Рефералов:* {data[1]}\n\n"
        "🔥 *ПРИГЛАШАЙ ДРУЗЕЙ = ПОЛУЧАЙ БОНУСЫ!*\n"
        "• Каждая регистрация = **+10 монет ВАМ**\n"
        "• Топ рефереров = эксклюзивные награды\n"
        "• Чем больше друзей → тем жирнее профит!\n\n"
        "👇 *Выбери действие:*"
    )

    keyboard = [[
        InlineKeyboardButton("💎 Моя ссылка", callback_data='link'),
        InlineKeyboardButton("🏆 Лидерборд", callback_data='leaderboard'),
    ]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')


async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()

    if query.data == 'link':
        cursor.execute('SELECT referrals FROM users WHERE user_id=?', (user_id,))
        row = cursor.fetchone()
        refs = row[0] if row and row[0] is not None else 0

        link = f"https://t.me/{BOT_USERNAME}?start={user_id}"
        text = (
            "🔗 *ТВОЯ РЕФЕРАЛЬНАЯ ССЫЛКА:*\n"
            f"`{link}`\n\n"
            "🎯 *КАК ПОБЕДИТЬ:*\n"
            "✅ Копируй → отправляй друзьям\n"
            "✅ Они жмут и регистрируются\n"
            "✅ **БАМ! +10 монет тебе** на баланс\n\n"
            f"📈 *Уже {refs} человек в твоей сети!*\n"
            "*Поделись сейчас → стань топ-1!* 👑"
        )

        await query.edit_message_text(text, parse_mode='Markdown')

    elif query.data == 'leaderboard':
        cursor.execute(
            'SELECT user_id, referrals, balance FROM users ORDER BY referrals DESC LIMIT 10'
        )
        top = cursor.fetchall()

        text = "👑 *ТОП РЕФЕРЕЛОВ СИСТЕМЫ:*\n\n"
        for i, (uid, refs, bal) in enumerate(top, 1):
            text += f"{i}. *{refs}* реф ({bal} монет)\n"

        cursor.execute('SELECT referrals FROM users WHERE user_id=?', (user_id,))
        row = cursor.fetchone()
        user_refs = row[0] if row and row[0] is not None else 0
        cursor.execute('SELECT COUNT(*) FROM users WHERE referrals > ?', (user_refs,))
        position = cursor.fetchone()[0] + 1

        text += f"\n🔥 *ТЫ НА МЕСТЕ #{position}* ({user_refs} рефералов)\n"
        text += "💎 *Поделись ссылкой → догони лидеров!*"

        await query.edit_message_text(text or "Пока пусто...", parse_mode='Markdown')


def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button))
    app.run_polling()


if __name__ == "__main__":
    main()
