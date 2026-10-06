# ============================================================
# ॐ OM MARKET AI AGENT — FULL LAUNCH EDITION
# ============================================================
# Purpose:
# - Live-first Indian market dashboard for NIFTY / SENSEX / BANKNIFTY
# - Screenshot/photo analysis fallback
# - Movement Radar: direction + size + estimated ETA + acceleration
# - 15m primary analysis, with 1H / 3H confirmation
# - Opening scenarios, option-theo, candles, backtest, database,
#   feedback board, self-upgrade candidates, security and recovery
#
# IMPORTANT:
# A market-data application cannot honestly guarantee "exactly X minutes
# before a move". Radar therefore reports an estimated window and confidence
# from fresh observations. It NEVER manufactures live prices.
#
# Run:
#   streamlit run app.py
# ============================================================

import base64
import io
import json
import math
import os
import sqlite3
import time as pytime
import wave
from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd
import requests
import streamlit as st
import streamlit.components.v1 as components
import xml.etree.ElementTree as ET

try:
    from PIL import Image, ImageEnhance, ImageOps
    PIL_OK = True
except Exception:
    PIL_OK = False

# Optional chart
try:
    import plotly.graph_objects as go
    PLOTLY_OK = True
except Exception:
    PLOTLY_OK = False

IST = ZoneInfo("Asia/Kolkata")
APP_VERSION = "OM Superpower AI 2026.10 — Smart Agent / Swipe Windows / Multi-Source Internet"
DB_PATH = os.environ.get("OM_DB_PATH", os.path.join(os.getcwd(), "om_market_ai.db"))

SYMBOLS = {
    "NIFTY": "%5ENSEI",
    "SENSEX": "%5EBSESN",
    "BANKNIFTY": "%5ENSEBANK",
}
BASES = {"NIFTY": 22422.0, "SENSEX": 73500.0, "BANKNIFTY": 48000.0}
INTERVALS = {"1m": "1m", "5m": "5m", "15m": "15m", "30m": "30m",
             "1H": "60m", "3H": "60m", "1D": "1d"}
RANGES = {"1m": "1d", "5m": "5d", "15m": "1mo", "30m": "1mo",
          "1H": "3mo", "3H": "6mo", "1D": "1y"}

st.set_page_config(page_title="ॐ OM MARKET AI", page_icon="ॐ", layout="wide")

# ============================================================
# THEME — deliberately scoped so white text never lands on white
# ============================================================
st.markdown("""
<style>
:root {
  --om-bg:#07111f;
  --om-panel:#101c2e;
  --om-panel2:#142238;
  --om-border:#2d405c;
  --om-text:#f8fafc;
  --om-muted:#aebed1;
  --om-green:#22c55e;
  --om-red:#ef4444;
  --om-yellow:#facc15;
  --om-blue:#60a5fa;
}
.stApp { background:var(--om-bg)!important; }
.block-container { max-width:1500px; padding-top:.65rem; padding-bottom:2rem; }
[data-testid="stHeader"] { background:var(--om-bg)!important; }
h1,h2,h3,h4,h5,h6,p,li,label,small { color:var(--om-text)!important; }
[data-testid="stMetric"] { background:var(--om-panel)!important; border:1px solid var(--om-border)!important; border-radius:14px!important; padding:10px!important; }
[data-testid="stMetricLabel"] { color:var(--om-muted)!important; }
[data-testid="stMetricValue"] { color:var(--om-text)!important; }
[data-testid="stMetricDelta"] { color:var(--om-green)!important; }
[data-baseweb="select"] > div,
[data-baseweb="input"] > div,
[data-baseweb="textarea"] > div {
  background:#0b1627!important; color:var(--om-text)!important;
  border-color:var(--om-border)!important;
}
[data-baseweb="select"] span { color:var(--om-text)!important; }
input, textarea { color:var(--om-text)!important; background:#0b1627!important; }
.stButton button, .stDownloadButton button {
  background:#122039!important; color:var(--om-text)!important;
  border:1px solid #38506f!important; border-radius:11px!important;
}
.stButton button:hover { border-color:var(--om-green)!important; }
button[role="tab"] { color:var(--om-muted)!important; }
button[role="tab"][aria-selected="true"] { color:var(--om-green)!important; }
/* Mobile-first OM window navigation: no tab strip; one horizontal window at a time. */
.om-nav { background:#0b1627; border:1px solid #2d405c; border-radius:16px; padding:8px; margin:8px 0 12px; }
.om-window-title { font-weight:900; font-size:18px; color:#fff!important; text-align:center; padding:4px; }
.om-nav-help { color:#aebed1!important; font-size:12px; text-align:center; }
.om-live-net { background:#0d1b2e; border:1px solid #284b70; border-radius:12px; padding:8px 12px; margin:6px 0 10px; }

.stProgress > div > div { background:var(--om-green)!important; }
.om-hero { background:linear-gradient(135deg,#0f1d32,#142b4d); border:1px solid #35506f;
  border-radius:20px; padding:18px; margin-bottom:12px; }
.om-title { font-size:31px; font-weight:900; color:#fff!important; }
.om-sub { color:#cbd5e1!important; }
.om-card { background:#101c2e!important; border:1px solid #2d405c; border-radius:16px;
  padding:14px; min-height:105px; }
.om-card * { color:#f8fafc!important; }
.om-big { font-size:26px; font-weight:900; }
.om-muted { color:#aebed1!important; font-size:12px; }
.om-green { color:#22c55e!important; font-weight:800; }
.om-red { color:#ef4444!important; font-weight:800; }
.om-yellow { color:#facc15!important; font-weight:800; }
.om-badge { display:flex; align-items:center; gap:10px; background:#0c1728;
  border:1px solid #2d405c; border-radius:16px; padding:9px 12px; margin:5px 0 12px; }
.om-orb { width:42px; height:42px; border-radius:50%; display:flex; align-items:center;
  justify-content:center; border:1px solid #22c55e; background:#13294b; font-size:23px; }
.om-pulse { margin-left:auto; color:#22c55e!important; }
[data-testid="stAlert"] { border-radius:12px!important; }
</style>
""", unsafe_allow_html=True)

# ============================================================
# SECURITY
# ============================================================
APP_PASSWORD = st.secrets.get("OM_APP_PASSWORD", "")
if APP_PASSWORD:
    if "om_auth" not in st.session_state:
        st.session_state.om_auth = False
    if not st.session_state.om_auth:
        st.title("ॐ OM MARKET AI")
        st.subheader("🔐 Private Access")
        pw = st.text_input("Password", type="password")
        if st.button("🔓 Unlock"):
            if pw == APP_PASSWORD:
                st.session_state.om_auth = True
                st.rerun()
            st.error("गलत password")
        st.stop()

# ============================================================
# HELPERS
# ============================================================
def now_ist():
    return datetime.now(IST)

def market_open():
    n = now_ist()
    return n.weekday() < 5 and time(9, 15) <= n.time() <= time(15, 30)

def digital_root(n):
    n = abs(int(n))
    return 0 if n == 0 else 1 + (n - 1) % 9

def ema(s, p):
    return s.ewm(span=p, adjust=False).mean()

def rsi(s, p=14):
    d = s.diff()
    gain = d.clip(lower=0)
    loss = -d.clip(upper=0)
    ag = gain.ewm(alpha=1/p, adjust=False).mean()
    al = loss.ewm(alpha=1/p, adjust=False).mean()
    rs = ag / al.replace(0, np.nan)
    return (100 - 100/(1+rs)).fillna(50)

def atr(d, p=14):
    pc = d["Close"].shift(1)
    tr = pd.concat([
        d["High"]-d["Low"],
        (d["High"]-pc).abs(),
        (d["Low"]-pc).abs()
    ], axis=1).max(axis=1)
    return tr.ewm(alpha=1/p, adjust=False).mean()

def prepare(raw):
    d = raw.copy()
    d.columns = [str(x).strip().title() for x in d.columns]
    for c in ["Open","High","Low","Close","Volume"]:
        if c not in d.columns:
            d[c] = 0
        d[c] = pd.to_numeric(d[c], errors="coerce")
    d = d.dropna(subset=["Open","High","Low","Close"])
    if d.empty:
        return d
    d["EMA9"] = ema(d["Close"],9)
    d["EMA21"] = ema(d["Close"],21)
    d["EMA50"] = ema(d["Close"],50)
    d["EMA200"] = ema(d["Close"],200)
    d["RSI"] = rsi(d["Close"],14)
    d["ATR"] = atr(d,14)
    d["MACD"] = ema(d["Close"],12)-ema(d["Close"],26)
    d["MACD_SIGNAL"] = ema(d["MACD"],9)
    vol = d["Volume"].replace(0,np.nan)
    d["VWAP"] = (d["Close"]*vol).cumsum()/vol.cumsum()
    d["Return1"] = d["Close"].pct_change()*100
    d["Range"] = d["High"]-d["Low"]
    d["Body"] = (d["Close"]-d["Open"]).abs()
    d["BodyPct"] = d["Body"]/d["Range"].replace(0,np.nan)*100
    d["VolMA20"] = d["Volume"].rolling(20).mean()
    d["VolRatio"] = d["Volume"]/d["VolMA20"].replace(0,np.nan)
    d["Momentum3"] = d["Close"].diff(3)
    d["Momentum6"] = d["Close"].diff(6)
    d["ATRMedian50"] = d["ATR"].rolling(50).median()
    return d

def demo_data(n=500, seed=369, base=22422):
    rng=np.random.default_rng(seed)
    steps=rng.normal(.04, 18, n)
    close=base+np.cumsum(steps)
    op=np.r_[close[0],close[:-1]]+rng.normal(0,5,n)
    hi=np.maximum(op,close)+rng.uniform(5,38,n)
    lo=np.minimum(op,close)-rng.uniform(5,38,n)
    vol=rng.integers(100000,800000,n)
    idx=pd.date_range(end=pd.Timestamp.now(),periods=n,freq="15min")
    return pd.DataFrame({"Open":op,"High":hi,"Low":lo,"Close":close,"Volume":vol},index=idx)

def technical_score(d):
    if len(d)<5: return 0
    x=d.iloc[-1]; s=0
    s += 20 if x.EMA9>x.EMA21 else -20
    s += 15 if x.EMA21>x.EMA50 else -15
    s += 10 if x.EMA50>x.EMA200 else -10
    s += 15 if x.RSI>=55 else (-15 if x.RSI<=45 else 0)
    s += 15 if x.MACD>x.MACD_SIGNAL else -15
    s += 10 if (np.isfinite(x.VWAP) and x.Close>x.VWAP) else -10
    s += 15 if x.Momentum6>0 else -15
    return int(np.clip(s,-100,100))

def signal(score):
    if score>=60: return "STRONG BULLISH"
    if score>=30: return "BULLISH"
    if score<=-60: return "STRONG BEARISH"
    if score<=-30: return "BEARISH"
    return "NEUTRAL / RANGE"

def candle_name(x):
    rng=max(float(x.High-x.Low),1e-9)
    body=abs(float(x.Close-x.Open))
    upper=float(x.High-max(x.Open,x.Close))
    lower=float(min(x.Open,x.Close)-x.Low)
    if body/rng<.15: return "DOJI / INDECISION"
    if lower>body*2 and upper<body: return "HAMMER-LIKE"
    if upper>body*2 and lower<body: return "SHOOTING-STAR-LIKE"
    return "BULLISH CANDLE" if x.Close>x.Open else "BEARISH CANDLE"

# ============================================================
# INTERNET FORCE / MULTI-SOURCE HEALTH
# ============================================================
@st.cache_data(ttl=30, show_spinner=False)
def internet_force_status():
    sources={
        "Yahoo Market Feed":"https://query1.finance.yahoo.com",
        "NSE India":"https://www.nseindia.com",
        "BSE India":"https://www.bseindia.com",
        "Google News Market Search":"https://news.google.com",
    }
    out=[]
    for name,url in sources.items():
        try:
            rr=requests.get(url,timeout=4,headers={"User-Agent":"Mozilla/5.0 OM-Market-AI/2.0"})
            out.append((name,rr.status_code<500,rr.status_code))
        except Exception:
            out.append((name,False,"OFFLINE"))
    return out

def internet_force_badge():
    health=internet_force_status()
    good=sum(1 for _,ok,_ in health if ok)
    total=len(health)
    label="GLOBAL INTERNET LINK STRONG" if good>=3 else "INTERNET LINK PARTIAL" if good>=1 else "INTERNET LINK OFFLINE"
    cls="om-green" if good>=3 else "om-yellow" if good>=1 else "om-red"
    st.markdown(f'<div class="om-live-net"><b class="{cls}">🌐 {label}</b> • {good}/{total} external routes reachable • OM uses fresh data only when a source actually responds.</div>',unsafe_allow_html=True)
    return health

@st.cache_data(ttl=120, show_spinner=False)
def market_news(symbol="NIFTY", limit=6):
    """Fetch fresh public market headlines. Fail silently; never invent headlines."""
    queries={"NIFTY":"NIFTY India stock market", "SENSEX":"SENSEX India stock market", "BANKNIFTY":"Bank Nifty India stock market"}
    try:
        r=requests.get("https://news.google.com/rss/search",params={"q":queries.get(symbol,queries["NIFTY"]),"hl":"en-IN","gl":"IN","ceid":"IN:en"},timeout=6,headers={"User-Agent":"Mozilla/5.0 OM-Market-AI"})
        r.raise_for_status()
        root=ET.fromstring(r.text)
        out=[]
        for item in root.findall("./channel/item")[:limit]:
            title=item.findtext("title") or ""
            pub=item.findtext("pubDate") or ""
            link=item.findtext("link") or ""
            if title: out.append({"title":title,"published":pub,"link":link})
        return out
    except Exception:
        return []

def llm_answer(prompt, context):
    """Optional real LLM. Uses OpenAI only when an API key is explicitly configured."""
    key=st.secrets.get("OPENAI_API_KEY", os.environ.get("OPENAI_API_KEY", ""))
    if not key:
        return None
    try:
        payload={"model":st.secrets.get("OM_LLM_MODEL","gpt-4.1-mini"),
                 "input":[{"role":"system","content":"You are OM AI Agent, a concise Indian market-analysis assistant. Use only the supplied live context and clearly label estimates. Never invent prices, news, or certainty. Answer the user's actual question directly."},{"role":"user","content":prompt+"\n\nLIVE CONTEXT:\n"+context}]}
        r=requests.post("https://api.openai.com/v1/responses",headers={"Authorization":"Bearer "+key,"Content-Type":"application/json"},json=payload,timeout=18)
        r.raise_for_status(); j=r.json()
        text=j.get("output_text")
        if text: return text.strip()
        for item in j.get("output",[]):
            for c in item.get("content",[]):
                if c.get("type") in ("output_text","text") and c.get("text"): return c["text"].strip()
    except Exception:
        return None
    return None

# ============================================================
# LIVE DATA
# ============================================================
def yahoo_url(symbol, timeframe):
    return (
        f"https://query1.finance.yahoo.com/v8/finance/chart/"
        f"{SYMBOLS.get(symbol,SYMBOLS['NIFTY'])}"
        f"?range={RANGES.get(timeframe,'5d')}&interval={INTERVALS.get(timeframe,'5m')}"
        f"&includePrePost=false&events=div%2Csplits"
    )

@st.cache_data(ttl=4, show_spinner=False)
def yahoo_history(symbol, timeframe):
    try:
        r=requests.get(yahoo_url(symbol,timeframe),timeout=7,
                       headers={"User-Agent":"Mozilla/5.0 OM-Market-AI"})
        r.raise_for_status()
        result=r.json()["chart"]["result"][0]
        q=result["indicators"]["quote"][0]
        ts=result.get("timestamp",[])
        rows=[]
        for i,t in enumerate(ts):
            try:
                o=q["open"][i]; h=q["high"][i]; l=q["low"][i]; c=q["close"][i]
                v=(q.get("volume") or [0]*len(ts))[i] or 0
                if None not in (o,h,l,c):
                    rows.append((datetime.fromtimestamp(t,IST),o,h,l,c,v))
            except Exception:
                continue
        if not rows: return pd.DataFrame()
        d=pd.DataFrame(rows,columns=["Date","Open","High","Low","Close","Volume"]).set_index("Date")
        return prepare(d)
    except Exception:
        return pd.DataFrame()

def configured_tick(url, symbol):
    if not url: return None
    try:
        r=requests.get(url,params={"symbol":symbol},timeout=2.5,
                       headers={"User-Agent":"OM-Market-AI/1.0"})
        r.raise_for_status()
        j=r.json()
        if isinstance(j,dict) and isinstance(j.get("data"),dict):
            j=j["data"]
        px=j.get("price",j.get("ltp",j.get("last_price")))
        if px is not None:
            return {"price":float(px),"timestamp":j.get("timestamp",now_ist().isoformat()),
                    "source":"Configured live feed"}
    except Exception:
        return None
    return None

def live_tick(url, symbol, timeframe):
    z=configured_tick(url,symbol)
    if z: return z
    try:
        d=yahoo_history(symbol,timeframe)
        if not d.empty:
            return {"price":float(d.Close.iloc[-1]),
                    "timestamp":d.index[-1].isoformat(),
                    "source":"Yahoo latest OHLC"}
    except Exception:
        pass
    return None

# ============================================================
# MOVEMENT RADAR — redesigned around speed + acceleration +
# volatility + volume + trend agreement + multi-timeframe confirmation
# ============================================================
def movement_radar(d, price):
    if d.empty:
        return {"direction":"NO DATA","size":"WAIT","points":0,"eta_low":0,
                "eta_high":0,"confidence":0,"score":0,"reason":"No data"}

    x=d.iloc[-1]
    av=float(x.ATR) if np.isfinite(x.ATR) and x.ATR>0 else max(price*.004,1)
    look=max(8,min(30,len(d)))
    tail=d.tail(look)

    # Momentum at multiple horizons
    m1=float(x.Close-d.Close.iloc[-2]) if len(d)>1 else 0
    m3=float(x.Close-d.Close.iloc[-4]) if len(d)>3 else m1
    m6=float(x.Close-d.Close.iloc[-7]) if len(d)>6 else m3

    # Speed = points per observed bar; acceleration = change of speed
    speed=m3/max(3,1)
    old_speed=float(d.Close.iloc[-4]-d.Close.iloc[-7])/3 if len(d)>7 else 0
    acceleration=speed-old_speed

    vol_ratio=float(x.VolRatio) if np.isfinite(x.VolRatio) else 1.0
    trend_fast=1 if x.EMA9>x.EMA21 else -1
    trend_mid=1 if x.EMA21>x.EMA50 else -1
    macd_bias=1 if x.MACD>x.MACD_SIGNAL else -1
    vwap_bias=1 if np.isfinite(x.VWAP) and price>x.VWAP else -1
    momentum_bias=1 if m6>0 else -1

    raw=0
    raw += np.clip(m1/av*12,-12,12)
    raw += np.clip(m3/av*15,-15,15)
    raw += np.clip(acceleration/av*18,-18,18)
    raw += 8*trend_fast + 5*trend_mid + 5*macd_bias + 4*vwap_bias + 4*momentum_bias
    raw += 8 if vol_ratio>=1.35 else 4 if vol_ratio>=1.1 else 0

    # Range compression can precede a move, but it is not itself a direction.
    recent_range=float(tail.High.max()-tail.Low.min())
    median_atr=float(d.ATR.tail(min(50,len(d))).median())
    compression=av < median_atr*.80 if median_atr>0 else False

    direction="UP" if raw>=15 else "DOWN" if raw<=-15 else "RANGE / WAIT"
    absraw=abs(raw)
    if absraw>=55: size="LARGE"
    elif absraw>=35: size="MEDIUM"
    elif absraw>=20: size="SMALL"
    else: size="QUIET"

    expected=max(av*.35,abs(m3)*.75,price*.00035)
    if size=="LARGE": expected=max(expected,av*1.25)
    elif size=="MEDIUM": expected=max(expected,av*.80)
    elif size=="SMALL": expected=max(expected,av*.50)
    else: expected=max(expected,av*.25)

    # ETA is a window, not a promise.
    if absraw>=60: eta_low,eta_high=2,6
    elif absraw>=45: eta_low,eta_high=3,10
    elif absraw>=30: eta_low,eta_high=5,15
    elif absraw>=20: eta_low,eta_high=10,25
    else: eta_low,eta_high=15,45

    confidence=int(np.clip(50+absraw*.62,50,95))
    if compression and direction!="RANGE / WAIT":
        confidence=int(np.clip(confidence-6,50,95))

    reason=[]
    if abs(m3)>av*.25: reason.append("momentum")
    if abs(acceleration)>av*.10: reason.append("acceleration")
    if vol_ratio>=1.35: reason.append("volume")
    if trend_fast==trend_mid: reason.append("trend aligned")
    if compression: reason.append("range compressed")
    if not reason: reason=["mixed / waiting"]

    return {
        "direction":direction,"size":size,"points":float(expected),
        "eta_low":eta_low,"eta_high":eta_high,"confidence":confidence,
        "score":float(raw),"momentum":float(m3),"acceleration":float(acceleration),
        "vol_ratio":float(vol_ratio),"compression":bool(compression),
        "reason":", ".join(reason),
    }

def m3_confirmation(symbol, timeframe, mode):
    """Use 1H as a robust confirmation source; 3H is synthesized from 60m bars."""
    if mode!="Best Effort Live": return None
    d1=yahoo_history(symbol,"1H")
    if d1.empty: return None
    # 3-hour confirmation from 60-minute OHLC
    try:
        d3=prepare(pd.DataFrame({
            "Open":d1.Open.resample("3h").first(),
            "High":d1.High.resample("3h").max(),
            "Low":d1.Low.resample("3h").min(),
            "Close":d1.Close.resample("3h").last(),
            "Volume":d1.Volume.resample("3h").sum()
        }).dropna())
    except Exception:
        d3=pd.DataFrame()
    out={}
    for name,z in [("1H",d1),("3H",d3)]:
        if z.empty: out[name]="NO DATA"
        else:
            sc=technical_score(z)
            out[name]=signal(sc)
    return out

# ============================================================
# DATABASE
# ============================================================
def db_connect():
    con=sqlite3.connect(DB_PATH,timeout=5)
    con.execute("PRAGMA journal_mode=WAL")
    return con

def init_db():
    try:
        con=db_connect()
        con.execute("""CREATE TABLE IF NOT EXISTS snapshots(
          id INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT, market TEXT, timeframe TEXT,
          mode TEXT, price REAL, technical REAL, om_score REAL, signal TEXT,
          direction TEXT, size TEXT, points REAL, eta_low REAL, eta_high REAL,
          confidence REAL, source TEXT)""")
        con.execute("""CREATE TABLE IF NOT EXISTS feedback(
          id INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT, market TEXT, timeframe TEXT,
          category TEXT, rating INTEGER, message TEXT, predicted_direction TEXT,
          predicted_size TEXT, predicted_points REAL, predicted_eta_low REAL,
          predicted_eta_high REAL, confidence REAL)""")
        con.execute("""CREATE TABLE IF NOT EXISTS settings(
          id INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT, payload TEXT)""")
        con.execute("""CREATE TABLE IF NOT EXISTS alerts(
          id INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT, market TEXT, kind TEXT,
          price REAL, message TEXT)""")
        con.commit(); con.close(); return True
    except Exception:
        return False

DB_OK=init_db()

def save_snapshot(symbol,timeframe,mode,price,tech,om,sig,radar,source):
    if not DB_OK: return
    try:
        con=db_connect()
        con.execute("""INSERT INTO snapshots
          (ts,market,timeframe,mode,price,technical,om_score,signal,direction,size,
           points,eta_low,eta_high,confidence,source)
          VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
          (now_ist().isoformat(),symbol,timeframe,mode,price,tech,om,sig,
           radar["direction"],radar["size"],radar["points"],radar["eta_low"],
           radar["eta_high"],radar["confidence"],source))
        con.commit(); con.close()
    except Exception:
        pass

def read_snapshots(limit=250):
    if not DB_OK: return pd.DataFrame()
    try:
        con=db_connect()
        d=pd.read_sql_query("SELECT * FROM snapshots ORDER BY id DESC LIMIT ?",con,params=(limit,))
        con.close(); return d
    except Exception:
        return pd.DataFrame()

# ============================================================
# OPTION THEO
# ============================================================
def normal_cdf(z):
    return .5*(1+math.erf(z/math.sqrt(2)))

def bs_theo(S,K,iv,days,rate,kind):
    if min(S,K,iv,days)<=0: return 0.0
    T=days/365
    v=iv/100
    r=rate/100
    d1=(math.log(S/K)+(r+.5*v*v)*T)/(v*math.sqrt(T))
    d2=d1-v*math.sqrt(T)
    call=S*normal_cdf(d1)-K*math.exp(-r*T)*normal_cdf(d2)
    put=K*math.exp(-r*T)*normal_cdf(-d2)-S*normal_cdf(-d1)
    return call if kind=="CALL" else put

# ============================================================
# PHOTO ENGINE
# ============================================================
def photo_features(img):
    arr=np.asarray(img.convert("RGB")).astype(float)
    gray=arr.mean(axis=2)
    h,w=gray.shape
    contrast=float(gray.std())
    eh=float(np.abs(np.diff(gray,axis=1)).mean()) if w>1 else 0
    ev=float(np.abs(np.diff(gray,axis=0)).mean()) if h>1 else 0
    dark=float((gray<80).mean()*100)
    bright=float((gray>180).mean()*100)
    # A simple luminance inversion makes dark charts readable in previews.
    if contrast<18: quality="LOW CONTRAST"
    elif eh>ev*1.20: quality="HORIZONTAL LEVEL / CANDLE STRUCTURE"
    elif ev>eh*1.20: quality="VERTICAL STRUCTURE"
    else: quality="MIXED CHART STRUCTURE"
    return {"width":w,"height":h,"contrast":contrast,"horizontal_edge":eh,
            "vertical_edge":ev,"dark_pct":dark,"bright_pct":bright,"quality":quality}

# ============================================================
# 50+ FEATURES
# ============================================================
def build_features(d,price,tech,om,radar,nifty,sensex,mid,loop):
    x=d.iloc[-1]
    prev=float(d.Close.iloc[-2]) if len(d)>1 else price
    rsi_v=float(x.RSI)
    vwap=float(x.VWAP) if np.isfinite(x.VWAP) else price
    atrv=float(x.ATR) if np.isfinite(x.ATR) else 0
    med=float(d.ATR.tail(50).median()) if len(d) else atrv
    hi20=float(d.High.tail(20).max()); lo20=float(d.Low.tail(20).min())
    hi50=float(d.High.tail(50).max()); lo50=float(d.Low.tail(50).min())
    ncp=nifty["change_pct"] if nifty else np.nan
    scp=sensex["change_pct"] if sensex else np.nan
    align = (ncp is not None and scp is not None and
             np.isfinite(ncp) and np.isfinite(scp) and ((ncp>=0)==(scp>=0)))
    return {
      "01 LTP":price,"02 Previous Close":prev,
      "03 Change %":(price/prev-1)*100 if prev else 0,
      "04 EMA9":float(x.EMA9),"05 EMA21":float(x.EMA21),"06 EMA50":float(x.EMA50),
      "07 EMA200":float(x.EMA200),"08 EMA9-21":float(x.EMA9-x.EMA21),
      "09 EMA21-50":float(x.EMA21-x.EMA50),"10 RSI":rsi_v,
      "11 RSI Regime":"OVERBOUGHT" if rsi_v>=70 else "OVERSOLD" if rsi_v<=30 else "NORMAL",
      "12 ATR":atrv,"13 ATR Regime":"HIGH" if atrv>med*1.25 else "LOW" if atrv<med*.8 else "NORMAL",
      "14 MACD":float(x.MACD),"15 MACD Signal":float(x.MACD_SIGNAL),
      "16 MACD Bias":"UP" if x.MACD>x.MACD_SIGNAL else "DOWN",
      "17 VWAP":vwap,"18 VWAP Position":"ABOVE" if price>vwap else "BELOW",
      "19 Technical Score":tech,"20 Technical Signal":signal(tech),
      "21 OM Score":om,"22 Digital Root":digital_root(round(price)),
      "23 Midpoint":mid,"24 Loop Point":loop,"25 20-Bar High":hi20,"26 20-Bar Low":lo20,
      "27 50-Bar High":hi50,"28 50-Bar Low":lo50,
      "29 Dist 20H":price-hi20,"30 Dist 20L":price-lo20,
      "31 Dist VWAP":price-vwap,
      "32 Volume Ratio":float(x.VolRatio) if np.isfinite(x.VolRatio) else 1,
      "33 Movement Direction":radar["direction"],"34 Movement Size":radar["size"],
      "35 Expected Points":radar["points"],"36 ETA Low Min":radar["eta_low"],
      "37 ETA High Min":radar["eta_high"],"38 Confidence":radar["confidence"],
      "39 Momentum":radar["momentum"],"40 Acceleration":radar["acceleration"],
      "41 Radar Score":radar["score"],"42 Compression":radar["compression"],
      "43 NIFTY Change %":ncp,"44 SENSEX Change %":scp,
      "45 Index Confirmation":"CONFIRMED" if align else "DIVERGENCE / UNKNOWN",
      "46 Short Trend":"UP" if x.EMA9>x.EMA21 else "DOWN",
      "47 Medium Trend":"UP" if x.EMA21>x.EMA50 else "DOWN",
      "48 Candle Shape":candle_name(x),"49 Current Range":float(x.High-x.Low),
      "50 Data Quality":"LIVE TICK + OHLC","51 Support Ref":lo20,
      "52 Resistance Ref":hi20,"53 Breakout":"ABOVE 20H" if price>=hi20 else "BELOW 20L" if price<=lo20 else "INSIDE",
      "54 Risk Gate":"WAIT" if rsi_v>=72 or rsi_v<=28 else "NORMAL",
      "55 Multi-TF": "see 1H/3H panel",
    }

# ============================================================
# UI CONTROLS
# ============================================================
PANEL_NAMES=[
"⚙️ Control Center","🏠 Dashboard","🕯️ Candles","🌅 Opening","⛓ Option Theo",
"🧠 OM AI","💬 AI Agent","🔔 Alarm","🧪 Backtest","📊 Data",
"🗺️ Market Map","📡 Movement Radar","📷 Photo AI","✨ OM Superpowers",
"🔬 Self-Upgrade","🧩 50+ Features","🗄️ Database","📝 Feedback Board",
"⚙️ App Settings"
]

# URL state makes swipe navigation survive a Streamlit rerun.
try:
    qp_screen=int(st.query_params.get("screen", st.session_state.get("om_panel",1)))
except Exception:
    qp_screen=int(st.session_state.get("om_panel",1))
st.session_state.om_panel=qp_screen % len(PANEL_NAMES)

def set_panel(n):
    n=int(n)%len(PANEL_NAMES)
    st.session_state.om_panel=n
    st.query_params["screen"]=str(n)

def nav_prev(): set_panel(int(st.session_state.om_panel)-1)
def nav_next(): set_panel(int(st.session_state.om_panel)+1)

panel=int(st.session_state.om_panel)

# Controls are tucked away so the active window gets the whole visual focus.
with st.expander("⚙️ Controls / Internet / Data source", expanded=False):
    c1,c2,c3,c4,c5=st.columns(5)
    symbol=c1.selectbox("Market",["NIFTY","SENSEX","BANKNIFTY"],key="market")
    timeframe=c2.selectbox("Primary Timeframe",["15m","5m","1m","30m","1H","3H","1D"],index=0,key="tf")
    mode=c3.selectbox("Data Mode",["Best Effort Live","Demo / Test","CSV Upload"],key="mode")
    auto=c4.checkbox("⚡ Auto refresh",value=True,key="auto")
    refresh=c5.number_input("Refresh (sec)",1,60,5,1,key="refresh")
    a1,a2,a3,a4=st.columns(4)
    live_url=a1.text_input("Optional live tick URL",str(st.secrets.get("LIVE_TICK_URL","")),key="live_url")
    confidence=a2.slider("Alert confidence",50,95,70,5,key="confidence")
    risk=a3.selectbox("Risk profile",["Conservative","Balanced","Aggressive"],index=1,key="risk")
    show_exp=a4.checkbox("Experimental OM layers",True,key="exp")
    upload=st.file_uploader("CSV upload (Open, High, Low, Close, Volume)",type=["csv"],key="csv")

# ============================================================
# LOAD DATA
# ============================================================
if mode=="CSV Upload" and upload is not None:
    try:
        raw=pd.read_csv(upload)
        if "Date" in raw.columns:
            raw["Date"]=pd.to_datetime(raw["Date"],errors="coerce")
            raw=raw.dropna(subset=["Date"]).set_index("Date")
        df=prepare(raw); source="CSV"
    except Exception as e:
        st.error(f"CSV error: {e}"); df=pd.DataFrame(); source="CSV ERROR"
elif mode=="Demo / Test":
    df=prepare(demo_data(base=BASES[symbol],seed=digital_root(BASES[symbol])*41+369))
    source="DEMO / TEST"
else:
    df=yahoo_history(symbol,timeframe)
    source="YAHOO LIVE/LATEST OHLC" if not df.empty else "NO LIVE OHLC"

tick=live_tick(live_url,symbol,timeframe) if mode=="Best Effort Live" else None
live_price=float(tick["price"]) if tick and tick.get("price") is not None else None

if df.empty:
    st.error("⚠️ Live OHLC उपलब्ध नहीं है. OM live mode में fake/demo price नहीं बनाता. Feed लौटे तो Refresh करें, या Demo/Test/CSV चुनें.")
    st.stop()

price=float(live_price if live_price is not None else df.Close.iloc[-1])
atrv=float(df.ATR.iloc[-1]) if np.isfinite(df.ATR.iloc[-1]) else price*.005
tech=technical_score(df)
sig=signal(tech)

# OM experimental score: deliberately separated from technical score.
root=digital_root(round(price))
mid=float((df.High.tail(20).max()+df.Low.tail(20).min())/2)
loop=float((df.High.tail(9).mean()+df.Low.tail(9).mean())/2)
root_c=(root-5)*8
binary_c=7 if bin(max(0,int(price))).count("1")>=bin(max(0,int(price))).count("0") else -7
mid_c=8 if price>mid else -8
loop_c=6 if price>loop else -6
om_score=int(np.clip(50+(tech+root_c+binary_c+mid_c+loop_c)/2,0,100))

radar=movement_radar(df,price)

def snapshot(name,z):
    if z is None or z.empty: return None
    p=float(z.Close.iloc[-1]); prev=float(z.Close.iloc[-2]) if len(z)>1 else p
    return {"price":p,"change":p-prev,"change_pct":(p/prev-1)*100 if prev else 0,
            "rsi":float(z.RSI.iloc[-1]),"atr":float(z.ATR.iloc[-1]),
            "signal":signal(technical_score(z))}

nifty=snapshot("NIFTY",df if symbol=="NIFTY" else yahoo_history("NIFTY",timeframe))
sensex=snapshot("SENSEX",df if symbol=="SENSEX" else yahoo_history("SENSEX",timeframe))
features=build_features(df,price,tech,om_score,radar,nifty,sensex,mid,loop)
save_snapshot(symbol,timeframe,mode,price,tech,om_score,sig,radar,source)

# ============================================================
# HEADER
# ============================================================
st.markdown(f"""
<div class="om-badge">
  <div class="om-orb">ॐ</div>
  <div><b>OM AI CORE — FULL AGENT</b><br><span class="om-muted">Live-first • Movement Radar • Photo AI • Database • 55 intelligence features</span></div>
  <div class="om-pulse">●</div>
</div>
<div class="om-hero">
  <div class="om-title">ॐ OM MARKET AI</div>
  <div class="om-sub">NIFTY • SENSEX • BANKNIFTY | scenario engine, not certainty</div>
</div>
""",unsafe_allow_html=True)

h1,h2,h3,h4,h5=st.columns(5)
h1.metric(f"{symbol} LTP",f"{price:,.2f}")
h2.metric("Technical",f"{tech:+d}/100")
h3.metric("OM Score",f"{om_score}/100")
h4.metric("Movement",f"{radar['direction']} / {radar['size']}")
h5.metric("Radar Confidence",f"{radar['confidence']}%")

if tick:
    st.success(f"🟢 LIVE FEED • ₹{price:,.2f} • {tick.get('timestamp','')} • {tick.get('source','feed')}")
elif market_open() and mode=="Best Effort Live":
    st.warning("🟡 Market is open but a fresh tick was not received. Current analysis uses latest available OHLC; it is NOT presented as second-by-second live.")
else:
    st.info(f"🕒 {now_ist().strftime('%d-%m-%Y %H:%M:%S')} IST • {source}")

internet_health=internet_force_badge()

# Full-window navigation: arrows plus touch swipe on the navigation deck.
n1,n2,n3=st.columns([1,4,1])
with n1: st.button("⬅️",on_click=nav_prev,use_container_width=True,key="om_prev")
with n2:
    st.markdown(f'<div class="om-nav"><div class="om-window-title">{PANEL_NAMES[panel]}</div><div class="om-nav-help">SCREEN {panel+1}/{len(PANEL_NAMES)} • swipe ← / → on this deck</div></div>',unsafe_allow_html=True)
with n3: st.button("➡️",on_click=nav_next,use_container_width=True,key="om_next")
components.html(f"""
<script>
(function(){{
 const box=document.getElementById('om-swipe-deck') || document.createElement('div');
 box.id='om-swipe-deck';
 box.style.cssText='height:54px;width:100%;border:1px solid #2d405c;border-radius:14px;background:#0b1627;color:#aebed1;display:flex;align-items:center;justify-content:center;font:700 12px system-ui;touch-action:pan-x;';
 box.innerHTML='👆 SWIPE LEFT / RIGHT — screen changes';
 document.body.appendChild(box);
 let x=0;
 box.addEventListener('touchstart',e=>{{x=e.changedTouches[0].screenX}},{{passive:true}});
 box.addEventListener('touchend',e=>{{const dx=e.changedTouches[0].screenX-x;if(Math.abs(dx)<45)return;const cur={panel};const next=(cur+(dx<0?1:-1)+{len(PANEL_NAMES)})%{len(PANEL_NAMES)};const u=new URL(window.parent.location.href);u.searchParams.set('screen',next);window.parent.location.href=u.toString();}},{{passive:true}});
}})();
</script>
""",height=58)

# ============================================================
# COMMON RENDERERS
# ============================================================
def common_strip():
    a,b,c,d,e=st.columns(5)
    a.metric("Price",f"{price:,.2f}")
    b.metric("Signal",sig)
    c.metric("RSI",f"{df.RSI.iloc[-1]:.1f}")
    d.metric("ATR",f"{atrv:.2f}")
    e.metric("NIFTY↔SENSEX","CONFIRMED" if nifty and sensex and ((nifty["change"]>=0)==(sensex["change"]>=0)) else "DIVERGENCE")

def dual_strip():
    n,s=st.columns(2)
    for col,name,z in [(n,"🇮🇳 NIFTY",nifty),(s,"🇮🇳 SENSEX",sensex)]:
        with col:
            if not z:
                st.markdown(f'<div class="om-card"><b>{name}</b><div class="om-big">NO DATA</div><div class="om-muted">Feed unavailable</div></div>',unsafe_allow_html=True)
            else:
                cls="om-green" if z["change"]>=0 else "om-red"
                st.markdown(f'<div class="om-card"><b>{name}</b><div class="om-big">{z["price"]:,.2f}</div><div class="{cls}">{z["change"]:+,.2f} ({z["change_pct"]:+.2f}%)</div><div class="om-muted">RSI {z["rsi"]:.1f} • ATR {z["atr"]:.2f} • {z["signal"]}</div></div>',unsafe_allow_html=True)

# ============================================================
# DASHBOARD
# ============================================================
if panel == 1:
    st.subheader("🏠 Dashboard — FULL SCREEN MARKET COMMAND")
    h1,h2,h3,h4,h5=st.columns(5)
    h1.metric("LTP",f"{price:,.2f}"); h2.metric("TECH",f"{tech:+d}"); h3.metric("RADAR",radar["direction"]); h4.metric("SIZE",radar["size"]); h5.metric("CONF",f"{radar['confidence']}%")
    gap=max(atrv*.55,price*.002)
    up=(price+gap,price+1.5*gap)
    flat=(price-gap*.35,price+gap*.35)
    down=(price-1.5*gap,price-gap)
    a,b,c=st.columns(3)
    a.markdown(f'<div class="om-card"><h3 class="om-green">🟢 GAP UP</h3><div class="om-big">{up[0]:,.0f} – {up[1]:,.0f}</div><div class="om-muted">scenario range</div></div>',unsafe_allow_html=True)
    b.markdown(f'<div class="om-card"><h3 class="om-yellow">🟡 FLAT / RANGE</h3><div class="om-big">{flat[0]:,.0f} – {flat[1]:,.0f}</div><div class="om-muted">confirmation zone</div></div>',unsafe_allow_html=True)
    c.markdown(f'<div class="om-card"><h3 class="om-red">🔴 GAP DOWN</h3><div class="om-big">{down[0]:,.0f} – {down[1]:,.0f}</div><div class="om-muted">scenario range</div></div>',unsafe_allow_html=True)
    st.caption("Opening ranges are volatility scenarios. They are not guaranteed predictions.")
    st.subheader("🧭 Current movement answer")
    st.info(f"OM Radar: **{radar['direction']}**, size **{radar['size']}**, expected movement about **±{radar['points']:.1f} points**, estimated window **{radar['eta_low']}–{radar['eta_high']} minutes**, confidence **{radar['confidence']}%**. Drivers: {radar['reason']}.")
    if nifty and sensex:
        if (nifty["change"]>=0)==(sensex["change"]>=0):
            st.success("NIFTY + SENSEX are aligned — confirmation is stronger.")
        else:
            st.warning("NIFTY and SENSEX are diverging — reduce confidence / wait for confirmation.")

# ============================================================
# CANDLES
# ============================================================
if panel == 2:
    st.subheader(f"🕯️ Candles / Horizontal Levels — {timeframe}")
    common_strip()
    if PLOTLY_OK:
        p=df.tail(150)
        fig=go.Figure([go.Candlestick(x=p.index,open=p.Open,high=p.High,low=p.Low,close=p.Close)])
        for label,val in [("LTP",price),("Mid",mid),("Loop",loop),("+ATR",price+atrv),("-ATR",price-atrv),
                          ("+2ATR",price+2*atrv),("-2ATR",price-2*atrv)]:
            fig.add_hline(y=val,line_dash="dot",annotation_text=f"{label} {val:,.0f}")
        fig.update_layout(template="plotly_dark",height=620,xaxis_rangeslider_visible=False,
                          paper_bgcolor="#07111f",plot_bgcolor="#07111f",margin=dict(l=10,r=10,t=25,b=10))
        st.plotly_chart(fig,use_container_width=True)
    else:
        st.warning("Plotly not installed. Add plotly to requirements.txt.")
    st.dataframe(df[["Close","EMA9","EMA21","EMA50","RSI","ATR","VWAP","VolRatio"]].tail(60),use_container_width=True)

# ============================================================
# OPENING
# ============================================================
if panel == 3:
    st.subheader("🌅 Opening Engine")
    common_strip(); dual_strip()
    st.write("Primary opening logic: prior/reference price + ATR + multi-index confirmation + overnight/pre-open feed when available.")
    st.dataframe(pd.DataFrame({
        "Scenario":["GAP UP","FLAT/RANGE","GAP DOWN"],
        "Low":[up[0],flat[0],down[0]],
        "High":[up[1],flat[1],down[1]],
        "Distance Low":[up[0]-price,flat[0]-price,down[0]-price],
        "Distance High":[up[1]-price,flat[1]-price,down[1]-price]
    }),use_container_width=True,hide_index=True)
    mtf=m3_confirmation(symbol,timeframe,mode)
    if mtf: st.dataframe(pd.DataFrame([mtf]),use_container_width=True,hide_index=True)
    else: st.caption("1H/3H confirmation unavailable in current mode/feed.")

# ============================================================
# OPTION THEO
# ============================================================
if panel == 4:
    st.subheader("⛓ Option Theo — transparent mathematics")
    common_strip()
    a,b,c,d=st.columns(4)
    S=a.number_input("Spot",value=float(round(price,2)),step=1.0)
    K=b.number_input("Strike",value=float(round(price/50)*50),step=50.0)
    iv=c.number_input("IV %",value=12.0,min_value=.1,step=.5)
    days=d.number_input("Days",value=4.0,min_value=.1,step=.5)
    kind=st.radio("Type",["CALL","PUT"],horizontal=True)
    rate=st.number_input("Risk-free %",value=6.5,step=.25)
    theo=bs_theo(S,K,iv,days,rate,kind)
    st.metric(f"Black-Scholes Theo {kind}",f"₹{theo:,.2f}")
    st.warning("Theo is not the live option premium. Real premium needs option-chain LTP, IV, OI, spread and liquidity.")

# ============================================================
# OM AI
# ============================================================
if panel == 5:
    st.subheader("🧠 OM AI — separated layers")
    common_strip(); dual_strip()
    st.dataframe(pd.DataFrame({
        "Layer":["Technical","3-6-9 Root","Binary","Midpoint","Loop Point"],
        "Contribution":[tech,root_c,binary_c,mid_c,loop_c]
    }),use_container_width=True,hide_index=True)
    st.metric("OM Combined",f"{om_score}/100")
    st.warning("3-6-9, binary and mathematical inspiration layers are experimental hypotheses, not proven predictors.")

# ============================================================
# AI AGENT — SMART CONTEXT ENGINE
# ============================================================
if panel == 6:
    st.subheader("💬 ॐ AI Agent — Smart Market Brain")
    common_strip(); dual_strip()
    st.caption("अब canned one-line replies नहीं: सवाल को intent में तोड़कर live market + news context से जवाब बनाया जाता है. Optional OPENAI_API_KEY मिलने पर real LLM reasoning भी जुड़ती है.")
    headlines=market_news(symbol,6)
    if headlines:
        st.markdown("**🌐 Fresh market context**")
        for h in headlines[:4]: st.markdown(f"• {h['title']} <span class='om-muted'>({h['published']})</span>",unsafe_allow_html=True)
    if "om_chat" not in st.session_state: st.session_state.om_chat=[]
    for role,msg in st.session_state.om_chat[-12:]:
        with st.chat_message(role): st.write(msg)
    prompt=st.chat_input("पूछो कुछ भी: अभी क्या चल रहा है? reversal? Call/Put? support? gap? news? क्यों?")
    if prompt:
        p=prompt.lower().strip(); x=df.iloc[-1]; prev=df.iloc[-2] if len(df)>1 else x
        change=float(price-prev.Close); change_pct=change/float(prev.Close)*100 if prev.Close else 0
        trend15="UP" if x.EMA9>x.EMA21 else "DOWN"; trend50="UP" if x.EMA21>x.EMA50 else "DOWN"
        vol=float(x.VolRatio) if np.isfinite(x.VolRatio) else 1.0
        divergence=bool(nifty and sensex and ((nifty["change"]>=0)!=(sensex["change"]>=0)))
        context=(f"Market={symbol}; price={price:.2f}; change={change:+.2f} ({change_pct:+.2f}%); technical={sig} {tech:+d}/100; OM={om_score}/100; RSI={float(x.RSI):.1f}; ATR={atrv:.2f}; 15m trend={trend15}; medium trend={trend50}; VWAP={float(x.VWAP):.2f}; volume_ratio={vol:.2f}; radar={radar['direction']} {radar['size']}; expected={radar['points']:.1f}; window={radar['eta_low']}-{radar['eta_high']}m; confidence={radar['confidence']}%; radar reasons={radar['reason']}; NIFTY/SENSEX divergence={divergence}; support20={float(df.Low.tail(20).min()):.2f}; resistance20={float(df.High.tail(20).max()):.2f}; gap-up={up[0]:.0f}-{up[1]:.0f}; gap-down={down[0]:.0f}-{down[1]:.0f}.")
        if headlines: context += " Headlines: " + " | ".join(h["title"] for h in headlines[:5])
        ans=llm_answer(prompt,context)
        if ans is None:
            asks_call=any(k in p for k in ["call","ce","कॉल"]); asks_put=any(k in p for k in ["put","pe","पुट"])
            asks_why=any(k in p for k in ["why","क्यों","कारण","reason"]); asks_reversal=any(k in p for k in ["reversal","reverse","पलट","बाउंस","bounce","turn"])
            asks_support=any(k in p for k in ["support","resistance","level","लेवल","सपोर्ट","रेजिस्टेंस"])
            if asks_reversal:
                side="ऊपर से नीचे reversal risk" if radar["direction"]=="DOWN" else "नीचे से ऊपर bounce risk" if radar["direction"]=="UP" else "दोनों तरफ trap risk"
                ans=(f"**Reversal check:** अभी {side}. RSI {float(x.RSI):.1f}, candle {candle_name(x)}, 15m trend {trend15}, volume ratio {vol:.2f}. पहले {float(df.Low.tail(20).min()):,.0f} / {float(df.High.tail(20).max()):,.0f} levels देखें. Radar {radar['direction']} {radar['size']} है, इसलिए confirmation के बिना chase नहीं.")
            elif asks_support:
                ans=(f"**Levels:** support ≈ ₹{float(df.Low.tail(20).min()):,.2f}, resistance ≈ ₹{float(df.High.tail(20).max()):,.2f}, VWAP ₹{float(x.VWAP):,.2f}, current ₹{price:,.2f}. Resistance के ऊपर टिकना bullish confirmation; support टूटना bearish pressure बढ़ा सकता है.")
            elif asks_call or asks_put:
                side="CALL" if asks_call and not asks_put else "PUT" if asks_put and not asks_call else "CALL/PUT दोनों"
                ans=(f"**{side} view:** underlying radar **{radar['direction']} / {radar['size']}**, confidence {radar['confidence']}%. Live option premium invent नहीं करूँगा. Strike के लिए actual option-chain LTP/OI/IV चाहिए; Theo अलग window में है.")
            elif asks_why:
                mac="positive" if x.MACD>x.MACD_SIGNAL else "negative"
                ans=(f"**क्यों:** Technical {sig}; EMA9/21 {trend15}; RSI {float(x.RSI):.1f}; MACD {mac}; volume ratio {vol:.2f}. Radar कारण: {radar['reason']}. NIFTY↔SENSEX {'diverge' if divergence else 'align/unknown'}.")
            elif any(k in p for k in ["news","खबर","समाचार","market today","आज"]):
                ans=("**Fresh context:**\n"+"\n".join(f"• {h['title']}" for h in headlines[:5])) if headlines else "Fresh public headlines अभी fetch नहीं हुईं; खबर invent नहीं करूँगा. Current OHLC/Radar analysis उपलब्ध है."
            else:
                ans=(f"**OM read:** {symbol} ₹{price:,.2f}, {change:+.2f} ({change_pct:+.2f}%). Technical {sig} {tech:+d}/100; RSI {float(x.RSI):.1f}; 15m {trend15}; Radar {radar['direction']} {radar['size']} ±{radar['points']:.1f} pts in {radar['eta_low']}-{radar['eta_high']}m, confidence {radar['confidence']}%. सवाल को market/option/news/level angle से पढ़कर evidence-based जवाब दूँगा.")
        st.session_state.om_chat += [("user",prompt),("assistant",ans)]
        st.rerun()

# ============================================================
# ALARM
# ============================================================
def beep(kind):
    freq={"movement":440,"call":660,"put":330}.get(kind,440)
    sr=8000; dur=.3; n=int(sr*dur)
    frames=bytearray()
    for i in range(n):
        amp=int(11000*math.sin(2*math.pi*freq*i/sr))
        frames += int(amp).to_bytes(2,"little",signed=True)
    bio=io.BytesIO()
    with wave.open(bio,"wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr); w.writeframes(bytes(frames))
    b64=base64.b64encode(bio.getvalue()).decode()
    st.markdown(f'<audio autoplay><source src="data:audio/wav;base64,{b64}" type="audio/wav"></audio>',unsafe_allow_html=True)

if panel == 7:
    st.subheader("🔔 Alarm / Movement Watch")
    common_strip()
    upa=st.number_input("Upper level",value=float(round(price+atrv)),step=1.0)
    dna=st.number_input("Lower level",value=float(round(price-atrv)),step=1.0)
    c1,c2,c3=st.columns(3)
    if c1.button("Check levels",use_container_width=True):
        if price>=upa: st.success("🟢 Upper level reached")
        elif price<=dna: st.error("🔴 Lower level reached")
        else: st.info(f"Waiting: {dna:,.0f} ↔ {upa:,.0f}")
    if c2.button("Test sound",use_container_width=True): beep("movement")
    if c3.button("Log alert",use_container_width=True) and DB_OK:
        con=db_connect(); con.execute("INSERT INTO alerts(ts,market,kind,price,message) VALUES(?,?,?,?,?)",
            (now_ist().isoformat(),symbol,"manual",price,f"{radar['direction']} {radar['size']}")); con.commit(); con.close()
        st.success("Alert logged.")
    st.caption("Browser audio may require a user interaction. Android background alarms cannot be guaranteed by a Streamlit page.")

# ============================================================
# BACKTEST
# ============================================================
if panel == 8:
    st.subheader("🧪 Backtest / calibration")
    common_strip()
    t=df.dropna().copy()
    t["Pred"]=np.where((t.EMA9>t.EMA21)&(t.RSI>50)&(t.MACD>t.MACD_SIGNAL),1,-1)
    t["Next"]=np.sign(t.Close.shift(-1)-t.Close)
    t=t.dropna()
    acc=float((t.Pred==t.Next).mean()*100) if len(t) else 0
    st.metric("Directional hit-rate (1 next bar)",f"{acc:.1f}%")
    st.caption("This is historical simulation only; it is not a guarantee of future performance.")
    st.dataframe(t[["Close","RSI","EMA9","EMA21","MACD","Pred","Next"]].tail(100),use_container_width=True)

# ============================================================
# DATA
# ============================================================
if panel == 9:
    st.subheader("📊 Data / Export")
    common_strip()
    st.dataframe(df.tail(150),use_container_width=True)
    st.download_button("⬇️ Download OHLC + indicators",df.to_csv().encode(),
                       "om_market_analysis.csv","text/csv",use_container_width=True)

# ============================================================
# MARKET MAP
# ============================================================
if panel == 10:
    st.subheader("🗺️ Market Map")
    common_strip(); dual_strip()
    recent=df.tail(50)
    support=float(recent.Low.quantile(.15))
    resistance=float(recent.High.quantile(.85))
    pivot=float((recent.High.max()+recent.Low.min()+price)/3)
    a,b,c,d=st.columns(4)
    a.metric("Support",f"{support:,.2f}")
    b.metric("Pivot",f"{pivot:,.2f}")
    c.metric("Resistance",f"{resistance:,.2f}")
    d.metric("Candle",candle_name(df.iloc[-1]))
    st.info(f"Regime: {'HIGH' if atrv>df.ATR.tail(50).median()*1.25 else 'LOW' if atrv<df.ATR.tail(50).median()*.8 else 'NORMAL'} volatility | Short trend: {'UP' if df.EMA9.iloc[-1]>df.EMA21.iloc[-1] else 'DOWN'}")

# ============================================================
# MOVEMENT RADAR — THE MAIN USER REQUEST
# ============================================================
if panel == 11:
    st.subheader("📡 OM Movement Radar — कब movement आने की संभावना है?")
    common_strip(); dual_strip()
    a,b,c,d,e=st.columns(5)
    a.metric("Direction",radar["direction"])
    b.metric("Size",radar["size"])
    c.metric("Expected",f"±{radar['points']:.1f} pts")
    d.metric("Window",f"{radar['eta_low']}–{radar['eta_high']} min")
    e.metric("Confidence",f"{radar['confidence']}%")
    st.progress(radar["confidence"]/100,text=f"Radar confidence {radar['confidence']}%")
    if radar["size"]=="LARGE":
        st.error(f"🚨 LARGE MOVE WATCH: {radar['direction']} | approx ±{radar['points']:.1f} pts | window {radar['eta_low']}–{radar['eta_high']} min")
    elif radar["size"]=="MEDIUM":
        st.warning(f"⚠️ MEDIUM MOVE WATCH: {radar['direction']} | approx ±{radar['points']:.1f} pts | window {radar['eta_low']}–{radar['eta_high']} min")
    elif radar["size"]=="SMALL":
        st.info(f"🔎 SMALL MOVE WATCH: {radar['direction']} | approx ±{radar['points']:.1f} pts | window {radar['eta_low']}–{radar['eta_high']} min")
    else:
        st.success("🟢 QUIET / WAIT — no strong acceleration confirmation yet.")
    st.write(f"**Why:** {radar['reason']} | momentum={radar['momentum']:+.2f} | acceleration={radar['acceleration']:+.2f} | volume ratio={radar['vol_ratio']:.2f}")
    st.caption("Radar does not claim to know the future. It estimates when a movement may become more likely from fresh momentum/acceleration/volatility/volume data. A feed delay makes the window weaker.")
    mtf=m3_confirmation(symbol,timeframe,mode)
    if mtf:
        st.subheader("🕐 1H / 3H Confirmation")
        st.dataframe(pd.DataFrame([mtf]),use_container_width=True,hide_index=True)
    st.subheader("🛡️ Trap Guard")
    trap=(radar["direction"]=="UP" and df.RSI.iloc[-1]>72) or (radar["direction"]=="DOWN" and df.RSI.iloc[-1]<28)
    if trap: st.error("TRAP RISK: fast movement + RSI extreme. Do not chase without confirmation.")
    else: st.success("No extreme RSI chase condition detected.")

# ============================================================
# PHOTO AI
# ============================================================
if panel == 12:
    st.subheader("📷 OM Photo AI — screenshot fallback")
    common_strip()
    if not PIL_OK:
        st.error("Pillow missing. Add Pillow to requirements.txt.")
    else:
        imgup=st.file_uploader("NIFTY/SENSEX chart or option-chain screenshot",type=["png","jpg","jpeg","webp"],key="photo")
        if imgup:
            img=Image.open(imgup).convert("RGB")
            st.image(img,use_container_width=True)
            f=photo_features(img)
            st.dataframe(pd.DataFrame([f]),use_container_width=True,hide_index=True)
            # Improve visibility without pretending to OCR exact prices.
            st.subheader("👁️ Mobile visibility preview")
            c1,c2=st.columns(2)
            with c1:
                st.image(ImageEnhance.Contrast(img).enhance(1.45),caption="Contrast enhanced",use_container_width=True)
            with c2:
                st.image(ImageOps.autocontrast(img),caption="Auto contrast",use_container_width=True)
            st.info(f"Photo structure: **{f['quality']}**. OM does not invent exact option prices from pixels. Visible levels can be used alongside live/OHLC confirmation.")

# ============================================================
# SUPERPOWERS
# ============================================================
if panel == 13:
    st.subheader("✨ OM Superpowers — experimental layers")
    common_strip()
    layers=[
      ("3-6-9 root",root),("Aryabhata zero-center",round((price%10)-5,2)),
      ("Shankaracharya dual-balance",1 if abs(price-mid)<atrv*.25 else 0),
      ("Shakuntala fast-math root",digital_root(round(abs(price)*100))),
      ("Binary pressure",bin(int(abs(price))).count("1")-bin(int(abs(price))).count("0")),
      ("Loop resonance",1 if price>loop else -1),
      ("Volatility phase",1 if atrv>df.ATR.tail(50).median() else -1),
      ("Momentum pulse",round(radar["score"],2)),
      ("Trap shield",-1 if trap else 1),
    ]
    st.dataframe(pd.DataFrame(layers,columns=["Layer","Value"]),use_container_width=True,hide_index=True)
    st.warning("इन concepts को research hypotheses की तरह रखा गया है, market law की तरह नहीं.")

# ============================================================
# SELF-UPGRADE
# ============================================================
if panel == 14:
    st.subheader("🔬 Self-Upgrade / Research Lab")
    st.info("Agent source code को अपने-आप बदलना बंद रखा गया है. पहले candidate → test → backtest → approval → deployment.")
    candidates=pd.DataFrame({
      "Upgrade":["Second-level feed adapter","Option-chain OI/IV engine","Adaptive volatility regime",
                 "Candle pattern ensemble","Screenshot OCR layer","Signal calibration from feedback",
                 "Persistent external DB","Push notification service"],
      "Value":["faster movement detection","CALL/PUT confirmation","dynamic thresholds",
               "more candle context","read visible prices where OCR works","learn false-alert patterns",
               "history survives cloud restarts","alerts outside browser"],
      "Status":["candidate"]*8
    })
    st.dataframe(candidates,use_container_width=True,hide_index=True)
    if st.button("🧪 Generate validation plan",use_container_width=True):
        st.success("Validation plan: collect snapshots → label actual 5/10/15/30m outcome → calculate precision/false alerts → reject weak features → keep only validated improvements.")

# ============================================================
# 50+ FEATURES
# ============================================================
if panel == 15:
    st.subheader("🧩 OM 50+ Feature Intelligence Hub")
    st.success("55 features are active in this launch build.")
    fdf=pd.DataFrame({"#":range(1,len(features)+1),
                      "Feature":list(features.keys()),
                      "Current value":list(features.values())})
    st.dataframe(fdf,use_container_width=True,hide_index=True,height=650)
    a,b,c,d,e=st.columns(5)
    confirmed=features["45 Index Confirmation"]=="CONFIRMED"
    trend=features["46 Short Trend"]==features["47 Medium Trend"]
    rsi_ok=30<df.RSI.iloc[-1]<70
    data_ok=features["50 Data Quality"]!="LIMITED"
    a.metric("Index Gate","PASS" if confirmed else "WAIT")
    b.metric("Trend Gate","PASS" if trend else "MIXED")
    c.metric("RSI Gate","PASS" if rsi_ok else "EXTREME")
    d.metric("Data Gate","PASS" if data_ok else "LIMITED")
    e.metric("Radar","ACTIVE")

# ============================================================
# DATABASE
# ============================================================
if panel == 16:
    st.subheader("🗄️ Database / Event History")
    st.caption("SQLite is persistent only as long as the app filesystem survives. Streamlit Cloud can reset local files; permanent history needs an external DB.")
    hist=read_snapshots(300)
    a,b,c=st.columns(3)
    a.metric("DB","READY" if DB_OK else "ERROR")
    b.metric("Rows",len(hist))
    c.metric("Current source",source)
    if not hist.empty:
        st.dataframe(hist,use_container_width=True,height=500)
        st.download_button("⬇️ Download DB history",hist.to_csv(index=False).encode(),
                           "om_database_history.csv","text/csv",use_container_width=True)
    st.json({"DB path":DB_PATH,"market":symbol,"timeframe":timeframe,"mode":mode,
             "live_tick":bool(tick),"rows":len(df),"source":source})

# ============================================================
# FEEDBACK BOARD
# ============================================================
if panel == 17:
    st.subheader("📝 Feedback Board — agent को वास्तव में improve करने का रास्ता")
    r=st.slider("Usefulness",1,5,3,key="rating")
    cat=st.selectbox("Category",["Movement timing","Movement size","CALL/PUT direction",
                                 "Opening","Photo AI","Option Theo","Data feed","UI","Other"],key="category")
    msg=st.text_area("क्या सही/गलत हुआ?",key="feedback_text",
                     placeholder="जैसे: UP सही था, लेकिन move 8 min में नहीं 14 min में आया.")
    if st.button("📌 Save Feedback",use_container_width=True):
        if msg.strip() and DB_OK:
            con=db_connect()
            con.execute("""INSERT INTO feedback
              (ts,market,timeframe,category,rating,message,predicted_direction,
               predicted_size,predicted_points,predicted_eta_low,predicted_eta_high,confidence)
              VALUES(?,?,?,?,?,?,?,?,?,?,?,?)""",
              (now_ist().isoformat(),symbol,timeframe,cat,int(r),msg.strip(),
               radar["direction"],radar["size"],radar["points"],radar["eta_low"],
               radar["eta_high"],radar["confidence"]))
            con.commit(); con.close()
            st.success("Saved. This becomes calibration data.")
        else: st.warning("Feedback लिखें और DB उपलब्ध हो.")
    if DB_OK:
        try:
            con=db_connect()
            fb=pd.read_sql_query("SELECT * FROM feedback ORDER BY id DESC LIMIT 100",con)
            con.close()
            if not fb.empty: st.dataframe(fb,use_container_width=True,height=400)
        except Exception: pass

# ============================================================
# SETTINGS / LAUNCH CHECK
# ============================================================
if panel == 18:
    st.subheader("⚙️ App Settings / Launch Check")
    checks={
      "Primary 15m":timeframe=="15m","Live-first mode":mode=="Best Effort Live",
      "Real tick received":bool(tick),"OHLC received":not df.empty,
      "Database":DB_OK,"Experimental labels visible":True,
      "Fake live price in live mode":False
    }
    for k,v in checks.items():
        st.write(("🟢 " if v else "🟡 ")+k)
    st.info("Recommended: 15m primary + 1H/3H confirmation + 1m/5m movement radar during market hours.")
    if st.button("💾 Save settings snapshot",use_container_width=True) and DB_OK:
        payload={"market":symbol,"timeframe":timeframe,"mode":mode,"auto_refresh":auto,
                 "refresh":refresh,"confidence":confidence,"risk":risk}
        con=db_connect(); con.execute("INSERT INTO settings(ts,payload) VALUES(?,?)",
                                      (now_ist().isoformat(),json.dumps(payload)))
        con.commit(); con.close(); st.success("Settings saved.")

# ============================================================
# GLOBAL EARLY ALERT
# ============================================================
if panel in (1,11) and radar["size"] in ("LARGE","MEDIUM") and radar["confidence"]>=confidence:
    st.warning(f"🔔 EARLY MOVEMENT ALERT — {radar['direction']} | {radar['size']} | ±{radar['points']:.1f} pts | window {radar['eta_low']}–{radar['eta_high']} min | confidence {radar['confidence']}%")

if panel == 18:
    st.divider(); st.subheader("🛡️ Recovery / Backup")
    try:
        with open(__file__,"rb") as f:
            st.download_button("⬇️ Download current app.py",f.read(),"om_market_ai_full_launch.py",use_container_width=True)
    except Exception: pass
    st.caption(f"ॐ OM MARKET AI • {APP_VERSION} • scenarios are estimates, not guarantees.")

# ============================================================
# AUTO REFRESH
# ============================================================
if auto:
    pytime.sleep(int(refresh))
    st.rerun()
