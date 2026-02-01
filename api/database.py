import os
from supabase import create_client, Client
from datetime import datetime

class SupabaseDB:
    def __init__(self):
        url = os.environ.get("SUPABASE_URL")
        key = os.environ.get("SUPABASE_KEY")
        self.supabase: Client = create_client(url, key)
    
    async def get_user(self, user_id: int):
        response = self.supabase.table("users")\
            .select("*")\
            .eq("user_id", user_id)\
            .execute()
        return response.data[0] if response.data else None
    
    async def create_user(self, user_id: int, username: str, referrer_id: int = None):
        response = self.supabase.table("users")\
            .insert({
                "user_id": user_id,
                "username": username,
                "referrer_id": referrer_id,
                "created_at": int(datetime.now().timestamp())
            })\
            .execute()
        return response
    
    async def update_balance(self, user_id: int, amount: float):
        # Сначала получаем текущий баланс
        user = await self.get_user(user_id)
        if not user:
            return None
        
        new_balance = user['balance'] + amount
        
        response = self.supabase.table("users")\
            .update({"balance": new_balance})\
            .eq("user_id", user_id)\
            .execute()
        
        return response
    
    async def add_transaction(self, user_id: int, amount: float, type: str, description: str = ""):
        response = self.supabase.table("transactions")\
            .insert({
                "user_id": user_id,
                "amount": amount,
                "type": type,
                "description": description,
                "created_at": int(datetime.now().timestamp())
            })\
            .execute()
        return response
    
    async def get_sponsors(self):
        response = self.supabase.table("sponsors")\
            .select("*")\
            .execute()
        return response.data
    
    async def add_sponsor(self, channel_username: str, channel_id: str, channel_url: str):
        response = self.supabase.table("sponsors")\
            .insert({
                "channel_username": channel_username,
                "channel_id": channel_id,
                "channel_url": channel_url
            })\
            .execute()
        return response
    
    async def delete_sponsor(self, sponsor_id: int):
        response = self.supabase.table("sponsors")\
            .delete()\
            .eq("id", sponsor_id)\
            .execute()
        return response
    
    async def update_user_sponsor(self, user_id: int, sponsor_id: int, is_subscribed: bool):
        response = self.supabase.table("user_sponsors")\
            .upsert({
                "user_id": user_id,
                "sponsor_id": sponsor_id,
                "is_subscribed": is_subscribed
            })\
            .execute()
        return response
    
    async def get_user_sponsors_status(self, user_id: int):
        response = self.supabase.rpc('get_user_sponsors_status', {'p_user_id': user_id}).execute()
        return response.data
    
    async def get_user_referrals(self, user_id: int):
        # Все рефералы
        response = self.supabase.table("users")\
            .select("user_id, username, created_at")\
            .eq("referrer_id", user_id)\
            .execute()
        total_ref = response.data if response.data else []
        
        # Активные рефералы
        active_response = self.supabase.rpc('get_active_referrals', {'p_user_id': user_id}).execute()
        active_ref = active_response.data if active_response.data else []
        
        return len(total_ref), len(active_ref)
    
    async def create_withdrawal(self, user_id: int, amount: float):
        response = self.supabase.table("withdrawals")\
            .insert({
                "user_id": user_id,
                "amount": amount,
                "status": "pending",
                "created_at": int(datetime.now().timestamp())
            })\
            .execute()
        return response.data[0] if response.data else None
    
    async def get_withdrawals(self, status: str = None):
        query = self.supabase.table("withdrawals")\
            .select("*, users(username)")\
            .order("created_at", desc=True)
        
        if status:
            query = query.eq("status", status)
        
        response = query.execute()
        return response.data
    
    async def update_withdrawal_status(self, withdrawal_id: int, status: str):
        response = self.supabase.table("withdrawals")\
            .update({"status": status})\
            .eq("id", withdrawal_id)\
            .execute()
        return response
    
    async def get_all_users(self):
        response = self.supabase.table("users")\
            .select("*")\
            .order("created_at", desc=True)\
            .execute()
        return response.data
    
    async def get_stats(self):
        # Общее количество пользователей
        users_resp = self.supabase.table("users")\
            .select("user_id", count="exact")\
            .execute()
        
        # Общий баланс
        balance_resp = self.supabase.table("users")\
            .select("balance")\
            .execute()
        total_balance = sum(user['balance'] for user in balance_resp.data)
        
        # Общий доход (проигрыши в играх)
        income_resp = self.supabase.table("transactions")\
            .select("amount")\
            .in_("type", ["game_lose", "click"])\
            .execute()
        total_income = sum(txn['amount'] for txn in income_resp.data)
        
        return {
            'total_users': users_resp.count,
            'total_balance': total_balance,
            'total_income': total_income
        }

# Создаем глобальный экземпляр
db = SupabaseDB()
