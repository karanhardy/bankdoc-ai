from config import settings

def main():
    print(f"Starting {settings.app_name}")
    print(f"Environment: {settings.environment}")
    print(f"Bronze: {settings.bronze_path}")
    print(f"Silver: {settings.silver_path}")
    print(f"Gold: {settings.gold_path}")

if __name__ == "__main__":
    main()