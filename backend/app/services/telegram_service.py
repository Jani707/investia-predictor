import requests
from app.config import TELEGRAM_CONFIG

class TelegramService:
    @staticmethod
    def send_message(message: str) -> tuple[bool, str]:
        """
        Envía un mensaje a través del bot de Telegram.
        
        Args:
            message: El texto del mensaje a enviar.
            
        Returns:
            Tuple (success, detail): 
            - success: True si el envío fue exitoso, False si falló.
            - detail: Mensaje de éxito o descripción del error.
        """
        token = TELEGRAM_CONFIG["bot_token"]
        chat_id = TELEGRAM_CONFIG["chat_id"]
        
        if not token or not chat_id:
            msg = "⚠️ Telegram credentials not configured (Token or Chat ID missing)."
            print(msg)
            return False, msg
            
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": message,
            "parse_mode": "Markdown"
        }
        
        try:
            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()
            return True, "Message sent successfully"
        except Exception as e:
            error_msg = f"Telegram Error: {str(e)}"
            if hasattr(e, 'response') and e.response is not None:
                error_msg += f" | Response: {e.response.text}"
            print(f"❌ {error_msg}")
            return False, error_msg
