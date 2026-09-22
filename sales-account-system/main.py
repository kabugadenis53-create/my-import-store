from src.database import create_tables


def main() -> None:
    create_tables()
    print("Sales account database created successfully.")


if __name__ == "__main__":
    main()
