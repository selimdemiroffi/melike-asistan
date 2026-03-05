import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

# --- AYARLAR ---
# Bunları Render'a yüklediğimizde panelden gireceğiz, şimdilik böyle kalsın.
WA_TOKEN = os.environ.get("WA_TOKEN") 
GEMINI_KEY = os.environ.get("GEMINI_KEY")
PHONE_NUMBER_ID = "1052737427912953"
VERIFY_TOKEN = "melike_asistan_2026" # Bunu Meta paneline yazacağız

SISTEM_TALIMATI = """Adın Melike. Selim Bey'in asistanısın. Samimi ama profesyonelsin. 
Pazar hariç 19:00-23:00 arası çalışıyoruz. Kilo verme ve bütçe dostu programlarda uzmanız."""

def gemini_cevap(soru):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_KEY}"
    payload = {"contents": [{"parts": [{"text": f"{SISTEM_TALIMATI}\n\nMüşteri: {soru}\nMelike:"}]}]}
    try:
        r = requests.post(url, json=payload)
        return r.json()['candidates'][0]['content']['parts'][0]['text']
    except Exception as e:
        print(f"HATA OLUŞTU: {e}") # Bu satır hatayı Render loglarına yazdıracak
        return "Selim Bey şuan meşgul, en kısa sürede size dönüş yapacaktır."

@app.route("/webhook", methods=["GET"])
def verify():
    if request.args.get("hub.verify_token") == VERIFY_TOKEN:
        return request.args.get("hub.challenge")
    return "Doğrulama Başarısız", 403

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json
    try:
        msg = data['entry'][0]['changes'][0]['value']['messages'][0]
        no = msg['from']
        txt = msg['text']['body']
        
        yanit = gemini_cevap(txt)
        
        # WhatsApp'a gönder
        url = f"https://graph.facebook.com/v18.0/{PHONE_NUMBER_ID}/messages"
        headers = {"Authorization": f"Bearer {WA_TOKEN}"}
        requests.post(url, json={"messaging_product": "whatsapp", "to": no, "text": {"body": yanit}}, headers=headers)
    except:
        pass
    return "OK", 200

if __name__ == "__main__":

    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
