import socket
import time
from datetime import datetime

# 服务器配置
SERVER_PORT = 2560
ACCOUNT_FILE = 'web-exp/accounts.dat'
LOG_FILE = 'web-exp/server.log'

# 加载账户数据
def load_accounts():
    accounts = {}
    with open(ACCOUNT_FILE, 'r') as f:
        for line in f:
            line = line.strip()
            if not line:  # 跳过空行
                continue
            card_no, pin, balance = line.split()
            accounts[card_no] = {'pin': pin, 'balance': float(balance)}
    return accounts

# 保存账户数据
def save_accounts(accounts):
    with open(ACCOUNT_FILE, 'w') as f:
        for card_no, data in accounts.items():
            f.write(f"{card_no} {data['pin']} {data['balance']}\n")

# 记录日志
def log(message):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with open(LOG_FILE, 'a') as f:
        f.write(f"{timestamp} - {message}\n")

# 主服务器
def main():
    accounts = load_accounts()
    log(f"Server started on port {SERVER_PORT}")
    
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('', SERVER_PORT))
    server_socket.listen(1)
    print(f"ATM server listening on port {SERVER_PORT}")

    while True:
        conn, addr = server_socket.accept()
        log(f"Connection from {addr}")
        current_card = None
        
        try:
            while True:
                data = conn.recv(1024).decode().strip()
                if not data:
                    break
                    
                log(f"Received: {data}")
                
                # 处理协议消息
                if data.startswith('HELO'):
                    _, card_no = data.split()
                    if card_no in accounts:
                        current_card = card_no
                        conn.send(b'500 AUTH REQUIRE')
                    else:
                        conn.send(b'401 ERROR!')
                        
                elif data.startswith('PASS'):
                    _, pin = data.split()
                    if current_card and accounts[current_card]['pin'] == pin:
                        conn.send(b'525 OK!')
                    else:
                        conn.send(b'401 ERROR!')
                        
                elif data == 'BALA':
                    if current_card:
                        balance = accounts[current_card]['balance']
                        conn.send(f'AMNT:{balance}'.encode())
                    else:
                        conn.send(b'401 ERROR!')
                        
                elif data.startswith('WDRA'):
                    _, amount = data.split()
                    amount = float(amount)
                    if current_card and accounts[current_card]['balance'] >= amount:
                        accounts[current_card]['balance'] -= amount
                        save_accounts(accounts)
                        conn.send(b'525 OK!')
                    else:
                        conn.send(b'401 ERROR!')
                        
                elif data == 'BYE':
                    conn.send(b'BYE')
                    break
                    
        finally:
            conn.close()
            log(f"Connection closed with {addr}")

if __name__ == '__main__':
    main()
