from database.init_db import initialize_database
from core.bot import LifeCheckBot


def main():

    print("=" * 50)
    print("LifeCheck v0.3.2")
    print("=" * 50)

    initialize_database()

    bot = LifeCheckBot()

    bot.run()


if __name__ == "__main__":
    main()