
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import math, statistics, urllib.request, json as j

app = FastAPI(title="Gold & FX Intelligence")
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

SYMBOLS = {
    "XAUUSD":"XAUUSD=X", "EURUSD":"EURUSD=X", "GBPUSD":"GBPUSD=X",
    "USDJPY":"JPY=X", "USDCHF":"CHF=X", "AUDUSD":"AUDUSD=X",
    "NZDUSD":"NZDUSD=X", "USDCAD":"CAD=X", "EURJPY":"EURJPY=X",
    "GBPJPY":"GBPJPY=X", "EURGBP":"EURGBP=X"
}
TF = {"M5":"5m","M15":"15m","H1":"60m","H4":"1h","D1":"1d","W1":"1wk","MN":"1mo"}

# These are editable model inputs. In production, replace them with licensed
# macro/news feeds (Fed/ECB/BoE/BoJ/etc., CPI, NFP, yields, positioning, news).
DEFAULT_MACRO = {
    "USD":{"policy":0,"inflation":0,"growth":0,"employment":0,"yields":0,"risk":0},
    "EUR":{"policy":0,"inflation":0,"growth":0,"employment":0,"yields":0,"risk":0},
    "GBP":{"policy":0,"inflation":0,"growth":0,"employment":0,"yields":0,"risk":0},
    "JPY":{"policy":0,"inflation":0,"growth":0,"employment":0,"yields":0,"risk":0},
    "CHF":{"policy":0,"inflation":0,"growth":0,"employment":0,"yields":0,"risk":0},
    "AUD":{"policy":0,"inflation":0,"growth":0,"employment":0,"yields":0,"risk":0},
    "NZD":{"policy":0,"inflation":0,"growth":0,"employment":0,"yields":0,"risk":0},
    "CAD":{"policy":0,"inflation":0,"growth":0,"employment":0,"yields":0,"risk":0},
}

def yahoo(symbol, interval, range_="1mo"):
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{urllib.parse.quote(symbol, safe='')}?interval={interval}&range={range_}"
    req = urllib.request.Request(url, headers={"User-Agent":"Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=8) as r:
        return j.loads(r.read())

import urllib.parse

def closes(symbol, interval):
    try:
        d = yahoo(symbol, interval)
        res = d["chart"]["result"][0]
        q = res["indicators"]["quote"][0]
        return [float(x) for x in q.get("close", []) if x is not None]
    except Exception:
        return []

def ema(vals, n):
    if len(vals) < n: return vals[-1] if vals else 0
    k = 2/(n+1); e = sum(vals[:n])/n
    for x in vals[n:]: e = x*k + e*(1-k)
    return e

def rsi(vals, n=14):
    if len(vals) < n+1: return 50
    gains=[]; losses=[]
    for a,b in zip(vals[-n-1:-1], vals[-n:]):
        d=b-a; gains.append(max(d,0)); losses.append(max(-d,0))
    ag=sum(gains)/n; al=sum(losses)/n
    if al == 0: return 100
    return 100 - 100/(1+ag/al)

def macd_hist(vals):
    if len(vals) < 35: return 0
    m = ema(vals,12)-ema(vals,26)
    signal = ema([ema(vals[:i],12)-ema(vals[:i],26) for i in range(26,len(vals)+1)],9)
    return m-signal

def technical_score(vals):
    if len(vals)<20: return 0, {"rsi":50,"trend":0,"macd":0}
    price=vals[-1]; e20=ema(vals,20); e50=ema(vals,50) if len(vals)>=50 else ema(vals, min(40,len(vals)))
    trend=max(-1,min(1,(e20-e50)/(price*0.01))) if price else 0
    rv=rsi(vals)
    r=max(-1,min(1,(rv-50)/25))
    mh=macd_hist(vals)
    m=max(-1,min(1,mh/(price*0.002))) if price else 0
    return 100*(0.45*trend+0.25*r+0.30*m), {"rsi":round(rv,1),"trend":round(trend,2),"macd":round(m,2)}

def currency(symbol):
    return symbol[:3] if symbol not in ("XAUUSD",) else "XAU"

def fundamental_pair(symbol):
    # Demo-neutral until macro feed is connected.
    if symbol=="XAUUSD":
        return 50, ["Macro feed not connected", "Gold model ready for yields/DXY/Fed inputs"]
    base, quote = symbol[:3], symbol[3:]
    b=DEFAULT_MACRO.get(base,{}); q=DEFAULT_MACRO.get(quote,{})
    def avg(x): return sum(x.values())/len(x) if x else 0
    score=50 + 20*(avg(b)-avg(q))
    return max(0,min(100,score)), ["Currency macro inputs currently neutral"]

def analyze(symbol):
    sym=SYMBOLS[symbol]
    out={}
    weights={"MN":0.22,"W1":0.20,"D1":0.23,"H4":0.17,"H1":0.10,"M15":0.08}
    weighted=0; used=0
    for tf, interval in TF.items():
        if tf not in weights: continue
        vals=closes(sym,interval)
        ts, meta=technical_score(vals)
        if vals:
            out[tf]={"score":round(ts+50,1),"price":round(vals[-1],6),"rsi":meta["rsi"],"trend":meta["trend"],"macd":meta["macd"]}
            weighted += (ts+50)*weights[tf]; used += weights[tf]
        else:
            out[tf]={"score":50,"price":None,"rsi":50,"trend":0,"macd":0}
    tech=weighted/used if used else 50
    fund, reasons=fundamental_pair(symbol)
    overall=0.55*tech+0.45*fund
    if overall>=62: bias="BUY"
    elif overall<=38: bias="SELL"
    else: bias="WAIT"
    confidence=abs(overall-50)*2
    return {"symbol":symbol,"price":next((v["price"] for v in out.values() if v["price"] is not None),None),
            "bias":bias,"score":round(overall,1),"confidence":round(confidence,1),
            "fundamental":round(fund,1),"technical":round(tech,1),"timeframes":out,
            "reasons":reasons}

@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request":request,"symbols":list(SYMBOLS)})

@app.get("/api/analyze/{symbol}")
def api_analyze(symbol: str):
    symbol=symbol.upper()
    if symbol not in SYMBOLS: return JSONResponse({"error":"Unknown symbol"}, status_code=404)
    try: return analyze(symbol)
    except Exception as e: return {"symbol":symbol,"bias":"WAIT","score":50,"confidence":0,"error":str(e)}

@app.get("/api/scan")
def scan():
    return [analyze(s) for s in SYMBOLS]
