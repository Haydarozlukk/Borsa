import yfinance as yf
import pandas as pd
import time
from datetime import datetime
import requests

# === Telegram ayarları ===
TELEGRAM_TOKEN = "7715979474:AAGbCq191VoX0xM69LqkUrgaI5sRRWj6JBg"
CHAT_ID = "895089486"

def send_telegram(message: str):
    if not TELEGRAM_TOKEN or not CHAT_ID:
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message}
    try:
        requests.post(url, data=payload, timeout=10)
    except Exception as e:
        print("Telegram gönderim hatası:", e)

# === İzlenecek semboller (örnek) ===
symbols = [
    "AKBNK.IS", "ALARK.IS", "ASELS.IS", "BIMAS.IS", "DOHOL.IS", "EKGYO.IS",
    "EREGL.IS", "FROTO.IS", "GARAN.IS", "HALKB.IS", "HEKTS.IS", "ISCTR.IS",
    "KCHOL.IS", "KOZAA.IS", "KOZAL.IS", "ODAS.IS", "PETKM.IS", "PGSUS.IS",
    "SAHOL.IS", "SISE.IS", "SOKM.IS", "TAVHL.IS", "TCELL.IS", "THYAO.IS",
    "TKFEN.IS", "TOASO.IS", "TRKCM.IS", "TTKOM.IS", "TUPRS.IS", "VAKBN.IS",
    "YKBNK.IS", "ZOREN.IS", "AGHOL.IS", "AKSA.IS", "ALGYO.IS", "ARCLK.IS",
    "ASELS.IS", "ASUZU.IS", "AYDEM.IS", "BANVT.IS", "BRISA.IS", "CEMTS.IS",
    "CIMSA.IS", "CMENT.IS", "DOAS.IS", "ENJSA.IS", "ENKAI.IS", "GESAN.IS",
    "GSDHO.IS", "GUBRF.IS", "KRDMD.IS", "KONTR.IS", "LOGO.IS", "MAVI.IS",
    "MGROS.IS", "OYAKC.IS", "QNBFB.IS", "SASA.IS", "SMRTG.IS", "TATGD.IS",
    "TMSN.IS", "TSKB.IS", "TTRAK.IS", "ULKER.IS", "VESTL.IS", "YATAS.IS",
    "YKSLN.IS", "ISDMR.IS", "SOKM.IS", "KONYA.IS", "KERVT.IS", "ALBRK.IS",
    "VAKKO.IS", "HUBVC.IS", "IPEKE.IS", "PRKME.IS", "SELEC.IS", "KARSN.IS",
    "KLMSN.IS", "BRSAN.IS", "KRDMB.IS", "NUGYO.IS", "ODINE.IS", "GWIND.IS",
    "QUAGR.IS", "PENTA.IS", "OZKGY.IS", "GEDIK.IS", "AKFGY.IS", "ISGYO.IS",
    "HALKS.IS", "HDFGS.IS", "AGESA.IS", "ANSGR.IS", "TURSG.IS", "VERTU.IS",
    "CANTE.IS", "EUPWR.IS", "FENER.IS", "SNGYO.IS"
]

# === EMA ve MACD hesaplama ===
def ema(series, period):
    return series.ewm(span=period, adjust=False).mean()

def macd(series, fast=12, slow=26, signal=9):
    fast_ema = ema(series, fast)
    slow_ema = ema(series, slow)
    macd_line = fast_ema - slow_ema
    signal_line = ema(macd_line, signal)
    return macd_line, signal_line

# === Sinyal kontrol ===
def check_signals(df):
    df["EMA14"] = ema(df["Close"], 14)
    df["EMA34"] = ema(df["Close"], 34)
    df["EMA_cross"] = (df["EMA14"] > df["EMA34"]) & (df["EMA14"].shift(1) <= df["EMA34"].shift(1))

    macd_line, signal_line = macd(df["Close"])
    df["MACD"] = macd_line
    df["Signal"] = signal_line
    df["MACD_cross"] = (df["MACD"] > df["Signal"]) & (df["MACD"].shift(1) <= df["Signal"].shift(1))

    return df.iloc[-1][["EMA_cross", "MACD_cross"]]

# === Sürekli tarama ===
def run_scanner():
    print(f"✅ {len(symbols)} sembol izleniyor (1 saatlik periyot).")
    while True:
        print(f"\n⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} için tarama...")
        try:
            # 1 saatlik mum verisi indir
            data = yf.download(symbols, period="1mo", interval="1h", group_by="ticker", progress=False)
        except Exception as e:
            print("Veri indirilemedi:", e)
            time.sleep(60)
            continue

        results = []
        for symbol in symbols:
            try:
                df = data[symbol]
                if df.empty:
                    continue
                signals = check_signals(df)
                if signals["EMA_cross"] or signals["MACD_cross"]:
                    results.append(f"{symbol} → EMA:{signals['EMA_cross']} | MACD:{signals['MACD_cross']}")
            except Exception as e:
                print(f"{symbol} işlenemedi: {e}")

        if results:
            message = "📊 1 Saatlik sinyal gelen semboller:\n" + "\n".join(results)
            print(message)
            send_telegram(message)
        else:
            print("⚠️ Bu saatlik mumda sinyal yok.")

        # 1 saatlik mum kapanışını bekle
        time.sleep(3600)

# === Başlat ===
if __name__ == "__main__":
    run_scanner()
