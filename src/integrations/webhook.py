"""Simple Flask webhook that accepts inbound WhatsApp messages.

This is a secure starting point for two-way WhatsApp interactions. In production, keep this behind
TLS and only accept messages from your verified WhatsApp Business account.
"""

import os
from typing import Any, Dict

from flask import Flask, request, Response

from src.integrations.whatsapp import verify_webhook_challenge, handle_whatsapp_reply

app = Flask(__name__)


def create_whatsapp_webhook() -> Flask:
    @app.route('/whatsapp/webhook', methods=['GET', 'POST'])
    def webhook():
        if request.method == 'GET':
            mode = request.args.get('hub.mode')
            token = request.args.get('hub.verify_token')
            challenge = request.args.get('hub.challenge')
            matched = verify_webhook_challenge(mode, token, challenge)
            if matched:
                return Response(str(matched), mimetype='text/plain')
            return Response('Forbidden', status=403)

        if request.method == 'POST':
            payload = request.get_json(silent=True) or {}
            text = handle_whatsapp_reply(payload)
            if text:
                print('WhatsApp inbound message:', text)
                # This is where you route to your dialog manager / voice confirmation system.
            return Response('OK', status=200)

    return app


if __name__ == '__main__':
    port = int(os.getenv('WHATSAPP_WEBHOOK_PORT', '5000'))
    create_whatsapp_webhook().run(host='0.0.0.0', port=port)
