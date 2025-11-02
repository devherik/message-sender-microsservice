from core.settings import settings

def main():
    print("Hello from message-sender-microsservice!")
    print(f"Postgres DSN: {settings.get_postgres_dsn}")

if __name__ == "__main__":
    main()
