"""Demo script to send a test WhatsApp message.

Requires env vars:
  - WHATSAPP_TOKEN
  - WHATSAPP_PHONE_NUMBER_ID
  - USER_WHATSAPP_NUMBER (without '+' prefix, e.g. 919876543210)
"""
import os
from src.integrations.whatsapp import send_whatsapp_message


if __name__ == '__main__':
    to_number = os.getenv('USER_WHATSAPP_NUMBER')
    if not to_number:
        raise SystemExit('Set USER_WHATSAPP_NUMBER in env before running this demo.')
    result = send_whatsapp_message(to_number, 'Hello from your AI trading agent. WhatsApp integration is working.')
    print(result)
