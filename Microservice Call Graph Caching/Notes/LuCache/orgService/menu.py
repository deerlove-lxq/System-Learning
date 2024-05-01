import requests

# 定义服务的基础URL
URL_FRONTEND = 'http://localhost:5555'
URL_CALLER_R = 'http://localhost:6666'
URL_CALLER_W = 'http://localhost:7777'

def caller_write():
    key = input("Enter the key: ")
    value = input("Enter the value: ")
    data = {key: value}
    response = requests.post(f'{URL_CALLER_W}/caller_write', json=data)
    if response.status_code == 200:
        print("[+] caller_write operation successful.")
    else:
        print(f"[-] caller_write operation failed with status code: {response.status_code}")

def caller_read():
    key = input("Enter the key: ")
    response = requests.get(f'{URL_CALLER_R}/caller_read', params={'key': key})
    if response.status_code == 200:
        print(f"[+] caller_read response: {response.json()}")
    else:
        print(f"[-] caller_read operation failed: {response.content}")
        
def frontend_read():
    key = input("Enter the key: ")
    response = requests.get(f'{URL_FRONTEND}/read_from_caller', params={'key': key})
    if response.status_code == 200:
        print(f"[+] frontend_read response: {response.json()}")
    else:
        print(f"[-] frontend_read operation failed: {response.content}")
        
def frontend_write():
    key = input("Enter the key: ")
    value = input("Enter the value: ")
    data = {key: value}
    response = requests.post(f'{URL_FRONTEND}/write_to_caller', json=data)
    if response.status_code == 200:
        print("[+] frontend_write operation successful.")
    else:
        print(f"[-] frontend_write operation failed with status code: {response.status_code}")
    
        
def show_ports_info():
    print("\n------------------------------")
    print("Ports Info:")
    print("frontend: 5555")
    print("caller_read: 6666")
    print("caller_write: 7777")
    print("callee: 8888")
    print("------------------------------")

# 定义主函数，提供交互式菜单
def main():
    while True:
        print("\n------------------------------")
        print("Menu:")
        print("0: Show Ports Info")
        print("1: caller_read")
        print("2: caller_write")
        print("3: frontend_read")
        print("4: frontend_write")
        print("------------------------------")
        choice = input("Enter your choice: ")
        if choice == '0':
            show_ports_info()
        elif choice == '1':
            caller_read()
        elif choice == '2':
            caller_write()
        elif choice == '3':
            frontend_read()
        elif choice == '4':
            frontend_write()
        else:
            print("Exiting menu...")
            break
            
if __name__ == "__main__":
    main()