def execute(api, chat_id):

    text = (
        "📚 <b>Привычки</b>\n\n"
        "1. ➕ Добавить привычку\n"
        "2. 📋 Все привычки\n"
        "3. ❌ Удалить привычку\n\n"
        "0. 🔙 Назад"
    )

    api.send_message(
        chat_id=chat_id,
        text=text
    )