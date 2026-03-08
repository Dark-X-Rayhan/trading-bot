import requests
import time
import random
import threading
from flask import Flask
from datetime import datetime, timedelta, timezone

# --- Flask App Setup (ওয়েব ইউআরএল ও বাটনের জন্য) ---
app = Flask(__name__)
is_bot_running = True  # এখান থেকে বট অন-অফ করা যাবে

# --- Settings ---
TELEGRAM_TOKEN = "8354111202:AAEqFLMoJ7W7AlwpfHibZbpusiWbnOcl5Xc"
CHAT_ID = "-1003606163349"
SIGNAL_API_URL = "https://mrbeaxt.site/Qx/Qx.php?pair={pair}&count=1&format=json"

MARKETS = [
    "AUDNZD_otc", "AXP_otc", "BRLUSD_otc", "BTCUSD_otc", "EURNZD_otc",
    "EURSGD_otc", "INTC_otc", "JNJ_otc", "MCD_otc", "MSFT_otc",
    "NZDCAD_otc", "NZDCHF_otc", "NZDJPY_otc", "NZDUSD_otc", "PFE_otc",
    "USDBDT_otc", "USDCOP_otc", "USDDZD_otc", "USDEGP_otc", "USDIDR_otc",
    "USDINR_otc", "USDMXN_otc", "USDNGN_otc", "USDPKR_otc", "USDTRY_otc",
    "USDZAR_otc", "XAUUSD_otc"
]

pair_wait_until = {}

# --- Web Interface Logic ---
@app.route('/')
def home():
    status = "RUNNING 🟢" if is_bot_running else "STOPPED 🔴"
    return f"""
    <html>
        <head><title>DARK SIGNAL BOT CONTROL</title></head>
        <body style='text-align:center; font-family:sans-serif; padding-top:50px;'>
            <h1>DARK SIGNAL BOT</h1>
            <h2>Status: <span style='color: {"green" if is_bot_running else "red"}'>{status}</span></h2>
            <br>
            <a href='/toggle'><button style='padding:15px 30px; font-size:20px; cursor:pointer;'>ON/OFF Switch</button></a>
            <p>Current Time: {get_bd_time().strftime('%H:%M:%S')}</p>
            <p style='color:gray;'>Put this URL in UptimeRobot to keep the bot alive.</p>
        </body>
    </html>
    """

@app.route('/toggle')
def toggle():
    global is_bot_running
    is_bot_running = not is_bot_running
    return "<script>window.location.href='/';</script>"

# --- Your Original Trading Bot Logic ---
def get_bd_time():
    return datetime.now(timezone(timedelta(hours=6)))

def send_notification(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try: requests.get(url, params={"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}, timeout=10)
    except: pass

def fetch_api_signal(pair):
    try:
        url = SIGNAL_API_URL.format(pair=pair)
        res = requests.get(url, timeout=5).json()
        data = res.get('data', [{}])[0]
        
        action = data.get('signal') or data.get('action')
        if action: return action
        
        cp, op = float(data.get('close', 0)), float(data.get('open', 0))
        if cp > op: return "BUY"
        if cp < op: return "SELL"
    except: return None
    return None

def scan_markets():
    curr_ts = time.time()
    shuffled = MARKETS.copy()
    random.shuffle(shuffled)
    for pair in shuffled:
        if pair in pair_wait_until and curr_ts < pair_wait_until[pair]: continue
        action = fetch_api_signal(pair)
        if action and action.upper() in ["BUY", "SELL"]:
            now_bd = get_bd_time()
            trade_t = (now_bd + timedelta(seconds=12)).replace(second=0).strftime("%H:%M:%S")
            msg = f"{'🚀' if 'BUY' in action.upper() else '📉'} *API SIGNAL*\n💎 Pair: `{pair}`\n📊 Action: *{action.upper()}*\n⏰ Time: `{now_bd.strftime('%H:%M:%S')}`\n🎯 Trade: `{trade_t}`"
            send_notification(msg)
            pair_wait_until[pair] = curr_ts + 180
            return True
    return False

def bot_loop():
    while True:
        if is_bot_running:
            if get_bd_time().second == 48:
                scan_markets()
                time.sleep(60)
        time.sleep(1)

if __name__ == "__main__":
    # বটকে আলাদা থ্রেডে চালানো যাতে ওয়েবসাইটটিও সচল থাকে
    threading.Thread(target=bot_loop, daemon=True).start()
    # Render এর জন্য পোর্ট ১০০০০ ব্যবহার করা হয়েছে
    app.run(host='0.0.0.0', port=10000)
