import requests
import time
import os

TG_BOT_TOKEN = os.environ.get("TG_BOT_TOKEN")
TG_CHAT_ID = os.environ.get("TG_CHAT_ID")

MIN_VOLUME = 5000000
OI_THRESHOLD = 8

def send(msg):
    url = f"https://api.telegram.org/bot{TG_BOT_TOKEN}/sendMessage"
    data = {
        "chat_id": TG_CHAT_ID,
        "text": msg
    }
    requests.post(url, data=data)

def get_symbols():
    r = requests.get("https://fapi.binance.com/fapi/v1/exchangeInfo")
    data = r.json()
    symbols = []
    for s in data["symbols"]:
        if s["quoteAsset"] == "USDT" and s["contractType"] == "PERPETUAL":
            symbols.append(s["symbol"])
    return symbols

def get_volume():
    r = requests.get("https://fapi.binance.com/fapi/v1/ticker/24hr")
    data = r.json()
    vol_map = {}
    for d in data:
        vol_map[d["symbol"]] = float(d["quoteVolume"])
    return vol_map

def get_funding():
    r = requests.get("https://fapi.binance.com/fapi/v1/premiumIndex")
    data = r.json()
    fr_map = {}
    for d in data:
        fr_map[d["symbol"]] = float(d["lastFundingRate"])
    return fr_map

def get_oi(symbol):
    url = "https://fapi.binance.com/futures/data/openInterestHist"
    params = {
        "symbol": symbol,
        "period": "15m",
        "limit": 16
    }
    r = requests.get(url, params=params)
    data = r.json()
    if len(data) < 4:
        return 0
    first = float(data[0]["sumOpenInterest"])
    last = float(data[-1]["sumOpenInterest"])
    if first == 0:
        return 0
    return (last - first) / first * 100

def scan():
    print("Scanning...")
    symbols = get_symbols()
    volumes = get_volume()
    funding = get_funding()

    signals = []

    for sym in symbols:
        if sym not in volumes:
            continue
        if volumes[sym] < MIN_VOLUME:
            continue
        if sym not in funding:
            continue
        if funding[sym] >= 0:
            continue

        oi_change = get_oi(sym)
        if oi_change > OI_THRESHOLD:
            signals.append((sym, funding[sym], oi_change))

    if signals:
        msg = "🚀 抓妖信号:\n\n"
        for s in signals:
            msg += f"{s[0]} | FR: {s[1]:.4f} | OI: {s[2]:.2f}%\n"
        send(msg)
        print("Signal sent")
    else:
        print("No signal")

while True:
    try:
        scan()
    except Exception as e:
        print("Error:", e)
    time.sleep(300)
