def execute(api, chat_id, first_name):

    text = (
        f"☀️ <b>Добро пожаловать, {first_name}!</b>\n\n"

        "Добро пожаловать в <b>LifeCheck</b>.\n"
        "Ваш личный помощник на каждый день.\n\n"

        "━━━━━━━━━━━━━━\n\n"

        "1. ☀️ Сегодня\n"
        "2. 📋 Мой день\n"
        "3. 📚 Привычки\n"
        "4. ❤️ Здоровье\n"
        "5. 📊 Статистика\n"
        "6. ⚙️ Настройки"
    )

    api.send_message(
        chat_id=chat_id,
        text=text
    )