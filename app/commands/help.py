def execute(api, message):

    chat_id = message["recipient"]["chat_id"]

    api.send_message(
        chat_id=chat_id,
        text=(
            "📖 Доступные команды\n\n"
            "/start — регистрация\n"
            "/help — помощь"
        )
    )