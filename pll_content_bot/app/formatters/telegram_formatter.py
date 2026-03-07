from __future__ import annotations


def format_roman_post(item: dict[str, str]) -> str:
    return (
        "📜 Roman Law Today\n\n"
        f"{item['reference']}\n\n"
        f"{item['latin']}\n\n"
        "Перевод\n"
        f"{item['translation']}\n\n"
        "Смысл\n"
        f"{item['explanation']}\n\n"
        "Современный аналог\n"
        f"{item['modern']}"
    )


def format_argument_post(topic: str, generated: dict[str, str] | None) -> str:
    if not generated:
        return "⚖️ Аргумент дня\n\nВопрос\n" + topic
    return (
        "⚖️ Аргумент дня\n\n"
        "Вопрос\n"
        f"{topic}\n\n"
        'Аргумент "за"\n'
        f"{generated.get('pro', '').strip()}\n\n"
        'Аргумент "против"\n'
        f"{generated.get('con', '').strip()}\n\n"
        "Вывод\n"
        f"{generated.get('synthesis', '').strip()}"
    )
