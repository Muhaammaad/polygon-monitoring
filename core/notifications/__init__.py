import os
import logging
import asyncio
from pathlib import Path
from typing import Optional, Dict, Tuple
from ..config import get_config
from telegram import Bot
from twilio.rest import Client

logger = logging.getLogger(__name__)


# NotificationManager handles sending notifications via Telegram and Twilio SMS
class NotificationManager:
    # Initialize with config and environment variables(this class is fully environment driven, not hadcoded)
    def __init__(self):
        self.config = get_config()                 # load global config
        self.templates_dir = Path(__file__).parent 
        self.telegram_token = os.getenv('TELEGRAM_BOT_TOKEN', '') # load from env
        self.twilio_sid = os.getenv('TWILIO_ACCOUNT_SID', '')
        self.twilio_token = os.getenv('TWILIO_AUTH_TOKEN', '')
        self.twilio_from = os.getenv('TWILIO_FROM_NUMBER', '')
        self.app_env = os.getenv('APP_ENV', 'production')
        self.it_channel = os.getenv('TELEGRAM_IT_CHANNEL_ID', '')
        # Global notification behavior settings
        self.global_sms_fallback_enabled = os.getenv('ENABLE_SMS_FALLBACK', 'true').lower() == 'true'
        self.telegram_retry_count = int(os.getenv('TELEGRAM_RETRY_COUNT', '1'))

    
    # Load template file for given channel, language, and warning type
    def _load_template(self, channel: str, lang: str, warning_type: str) -> Optional[str]:
        base = 'templates/telegram' if channel == 'telegram' else 'templates/sms'
        tpl_path = self.templates_dir / base / lang / f"{warning_type}.txt"
        if tpl_path.exists():
            return tpl_path.read_text(encoding='utf-8')
        return None
    

    # Resolve Telegram language with user override if supported
    def _resolve_telegram_language(self, user_lang: Optional[str], city_config) -> Tuple[str, str]:
        # Telegram: user override only if present and supported
        supported = set(city_config.language.supported)
        if user_lang:
            user_lang = str(user_lang).upper()
            if user_lang in supported:
                return user_lang, "user_override"
            else:
                logger.info({
                    "event": "invalid_user_language_ignored",
                    "channel": "telegram",
                    "provided_language": user_lang,
                    "city_default": city_config.language.default
                })
        return city_config.language.default, "city_default"
    

    # Resolve SMS language (no user override, always city default)
    def _resolve_sms_language(self, city_config) -> str:
        return city_config.language.default

    # Send notification to user via Telegram and SMS fallback
    async def send(self, user: Dict, warning_type: str, city_config) -> bool:
        """Send notification: Telegram first, Twilio SMS fallback if enabled.

        Returns True if a notification was successfully sent.
        """
        # Telegram resolution
        tg_lang, tg_source = self._resolve_telegram_language(user.get('telegram_language'), city_config)
        logger.info({
            "event": "telegram_language_resolved",
            "user_id": user.get('uuid'),
            "city": city_config.city_code,
            "resolved_language": tg_lang,
            "source": tg_source
        })
        tg_tpl = self._load_template('telegram', tg_lang, warning_type)

        # SMS resolution
        sms_lang = self._resolve_sms_language(city_config)
        sms_tpl = self._load_template('sms', sms_lang, warning_type)

        # assemble message by simple formatting
        context = user.copy()
        context.update({
            'first_name': user.get('first_name', ''),
            'warning': warning_type,
        })

        # Try Telegram
        # Handle both dict and Pydantic model
        notifications = city_config.notifications
        if isinstance(notifications, dict):
            tg_config = notifications.get('telegram', {})
            tg_enabled = tg_config.get('enabled', False) if isinstance(tg_config, dict) else tg_config
        else:
            tg_config = getattr(notifications, 'telegram', {})
            tg_enabled = getattr(tg_config, 'enabled', tg_config) if hasattr(tg_config, 'enabled') else tg_config
        
        if tg_enabled and user.get('telegram_id'):
            if tg_tpl is None:
                # fallback to city language template if missing (spec: Telegram fallback to city language)
                tg_tpl = self._load_template('telegram', city_config.language.default, warning_type)

            if tg_tpl:
                message = tg_tpl.format(**context)
                if self.app_env == 'test':
                    logger.info(f"[TEST] Telegram message to {user.get('telegram_id')}: {message}")
                    return True
                bot = Bot(token=self.telegram_token)
                try:
                    await bot.send_message(chat_id=user.get('telegram_id'), text=message)
                    logger.info(f"Telegram sent to {user.get('telegram_id')}")
                    return True
                except Exception as e:
                    logger.error({
                        "event": "telegram_send_failed",
                        "user_id": user.get('uuid'),
                        "city": city_config.city_code,
                        "error": str(e)
                    })
                    # Retry based on configured retry count
                    for retry_attempt in range(self.telegram_retry_count):
                        try:
                            await bot.send_message(chat_id=user.get('telegram_id'), text=message)
                            logger.info(f"Telegram sent on retry {retry_attempt + 1} to {user.get('telegram_id')}")
                            return True
                        except Exception as e2:
                            logger.error({
                                "event": f"telegram_retry_{retry_attempt + 1}_failed",
                                "user_id": user.get('uuid'),
                                "city": city_config.city_code,
                                "error": str(e2)
                            })
                    
                    # All retries failed - alert IT channel if available
                    if self.it_channel:
                        try:
                            await bot.send_message(chat_id=self.it_channel, text=f"Notification failure for {user.get('uuid')}: {warning_type}")
                        except Exception:
                            pass

        # Telegram failed or not available => SMS fallback
        # Check global SMS fallback setting first (ENV override)
        if not self.global_sms_fallback_enabled:
            logger.info({
                "event": "sms_fallback_disabled_globally",
                "user_id": user.get('uuid'),
                "city": city_config.city_code
            })
            return False
        
        # Handle both dict and Pydantic model
        notifications = city_config.notifications
        if isinstance(notifications, dict):
            sms_config = notifications.get('sms_fallback', {})
            sms_enabled = sms_config.get('enabled', False) if isinstance(sms_config, dict) else sms_config
        else:
            sms_config = getattr(notifications, 'sms_fallback', {})
            sms_enabled = getattr(sms_config, 'enabled', sms_config) if hasattr(sms_config, 'enabled') else sms_config
        
        if sms_enabled:
            if sms_tpl is None:
                # per spec: missing SMS template for city language -> hard error + log
                logger.error({
                    "event": "missing_sms_template",
                    "city": city_config.city_code,
                    "language": sms_lang
                })
                return False

            # phone format: prefix + phone
            prefix = user.get('prefix', '')
            phone = user.get('phone', '')
            if not phone:
                logger.error(f"No phone for user {user.get('uuid')}")
                return False

            number = f"{phone.lstrip('0')}"
            message = sms_tpl.format(**context)

            if self.app_env == 'test':
                logger.info(f"[TEST] SMS to {number}: {message}")
                return True

            sent = self._send_twilio_sms(number, message, user.get('uuid'), city_config.city_code)
            return sent

        return False

    def send_sync(self, user: Dict, warning_type: str, city_config) -> bool:
        """Synchronous wrapper for send() method.
        
        Runs the async send() method using asyncio.run().
        Use this when you can't use await directly (e.g., synchronous code).
        """
        try:
            return asyncio.run(self.send(user, warning_type, city_config))
        except RuntimeError as e:
            # If event loop is already running, run in executor
            if "asyncio.run() cannot be called from a running event loop" in str(e):
                import concurrent.futures
                loop = asyncio.get_event_loop()
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, self.send(user, warning_type, city_config))
                    return future.result()
            raise

    def _send_twilio_sms(self, to_number: str, body: str, user_id: Optional[str], city_code: str) -> bool:
        """Send a single SMS via Twilio using environment-driven credentials."""

        if not (self.twilio_sid and self.twilio_token and self.twilio_from):
            logger.error({
                "event": "twilio_missing_credentials",
                "user_id": user_id,
                "city": city_code,
                "missing": {
                    "sid": bool(self.twilio_sid),
                    "token": bool(self.twilio_token),
                    "from": bool(self.twilio_from)
                }
            })
            return False

        try:
            client = Client(self.twilio_sid, self.twilio_token)
            client.messages.create(
                body=body,
                from_=self.twilio_from,
                to=to_number,
            )
            logger.info(f"SMS sent to {to_number}")
            return True
        except Exception as e:
            logger.error({
                "event": "sms_send_failed",
                "user_id": user_id,
                "city": city_code,
                "error": str(e)
            })
            return False


# helper instance
# global notification manager instance
notification_manager = NotificationManager()



def get_notification_manager() -> NotificationManager:
    return notification_manager
