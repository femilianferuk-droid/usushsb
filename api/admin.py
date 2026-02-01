from http.server import BaseHTTPRequestHandler
import json
from urllib.parse import parse_qs
from api.database import db

ADMIN_ID = 7973988177

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        # Проверка админ прав
        cookies = self.parse_cookies()
        user_id = cookies.get('user_id')
        
        if not user_id or int(user_id) != ADMIN_ID:
            self.send_error(403, "Access denied")
            return
        
        # Получаем статистику
        stats = await db.get_stats()
        sponsors = await db.get_sponsors()
        withdrawals = await db.get_withdrawals()
        
        response = {
            'stats': stats,
            'sponsors': sponsors,
            'withdrawals': withdrawals
        }
        
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(response).encode())
    
    def do_POST(self):
        cookies = self.parse_cookies()
        user_id = cookies.get('user_id')
        
        if not user_id or int(user_id) != ADMIN_ID:
            self.send_error(403, "Access denied")
            return
        
        content_length = int(self.headers['Content-Length'])
        post_data = json.loads(self.rfile.read(content_length))
        
        action = post_data.get('action')
        
        if action == 'add_sponsor':
            result = await db.add_sponsor(
                post_data['channel_username'],
                post_data['channel_id'],
                post_data['channel_url']
            )
            response = {'success': True, 'data': result}
        
        elif action == 'delete_sponsor':
            result = await db.delete_sponsor(int(post_data['sponsor_id']))
            response = {'success': True, 'data': result}
        
        elif action == 'update_withdrawal':
            result = await db.update_withdrawal_status(
                int(post_data['withdrawal_id']),
                post_data['status']
            )
            response = {'success': True, 'data': result}
        
        else:
            response = {'success': False, 'error': 'Unknown action'}
        
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(response).encode())
    
    def parse_cookies(self):
        cookies = {}
        cookie_header = self.headers.get('Cookie', '')
        for cookie in cookie_header.split(';'):
            if '=' in cookie:
                key, value = cookie.strip().split('=', 1)
                cookies[key] = value
        return cookies
