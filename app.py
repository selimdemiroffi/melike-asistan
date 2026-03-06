import os
import requests
from flask import Flask, request
from google import genai
from google.genai import types

app = Flask(__name__)

WA_TOKEN = os.getenv("WA_TOKEN")
GEMINI_KEY = os.getenv("GEMINI_KEY")
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN", "melike_asistan_2026")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID", "1052737427912953")

client = genai.Client(
    api_key=GEMINI_KEY,
    http_options=types.HttpOptions(api_version="v1"),
)

MODEL_ID = "gemini-2.5-flash"

MELIKE_PROMPT = (
    "Senin adın Melike. Selim Bey'in asistanısın. "
    "Profesyonel ve samimisin. "
    "Kilo verme uzmanısın. "
    "Çalışma saatlerin Pazar hariç 19:00-23:00 arasıdır. "
    "Kısa ve net cevaplar ver."
)


@app.route("/", methods=["GET"])
def home():
    return "Servis aktif", 200


@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    print(f"Webhook çağrıldı. Method={request.method}")

    if request.method == "GET":
        token = request.args.get("hub.verify_token")
        challenge = request.args.get("hub.challenge")

        if token == VERIFY_TOKEN:
            return challenge, 200
        return "Doğrulama hatası", 403

    data = request.get_json(silent=True) or {}
    print(f"Gelen POST verisi: {data}")

    try:
        value = data["entry"][0]["changes"][0]["value"]

        if "messages" not in value:
            print("messages alanı yok.")
            return "OK", 200

        message = value["messages"][0]

        if message.get("type") != "text":
            print("Text olmayan mesaj geldi.")
            return "OK", 200

        sender_id = message["from"]
        user_text = message["text"]["body"].strip()

        if not user_text:
            return "OK", 200

        full_prompt = (
            f"{MELIKE_PROMPT}\n\n"
            f"Kullanıcının mesajı: {user_text}"
        )

        response = client.models.generate_content(
            model=MODEL_ID,
            contents=full_prompt,
            config=types.GenerateContentConfig(
                temperature=0.7,
                max_output_tokens=300,
            ),
        )

        reply_text = (response.text or "").strip()

        if not reply_text:
            reply_text = "Şu an cevap oluşturamadım, lütfen tekrar yazar mısınız?"

        print(f"Gemini cevabı: {reply_text}")
        send_whatsapp_message(sender_id, reply_text)

    except Exception as e:
        print(f"Hata: {e}")

    return "OK", 200


def send_whatsapp_message(to, text):
    url = f"https://graph.facebook.com/v18.0/{PHONE_NUMBER_ID}/messages"

    headers = {
        "Authorization": f"Bearer {WA_TOKEN}",
        "Content-Type": "application/json",
    }

    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": text},
    }

    print(f"WhatsApp'a gönderiliyor: {payload}")

    try:
        resp = requests.post(url, json=payload, headers=headers, timeout=30)
        print(f"WhatsApp API durum kodu: {resp.status_code}")
        print(f"WhatsApp API cevabı: {resp.text}")
    except Exception as e:
        print(f"WhatsApp isteği başarısız: {e}")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
