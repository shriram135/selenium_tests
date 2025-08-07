# open_close_browser.py
import webbrowser

while True:
    print("\nOptions:")
    print("1. Open Mini Shop")
    print("2. Exit")
    choice = input("Enter your choice (1/2): ")

    if choice == "1":
        webbrowser.open("http://localhost/minishop/index.php")
        print("Mini Shop opened in browser.")
    elif choice == "2":
        print("Exiting program.")
        break
    else:
        print("Invalid input. Try again.")
