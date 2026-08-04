from dotenv import load_dotenv
import os

print("=" * 50)
print("        LifeCheck v0.0.1")
print("=" * 50)

# Загрузка .env
load_dotenv()

# Проверка токена
token = os.getenv("BOT_TOKEN")

# Проверка структуры проекта
folders = [
    "app",
    "assets",
    "config",
    "core",
    "database",
    "docs",
    "modules",
    "tests",
]

files = [
    ".env",
    ".gitignore",
    "README.md",
    "requirements.txt",
    "main.py",
    "config/settings.py",
    "app/bot.py",
    "app/handlers.py",
    "app/keyboard.py",
]

print("\nПроверка проекта...\n")

ok = True

# Проверка папок
for folder in folders:
    if os.path.isdir(folder):
        print(f"✅ Папка {folder}")
    else:
        print(f"❌ Нет папки {folder}")
        ok = False

# Проверка файлов
for file in files:
    if os.path.isfile(file):
        print(f"✅ Файл {file}")
    else:
        print(f"❌ Нет файла {file}")
        ok = False

# Проверка токена
if token:
    print("\n✅ BOT_TOKEN найден")
else:
    print("\n❌ BOT_TOKEN не найден")
    ok = False

print("\n" + "=" * 50)

if ok:
    print("🎉 LifeCheck готов к следующему этапу!")
else:
    print("⚠️ Есть проблемы, которые нужно исправить.")

print("=" * 50)