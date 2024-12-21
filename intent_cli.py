import subprocess

def show_menu():
    print("\n======================")
    print(" SDN Link Manager CLI")
    print("======================")
    print("1. Downlink (Block connection between s1 and s2)")
    print("2. Uplink (Unblock connection between s1 and s2)")
    print("3. Exit")
    print("======================")

def execute_curl(command):
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print("\nResponse from the server:")
        print(result.stdout)
    except subprocess.CalledProcessError as e:
        print("\nError executing the curl command:")
        print(e.stderr)

def main():
    while True:
        show_menu()
        choice = input("Enter your choice (1/2/3): ").strip()

        if choice == "1":
            print("\nExecuting: Downlink (Blocking connection between s1 and s2)...")
            curl_command = "curl -X POST http://127.0.0.1:8080/link/down"
            execute_curl(curl_command)

        elif choice == "2":
            print("\nExecuting: Uplink (Unblocking connection between s1 and s2)...")
            curl_command = "curl -X POST http://127.0.0.1:8080/link/up"
            execute_curl(curl_command)

        elif choice == "3":
            print("\nExiting the SDN Link Manager CLI. Goodbye!")
            break

        else:
            print("\nInvalid choice! Please try again.")

if __name__ == "__main__":
    main()


