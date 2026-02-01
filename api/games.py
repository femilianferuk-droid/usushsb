from http.server import BaseHTTPRequestHandler
import json
import random
from urllib.parse import urlparse, parse_qs
from api.database import db

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = json.loads(self.rfile.read(content_length))
            
            # Получаем куки
            cookies = self.parse_cookies()
            user_id = cookies.get('user_id')
            
            if not user_id:
                self.send_error(401, "Not authenticated")
                return
            
            user_id = int(user_id)
            game_type = post_data.get('game')
            bet = float(post_data.get('bet', 0))
            
            # Проверяем баланс
            user = await db.get_user(user_id)
            if not user or user['balance'] < bet:
                self.send_error(400, "Insufficient balance")
                return
            
            result = await self.play_game(game_type, bet, post_data)
            
            # Обновляем баланс
            if result['win']:
                await db.update_balance(user_id, result['amount'] - bet)
                await db.add_transaction(
                    user_id,
                    result['amount'] - bet,
                    "game_win",
                    f"Выигрыш в {game_type}: x{result['multiplier']:.2f}"
                )
            else:
                await db.update_balance(user_id, -bet)
                await db.add_transaction(
                    user_id,
                    -bet,
                    "game_lose",
                    f"Проигрыш в {game_type}"
                )
            
            # Получаем обновленный баланс
            user = await db.get_user(user_id)
            
            response = {
                **result,
                'new_balance': user['balance']
            }
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode())
            
        except Exception as e:
            self.send_error(500, str(e))
    
    async def play_game(self, game_type, bet, data):
        if game_type == 'flip':
            # Monkey Flip
            if random.random() < 0.015:  # 1.5% шанс проигрыша
                return {'win': False, 'multiplier': 0, 'amount': 0}
            
            win = random.random() < 0.49  # 49% шанс выигрыша
            multiplier = 2.0 if win else 0
            return {'win': win, 'multiplier': multiplier, 'amount': bet * multiplier}
        
        elif game_type == 'crash':
            # Banana Crash
            if random.random() < 0.6:  # 60% мгновенный краш
                return {'win': False, 'multiplier': 1.0, 'amount': 0}
            
            # 2% шанс на высокий множитель
            if random.random() < 0.02:
                multiplier = random.uniform(1.5, 5.0)
            else:
                multiplier = random.uniform(1.0, 1.1)
            
            # Имитация того, что игрок забирает вовремя в 80% случаев
            win = random.random() < 0.8
            return {'win': win, 'multiplier': multiplier if win else 1.0, 'amount': bet * multiplier if win else 0}
        
        elif game_type == 'slot':
            # Слот-машина
            win = random.randint(1, 27) <= 1  # 1/27 шанс
            multiplier = 20 if win else 0
            return {'win': win, 'multiplier': multiplier, 'amount': bet * multiplier}
    
    def parse_cookies(self):
        cookies = {}
        cookie_header = self.headers.get('Cookie', '')
        for cookie in cookie_header.split(';'):
            if '=' in cookie:
                key, value = cookie.strip().split('=', 1)
                cookies[key] = value
        return cookies
