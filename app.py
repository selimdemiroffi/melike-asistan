import os
from flask import Flask, request
from google import genai # Yeni kütüphane
import requests

app = Flask(__name__)

# Değişkenler
WA_TOKEN = os.getenv("WA_TOKEN")
GEMINI_KEY = os.getenv("GEMINI_KEY")
VERIFY_TOKEN = "melike_asistan_2026"
PHONE_NUMBER_ID = "1052737427912953"

# Yeni Gemini Yapılandırması
client = genai.Client(api_key=GEMINI_KEY)
MODEL_ID = "gemini-1.5-flash"

MELIKE_PROMPT = (
    "Senin adın Melike. Selim Bey'in asistanısın. Profesyonel ve samimisin. "
    "Kilo verme uzmanısın. Çalışma saatlerin Pazar hariç 19:00-23:00 arasıdır. "
    "Kısa ve net cevaplar ver."
)

@app.route('/webhook', methods=['GET', 'POST'])
def webhook():
    if request.method == 'GET':
        if request.args.get('hub.verify_token') == VERIFY_TOKEN:
            return request.args.get('hub.challenge'), 200
        return 'Hata', 403

    if request.method == 'POST':
        data = request.json
        try:
            if 'messages' in data['entry'][0]['changes'][0]['value']:
                message = data['entry'][0]['changes'][0]['value']['messages'][0]
                sender_id = message['from']
                user_text = message['text']['body']

                # Yeni kütüphane ile cevap oluşturma
                response = client.models.generate_content(
                    model=MODEL_ID,
                    config={'system_instruction': MELIKE_PROMPT},
                    contents=user_text
                )
                
                send_whatsapp_message(sender_id, response.text)
        except Exception as e:
            print(f"Hata: {e}")
        return 'OK', 200

def send_whatsapp_message(to, text):
    url = f"https://graph.facebook.com/v18.0/{PHONE_NUMBER_ID}/messages"
    headers = {"Authorization": f"Bearer {WA_TOKEN}", "Content-Type": "application/json"}
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": text}
    }
    requests.post(url, json=payload, headers=headers)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
