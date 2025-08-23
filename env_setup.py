import os

def main():
    env_file = ".env"

    print("Let's set up your .env file.\n")

    # Prompt for environment variables
    db_name = input("Enter DB_NAME: ").strip()
    db_user = input("Enter DB_USER: ").strip()
    db_password = input("Enter DB_PASSWORD: ").strip()
    db_host = input("Enter DB_HOST (default: localhost): ").strip() or "localhost"
    db_port = input("Enter DB_PORT (default: 5432): ").strip() or "5432"
    gemini_key = input("Enter gemini_key: ").strip()

    # Build content
    env_content = f"""DB_NAME={db_name}
DB_USER={db_user}
DB_PASSWORD={db_password}
DB_HOST={db_host}
DB_PORT={db_port}
GEMINI_KEY={gemini_key}
"""

    # Write to .env
    with open(env_file, "w") as f:
        f.write(env_content)

    print(f"\n✅ .env file created at {os.path.abspath(env_file)}")


if __name__ == "__main__":
    main()
