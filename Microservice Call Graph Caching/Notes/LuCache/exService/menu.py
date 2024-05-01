import requests
import time
import json

# Define the URL of the service
URL_FRONTEND = 'http://localhost:5555'
URL_CALLER_R = 'http://localhost:6666'
URL_CALLER_W = 'http://localhost:7777'

def caller_write(key=None, value=None):
    if key is None:
        key = input("Enter the key: ")
    if value is None:
        value = input("Enter the value: ")
    response = requests.get(f'{URL_CALLER_W}/call_write', params={'key': key, 'value': value})
    response_content = response.json() if response.headers['Content-Type'] == 'application/json' else response.text
    if response.status_code == 200:
        print(f"[+] caller_write successful(visited services: {response_content['visited']})")
    else:
        print(f"[-] caller_write operation failed with status code: {response.status_code}")

def caller_read(key=None):
    if key is None:
        key = input("Enter the key: ")
    response = requests.get(f'{URL_CALLER_R}/call_read', params={'key': key})
    response_content = response.json() if response.headers['Content-Type'] == 'application/json' else response.text
    if response.status_code == 200:
        print(f"[+] caller_read successful(cacheHit: {response_content['cache_hit']}, result: {response_content['data']}, visited services: {response_content['visited']})")
    else:
        print(f"[-] caller_read operation failed({response_content['data']}, status code: {response.status_code})")
        
def frontend_read(key=None):
    if key is None:
        key = input("Enter the key: ")
    response = requests.get(f'{URL_FRONTEND}/read_from_caller', params={'key': key})
    response_content = response.json() if response.headers['Content-Type'] == 'application/json' else response.text
    if response.status_code == 200:
        print(f"[+] frontend_read successful(cacheHit: {response_content['cache_hit']}, result: {response_content['data']}, visited services: {response_content['visited']})")
    else:
        print(f"[-] frontend_read operation failed({response_content['data']}, status code: {response.status_code})")
        
def frontend_write(key=None, value=None):
    if key is None:
        key = input("Enter the key: ")
    if value is None:
        value = input("Enter the value: ")
    response = requests.get(f'{URL_FRONTEND}/write_to_caller', params={'key': key, 'value': value})
    if response.headers['Content-Type'] == 'application/json':
        response_content = response.json()
    else:
        try:
            response_content = json.loads(response.text)
        except json.JSONDecodeError:
            response_content = response.text
    if response.status_code == 200:
        print(f"[+] frontend_write successful(visited services: {response_content['visited']})")
    else:
        print(f"[-] frontend_write operation failed with status code: {response.status_code}")
        
def show_infos():
    print("\n------------------------------")
    print("Ports Info:")
    print("frontend: 5555")
    print("caller_read: 6666")
    print("caller_write: 7777")
    print("callee: 8888")
    print("------------------------------\n")
    
def show_menu():
    while True:
        print("------------------------------")
        print("Menu:")
        print("0: Show Infos")
        print("1: caller read")
        print("2: caller write")
        print("3: frontend read")
        print("4: frontend write")
        print("------------------------------")
        choice = input("Enter your choice: ")
        if choice == '0':
            show_infos()
        elif choice == '1':
            caller_read()
        elif choice == '2':
            caller_write()
        elif choice == '3':
            frontend_read()
        elif choice == '4':
            frontend_write()
        else:
            print("Exiting...")
            print("Thank you for using LuCache Protocol ^_^\n")
            break
        time.sleep(10)