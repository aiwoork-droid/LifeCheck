def execute(api, chat_id, first_name):
    """Отправляет главное меню LifeCheck с inline-кнопками MAX."""

    text = (
        f"☀️ <b>LifeCheck</b>\n"
        f"Привет, {first_name}!\n\n"
        "Выберите раздел:"
    )

    buttons = [
        [
            {
                "type": "callback",
                "text": "☀️ Сегодня",
                "payload": "main:1"
            },
            {
                "type": "callback",
                "text": "📋 Мой день",
                "payload": "main:2"
            }
        ],
        [
            {
                "type": "callback",
                "text": "📚 Привычки",
                "payload": "main:3"
            },
            {
                "type": "callback",
                "text": "❤️ Здоровье",
                "payload": "main:4"
            }
        ],
        [
            {
                "type": "callback",
                "text": "📊 Статистика",
                "payload": "main:5"
            },
            {
                "type": "callback",
                "text": "⚙️ Настройки",
                "payload": "main:6"
            }
        ]
    ]

    return api.send_message(
        chat_id=chat_id,
        text=text,
        buttons=buttons
    )
