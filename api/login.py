from http.server import BaseHTTPRequestHandler
import json
import os
import hashlib
import hmac
from urllib.parse import parse_qs
from api.database import db

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length).decode()
            data = parse_qs(post_data)
            
            # Извлекаем данные из формы
            hash_value = data.get('hash', [''])[0]
            user_id = int(data.get('id', [0])[0])
            username = data.get('username', [''])[0]
            first_name = data.get('first_name', [''])[0]
            
            if not self.verify_telegram_data(data, hash_value):
                self.send_error(401, "Invalid Telegram hash")
                return
            
            # Создаем/обновляем пользователя
            await db.create_user(user_id, username)
            
            # Устанавливаем куки через JavaScript
            response_data = {
                'success': True,
                'user_id': user_id,
                'username': username,
                'redirect': '/games.html'
            }
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            self.wfile.write(json.dumps(response_data).encode())
            
        except Exception as e:
            self.send_error(500, str(e))
    
    def verify_telegram_data(self, data, hash_value):
        """Проверка подписи Telegram"""
        try:
            # Создаем строку для проверки
            check_string = []
            for key in sorted(data.keys()):
                if key != 'hash':
                    check_string.append(f"{key}={data[key][0]}")
            check_string = "\n".join(check_string)
            
            # Создаем секретный ключ из токена бота
            secret_key = hashlib.sha256(os.environ['BOT_TOKEN'].encode()).digest()
            
            # Вычисляем HMAC
            hmac_string = hmac.new(
                secret_key,
                check_string.encode(),
                hashlib.sha256
            ).hexdigest()
            
            return hmac_string == hash_value
            
        except:
            return False
    
    def do_OPTIONS(self):
        # Для CORS
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
