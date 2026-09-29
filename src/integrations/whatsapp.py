import os
import json
from typing import Optional, Dict, Any

import requests


WHATSAPP_TOKEN = os.getenv('WHATSAPP_TOKEN')
WHATSAPP_PHONE_NUMBER_ID = os.getenv('WHATSAPP_PHONE_NUMBER_ID')
WHATSAPP_API_VERSION = os.getenv('WHATSAPP_API_VERSION', 'v18.0')
WHATSAPP_WEBHOOK_VERIFY_TOKEN = os.getenv('WHATSAPP_WEBHOOK_VERIFY_TOKEN', 'demo_verify_token')


def send_whatsapp_message(to_number: str, body: str) -> Dict[str, Any]:
    """Send a WhatsApp text message via the Meta WhatsApp Cloud API.

    Requires env vars:
      - WHATSAPP_TOKEN
      - WHATSAPP_PHONE_NUMBER_ID
    Example recipient: "918888888888" without '+' prefix or with phone id as per WhatsApp format.
    """
    if not WHATSAPP_TOKEN or not WHATSAPP_PHONE_NUMBER_ID:
        raise RuntimeError('WHATSAPP_TOKEN / WHATSAPP_PHONE_NUMBER_ID not set. Check your .env')

    url = f'https://graph.facebook.com/{WHATSAPP_API_VERSION}/{WHATSAPP_PHONE_NUMBER_ID}/messages'
    headers = {
        'Authorization': f'Bearer {WHATSAPP_TOKEN}',
        'Content-Type': 'application/json',
    }
    payload = {
        'messaging_product': 'whatsapp',
        'to': to_number,
        'type': 'text',
        'text': {'body': body},
    }
    response = requests.post(url, headers=headers, data=json.dumps(payload), timeout=30)
    response.raise_for_status()
    return response.json()


def verify_webhook_challenge(mode: str, token: str, challenge: str) -> Optional[str]:
    """Verify Meta webhook challenge as required by the WhatsApp Cloud API.

    Returns the challenge string if the token matches.
    """
    if mode == 'subscribe' and token == WHATSAPP_WEBHOOK_VERIFY_TOKEN:
        return challenge
    return None


def parse_incoming_whatsapp_event(payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Extract message text and sender information from a Meta webhook payload."""
    entries = payload.get('entry', [])
    for entry in entries:
        for change in entry.get('changes', []):
            value = change.get('value', {})
            messages = value.get('messages', [])
            if not messages:
                continue
            msg = messages[0]
            sender = msg.get('from')
            text = msg.get('text', {}).get('body')
            if sender and text:
                return {
                    'from': sender,
                    'text': text,
                    'message_id': msg.get('id'),
                    'type': msg.get('type'),
                }
    return None


def handle_whatsapp_reply(payload: Dict[str, Any]) -> Optional[str]:
    """A thin adapter for WhatsApp reply handling.

    Returns the text message body from the incoming WhatsApp payload, or None.
    """
    event = parse_incoming_whatsapp_event(payload)
    if event is None:
        return None
    return event.get('text')
