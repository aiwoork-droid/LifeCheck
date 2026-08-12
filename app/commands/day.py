from database.repositories.day_items import day_items


def execute(api, chat_id, user_id):

    items = day_items.get_items(user_id)

    text = (
        "📋 <b>Мой день</b>\n\n"

        "Настройте свой ежедневный экран.\n"
        "Все отмеченные пункты будут автоматически\n"
        "появляться на экране <b>Сегодня</b>.\n\n"

        "━━━━━━━━━━━━━━\n\n"
    )

    for number, item in enumerate(items, start=1):

        mark = "☑" if item["enabled"] else "☐"

        text += f"{number}. {mark} {item['title']}\n"

    text += (
        "\n━━━━━━━━━━━━━━\n\n"

        "Введите номер,\n"
        "чтобы включить или выключить пункт.\n\n"

        "0. 🔙 Назад"
    )

    api.send_message(
        chat_id=chat_id,
        text=text
    )