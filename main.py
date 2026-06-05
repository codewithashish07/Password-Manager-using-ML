from manager import generate_key, encrypt_password, decrypt_password
from database import init_db, save_password, get_all_passwords, delete_password
from ml_model import predict_strength, train_model
from breach_check import check_breach
from generator import generate_password, calculate_entropy, suggest_passwords

def add_password():
    site = input("Enter website/app name: ")
    username = input("Enter username/email: ")

    use_generated = input("Generate a strong password? (y/n): ").lower()
    if use_generated == 'y':
        password = generate_password()
        print(f"Generated password: {password}")
    else:
        password = input("Enter password: ")

    # ML Strength Check
    strength = predict_strength(password)
    print(f"Password strength: {strength['label']} (confidence: {strength['score']})")

    # Entropy
    entropy = calculate_entropy(password)
    print(f"Entropy: {entropy} bits")

    # Breach Check
    print("Checking for breaches...")
    breach = check_breach(password)
    if breach.get("breached"):
        print(f"⚠️  WARNING: This password was found {breach['count']} times in data breaches!")
        confirm = input("Save anyway? (y/n): ").lower()
        if confirm != 'y':
            return
    else:
        print("✅ Password not found in known breaches.")

    encrypted = encrypt_password(password)
    save_password(site, username, encrypted, strength["raw"])
    print("✅ Password saved securely!\n")

def view_passwords():
    records = get_all_passwords()
    if not records:
        print("No passwords stored yet.")
        return
    print(f"\n{'ID':<5} {'Site':<20} {'Username':<25} {'Strength':<10}")
    print("-" * 65)
    for row in records:
        strength_map = {0: "Weak 🔴", 1: "Medium 🟡", 2: "Strong 🟢"}
        strength = strength_map.get(int(row[4] or 0), "Unknown")
        print(f"{row[0]:<5} {row[1]:<20} {row[2]:<25} {strength:<10}")

def retrieve_password():
    view_passwords()
    try:
        record_id = int(input("\nEnter ID to retrieve: "))
        records = get_all_passwords()
        for row in records:
            if row[0] == record_id:
                plain = decrypt_password(row[3])
                print(f"\nSite: {row[1]}")
                print(f"Username: {row[2]}")
                print(f"Password: {plain}")
                return
        print("Record not found.")
    except ValueError:
        print("Invalid ID.")

def delete_entry():
    view_passwords()
    try:
        record_id = int(input("\nEnter ID to delete: "))
        delete_password(record_id)
        print("✅ Deleted successfully.")
    except ValueError:
        print("Invalid ID.")

def main():
    generate_key()
    init_db()
    train_model()

    while True:
        print("\n===== ML Password Manager =====")
        print("1. Add / Save a password")
        print("2. View all passwords")
        print("3. Retrieve a password")
        print("4. Delete a password")
        print("5. Suggest strong passwords")
        print("6. Exit")

        choice = input("Choose an option: ")

        if choice == "1":
            add_password()
        elif choice == "2":
            view_passwords()
        elif choice == "3":
            retrieve_password()
        elif choice == "4":
            delete_entry()
        elif choice == "5":
            print("\nSuggested strong passwords:")
            for i, p in enumerate(suggest_passwords(), 1):
                print(f"  {i}. {p}  (entropy: {calculate_entropy(p)} bits)")
        elif choice == "6":
            print("Goodbye Ashish! 👋")
            break
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main()