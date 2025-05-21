import sys
from socket import *
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, 
    QVBoxLayout, QLabel, QLineEdit,
    QPushButton, QMessageBox
)

class LoginWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('ATM 登录')
        self.setFixedSize(350, 250)
        
        # 设置样式
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f5f5;
            }
            QLabel {
                font-size: 14px;
                color: #333;
            }
            QLineEdit {
                padding: 8px;
                border: 1px solid #ddd;
                border-radius: 4px;
                font-size: 14px;
            }
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 10px;
                border-radius: 4px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        
        self.server_ip = 'localhost'
        self.server_port = 2525
        self.socket = None
        self.card_no = None
        
        # 创建UI
        central_widget = QWidget()
        layout = QVBoxLayout()
        
        self.card_input = QLineEdit()
        self.card_input.setPlaceholderText('请输入卡号')
        layout.addWidget(QLabel('卡号:'))
        layout.addWidget(self.card_input)
        
        self.pin_input = QLineEdit()
        self.pin_input.setPlaceholderText('请输入密码')
        self.pin_input.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(QLabel('密码:'))
        layout.addWidget(self.pin_input)
        
        login_btn = QPushButton('登录')
        login_btn.clicked.connect(self.handle_login)
        layout.addWidget(login_btn)
        
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)
    
    def connect_to_server(self):
        try:
            self.socket = socket(AF_INET, SOCK_STREAM)
            self.socket.connect((self.server_ip, self.server_port))
            return True
        except Exception as e:
            QMessageBox.critical(self, '错误', f'无法连接到服务器: {str(e)}')
            return False
    
    def handle_login(self):
        if not self.connect_to_server():
            return
            
        card_no = self.card_input.text().strip()
        pin = self.pin_input.text().strip()
        
        if not card_no or not pin:
            QMessageBox.warning(self, '警告', '请输入卡号和密码')
            return
            
        try:
            # 发送HELO消息
            self.socket.send(f'HELO {card_no}'.encode())
            response = self.socket.recv(1024).decode()
            
            if response != '500 AUTH REQUIRE':
                raise Exception('无效的服务器响应')
                
            # 发送PASS消息
            self.socket.send(f'PASS {pin}'.encode())
            response = self.socket.recv(1024).decode()
            
            if response == '525 OK!':
                self.card_no = card_no
                self.show_atm_window()
            else:
                QMessageBox.warning(self, '错误', '卡号或密码错误')
                
        except Exception as e:
            QMessageBox.critical(self, '错误', f'登录失败: {str(e)}')
            self.socket.close()
    
    def show_atm_window(self):
        self.atm_window = ATMWindow(self.socket, self.card_no)
        self.atm_window.show()
        self.close()

class ATMWindow(QMainWindow):
    def __init__(self, socket, card_no):
        super().__init__()
        self.setWindowTitle('ATM 操作')
        self.setFixedSize(450, 350)
        
        
        self.socket = socket
        self.card_no = card_no
        
        # 创建UI
        central_widget = QWidget()
        layout = QVBoxLayout()
        
        self.balance_label = QLabel('余额: --')
        self.balance_label.setObjectName("balance_label")
        layout.addWidget(self.balance_label)
        
        # 设置样式
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f5f5;
            }
            QLabel {
                font-size: 16px;
                color: #333;
                font-weight: bold;
            }
            QLineEdit {
                padding: 8px;
                border: 1px solid #ddd;
                border-radius: 4px;
                font-size: 14px;
            }
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 10px;
                border-radius: 4px;
                font-size: 14px;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #0b7dda;
            }
            #balance_label {
                font-size: 18px;
                color: #4CAF50;
            }
        """)
        
        check_balance_btn = QPushButton('查询余额')
        check_balance_btn.clicked.connect(self.check_balance)
        layout.addWidget(check_balance_btn)
        
        self.amount_input = QLineEdit()
        self.amount_input.setPlaceholderText('输入取款金额')
        layout.addWidget(QLabel('取款金额:'))
        layout.addWidget(self.amount_input)
        
        withdraw_btn = QPushButton('取款')
        withdraw_btn.clicked.connect(self.withdraw)
        layout.addWidget(withdraw_btn)
        
        logout_btn = QPushButton('退出')
        logout_btn.clicked.connect(self.logout)
        layout.addWidget(logout_btn)
        
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)
    
    def check_balance(self):
        try:
            self.socket.send(b'BALA')
            response = self.socket.recv(1024).decode()
            
            if response.startswith('AMNT:'):
                balance = response.split(':')[1]
                self.balance_label.setText(f'余额: {balance}')
            else:
                QMessageBox.warning(self, '错误', '查询余额失败')
                
        except Exception as e:
            QMessageBox.critical(self, '错误', f'查询失败: {str(e)}')
    
    def withdraw(self):
        amount = self.amount_input.text().strip()
        if not amount:
            QMessageBox.warning(self, '警告', '请输入取款金额')
            return
            
        try:
            amount = float(amount)
            if amount <= 0:
                raise ValueError('金额必须大于0')
                
            self.socket.send(f'WDRA {amount}'.encode())
            response = self.socket.recv(1024).decode()
            
            if response == '525 OK!':
                QMessageBox.information(self, '成功', '取款成功')
                self.check_balance()
            else:
                QMessageBox.warning(self, '错误', '取款失败: 余额不足')
                
        except ValueError:
            QMessageBox.warning(self, '错误', '请输入有效的金额')
        except Exception as e:
            QMessageBox.critical(self, '错误', f'取款失败: {str(e)}')
    
    def logout(self):
        try:
            self.socket.send(b'BYE')
            self.socket.recv(1024)  # 等待服务器返回BYE
        except:
            pass
            
        self.socket.close()
        self.close()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = LoginWindow()
    window.show()
    sys.exit(app.exec())
