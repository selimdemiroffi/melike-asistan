import os
from flask import Flask, request, jsonify
import google.generativeai as genai
import requests

app = Flask(__name__)

# Environment Variables
WA_TOKEN = os.getenv("WA_TOKEN")
GEMINI_KEY = os.getenv("GEMINI_KEY")
VERIFY_TOKEN = "melike_asistan_2026"
PHONE_NUMBER_ID = "1052737427912953" # Burayı başarıyla eklemişsin

# Gemini Yapılandırması - GÜNCELLENDİ
genai.configure(api_key=GEMINI_KEY)

# Bazı kütüphane versiyonlarında 'models/' ön eki şarttır
try:
    model = genai.GenerativeModel('gemini-1.5-flash')
except:
    model = genai.GenerativeModel('models/gemini-1.5-flash')

# Melike'nin Karakter Tanımı
MELIKE_PROMPT = (
    "Senin adın Melike. Selim Bey'in asistanısın. Profesyonel, samimi ve güven verici bir tavrın var. "
    "Kilo verme uzmanısın. Çalışma saatlerin Pazar hariç her gün 19:00 - 23:00 arasıdır. "
    "Sorulara bu kimlikle, kısa ve net cevaplar ver."
)

@app.route('/webhook', methods=['GET', 'POST'])
def webhook():
    if request.method == 'GET':
        mode = request.args.get('hub.mode')
        token = request.args.get('hub.verify_token')
        challenge = request.args.get('hub.challenge')
        if mode == 'subscribe' and token == VERIFY_TOKEN:
            return challenge, 200
        return 'Hatalı Token', 403

    if request.method == 'POST':
        data = request.json
        try:
            # WhatsApp'tan mesaj geldi mi kontrolü
            if 'messages' in data['entry'][0]['changes'][0]['value']:
                message = data['entry'][0]['changes'][0]['value']['messages'][0]
                sender_id = message['from']
                user_text = message['text']['body']

                # Gemini'ye sor ve cevabı al
                full_prompt = f"{MELIKE_PROMPT}\n\nKullanıcı: {user_text}\nMelike:"
                response = model.generate_content(full_prompt)
                ai_reply = response.text.strip() # .strip() ile gereksiz boşlukları temizledik

                # WhatsApp üzerinden cevap gönder
                send_whatsapp_message(sender_id, ai_reply)

        except Exception as e:
            print(f"Hata oluştu: {e}")
        
        return 'OK', 200

def send_whatsapp_message(to, text):
    # Değişkeni burada F-string içinde kullandık:
    url = f"https://graph.facebook.com/v18.0/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {WA_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": text}
    }
    response = requests.post(url, json=payload, headers=headers)
    print(f"WhatsApp API Yanıtı: {response.status_code} - {response.text}")

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

