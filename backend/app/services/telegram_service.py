import requests
from app.config import TELEGRAM_CONFIG

class TelegramService:
    @staticmethod
    def send_message(message: str) -> bool:
        """
        Envía un mensaje a través del bot de Telegram.
        
        Args:
            message: El texto del mensaje a enviar.
            
        Returns:
            True si el envío fue exitoso, False si falló.
        """
        token = TELEGRAM_CONFIG["bot_token"]
        chat_id = TELEGRAM_CONFIG["chat_id"]
        
        if not token or not chat_id:
            print("⚠️ Telegram credentials not configured.")
            return False
            
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": message,
            "parse_mode": "Markdown"
        }
        
        try:
            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()
            print(f"✅ Telegram message sent to {chat_id}")
            return True
        except Exception as e:
            print(f"❌ Error sending Telegram message: {e}")
            return False
