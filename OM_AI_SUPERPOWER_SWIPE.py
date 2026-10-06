
# ============================================================
# OM AI AGENT — DYNAMIC MOVEMENT TRACKER PATCH
# Replace ONLY the old fixed "10 point" movement-tracker logic.
# Keep all other OM AI Agent features unchanged.
# ============================================================

import numpy as np
import pandas as pd

def _num(v, default=np.nan):
    try:
        return float(v)
    except Exception:
        return default


def _atr(df, n=14):
    h = pd.to_numeric(df["High"], errors="coerce")
    l = pd.to_numeric(df["Low"], errors="coerce")
    c = pd.to_numeric(df["Close"], errors="coerce")
    prev = c.shift(1)
    tr = pd.concat([
        h - l,
        (h - prev).abs(),
        (l - prev).abs()
    ], axis=1).max(axis=1)
    return tr.rolling(n, min_periods=max(5, n // 2)).mean()


def om_dynamic_movement(df, symbol="^NSEI"):
    """
    Dynamic movement detector.

    IMPORTANT:
    - No fixed 10-point trigger.
    - Uses ATR + candle expansion + momentum + acceleration +
      breakout + EMA slope.
    - Detects a move after it starts and can warn during acceleration.
    - It does NOT claim to predict a guaranteed future move.
    """
    out = {
        "status": "WAIT",
        "side": "NEUTRAL",
        "confidence": 0,
        "move_now": 0.0,
        "velocity": 0.0,
        "acceleration": 0.0,
        "atr": 0.0,
        "range_ratio": 1.0,
        "score": 0,
        "warning": "Waiting for live candles",
        "reason": "",
        "small": "",
        "medium": "",
        "large": "",
        "breakout": "NONE",
    }

    if df is None or len(df) < 25:
        return out

    x = df.copy()

    # Accept both normal OHLC and yfinance MultiIndex columns.
    if isinstance(x.columns, pd.MultiIndex):
        x.columns = [c[0] if isinstance(c, tuple) else c for c in x.columns]

    required = {"Open", "High", "Low", "Close"}
    if not required.issubset(set(x.columns)):
        return out

    for col in ["Open", "High", "Low", "Close", "Volume"]:
        if col in x.columns:
            x[col] = pd.to_numeric(x[col], errors="coerce")

    x = x.dropna(subset=["Open", "High", "Low", "Close"]).copy()
    if len(x) < 25:
        return out

    close = x["Close"]
    high = x["High"]
    low = x["Low"]

    x["ATR"] = _atr(x, 14)
    x["EMA9"] = close.ewm(span=9, adjust=False).mean()
    x["EMA21"] = close.ewm(span=21, adjust=False).mean()

    x["range"] = high - low
    x["body"] = (close - x["Open"]).abs()
    x["ret"] = close.diff()
    x["velocity"] = close.diff(3)
    x["accel"] = x["velocity"].diff(2)

    range_med = x["range"].rolling(20).median()
    ret_std = x["ret"].rolling(20).std()

    last = x.iloc[-1]
    prev = x.iloc[-2]
    p3 = x.iloc[-4]

    price = _num(last["Close"], 0)
    atr = _num(last["ATR"], 0)
    if not np.isfinite(atr) or atr <= 0:
        atr = _num(x["range"].rolling(14).mean().iloc[-1], 1)

    rmed = _num(range_med.iloc[-1], atr)
    if not np.isfinite(rmed) or rmed <= 0:
        rmed = max(atr, 1.0)

    rng = _num(last["range"], 0)
    body = _num(last["body"], 0)
    velocity = _num(last["velocity"], 0)
    accel = _num(last["accel"], 0)

    # Current move from the recent local base, not a fixed 10 points.
    lookback = min(12, len(x) - 1)
    base = _num(close.iloc[-lookback-1], price)
    move_now = price - base

    # Candle expansion: catches "market suddenly woke up".
    range_ratio = rng / max(rmed, 0.01)

    # EMA slope normalized by ATR.
    ema_slope = _num(x["EMA9"].iloc[-1] - x["EMA9"].iloc[-4], 0) / max(atr, 0.01)
    ema_gap = _num(x["EMA9"].iloc[-1] - x["EMA21"].iloc[-1], 0) / max(atr, 0.01)

    # Breakout from recent 8 candles.
    prev_high = _num(high.iloc[-9:-1].max(), price)
    prev_low = _num(low.iloc[-9:-1].min(), price)

    breakout_up = price > prev_high
    breakout_down = price < prev_low

    # Direction from multi-factor evidence.
    score = 0.0

    if move_now > 0:
        score += 2
    elif move_now < 0:
        score -= 2

    if velocity > atr * 0.18:
        score += 2
    elif velocity < -atr * 0.18:
        score -= 2

    if accel > atr * 0.08:
        score += 2
    elif accel < -atr * 0.08:
        score -= 2

    if ema_slope > 0.10:
        score += 2
    elif ema_slope < -0.10:
        score -= 2

    if ema_gap > 0.10:
        score += 1
    elif ema_gap < -0.10:
        score -= 1

    if breakout_up:
        score += 3
    if breakout_down:
        score -= 3

    # Large candle expansion is a warning, not a direction by itself.
    if range_ratio >= 1.8:
        score += 1 if body > 0 and last["Close"] > last["Open"] else 0
        score -= 1 if body > 0 and last["Close"] < last["Open"] else 0

    side = "UP" if score >= 3 else "DOWN" if score <= -3 else "NEUTRAL"

    # Confidence is based on independent evidence.
    evidence = 0
    if abs(move_now) >= atr * 0.20:
        evidence += 1
    if abs(velocity) >= atr * 0.18:
        evidence += 1
    if abs(accel) >= atr * 0.08:
        evidence += 1
    if abs(ema_slope) >= 0.10:
        evidence += 1
    if breakout_up or breakout_down:
        evidence += 1
    if range_ratio >= 1.5:
        evidence += 1

    confidence = min(95, 35 + evidence * 10 + min(20, abs(score) * 3))

    # Early warning states:
    # IGNITION = movement is starting
    # ACTIVE   = movement is already expanding
    # HEAVY    = unusually large/fast movement
    norm_move = abs(move_now) / max(atr, 0.01)
    norm_vel = abs(velocity) / max(atr, 0.01)

    if range_ratio >= 2.2 or norm_vel >= 0.90 or norm_move >= 1.25:
        status = "HEAVY"
    elif range_ratio >= 1.45 or norm_vel >= 0.45 or norm_move >= 0.55 or abs(score) >= 7:
        status = "ACTIVE"
    elif abs(score) >= 3 or norm_vel >= 0.20 or abs(accel) >= atr * 0.08:
        status = "IGNITION"
    else:
        status = "WAIT"

    # Dynamic expected movement bands.
    # These are estimates from current volatility, not guarantees.
    small = max(atr * 0.25, rmed * 0.80)
    medium = max(atr * 0.55, rmed * 1.50)
    large = max(atr * 0.95, rmed * 2.20)

    # For SENSEX, points are naturally larger; do NOT use a NIFTY
    # 10-point threshold on it.
    sym = str(symbol).upper()
    index_name = "SENSEX" if ("BSESN" in sym or "SENSEX" in sym) else "NIFTY"

    # Very fast expansion multiplier for the displayed "potential".
    expansion = 1.0
    if range_ratio >= 1.5:
        expansion += 0.25
    if range_ratio >= 2.0:
        expansion += 0.35
    if abs(accel) >= atr * 0.15:
        expansion += 0.20

    small *= expansion
    medium *= expansion
    large *= expansion

    if side == "UP":
        arrow = "↑"
    elif side == "DOWN":
        arrow = "↓"
    else:
        arrow = "→"

    if status == "HEAVY":
        warning = f"HEAVY {arrow} — fast expansion detected"
    elif status == "ACTIVE":
        warning = f"ACTIVE {arrow} — movement expanding"
    elif status == "IGNITION":
        warning = f"IGNITION {arrow} — early movement detected"
    else:
        warning = "WAIT — no strong expansion yet"

    reasons = []
    if breakout_up:
        reasons.append("recent-high breakout")
    elif breakout_down:
        reasons.append("recent-low breakdown")
    if range_ratio >= 1.5:
        reasons.append(f"candle range {range_ratio:.1f}x normal")
    if abs(accel) >= atr * 0.08:
        reasons.append("acceleration")
    if abs(ema_slope) >= 0.10:
        reasons.append("EMA slope")
    if abs(velocity) >= atr * 0.20:
        reasons.append("momentum")

    out.update({
        "status": status,
        "side": side,
        "confidence": int(confidence),
        "move_now": float(move_now),
        "velocity": float(velocity),
        "acceleration": float(accel),
        "atr": float(atr),
        "range_ratio": float(range_ratio),
        "score": int(round(score)),
        "warning": warning,
        "reason": ", ".join(reasons) if reasons else "mixed / low expansion",
        "small": f"{small:.1f} pts",
        "medium": f"{medium:.1f} pts",
        "large": f"{large:.1f} pts",
        "breakout": "UP" if breakout_up else "DOWN" if breakout_down else "NONE",
        "index": index_name,
    })

    return out


# ============================================================
# STREAMLIT PANEL
# Put this where the old Movement Tracker panel was.
# df MUST be the latest OHLC dataframe.
# ============================================================

def show_dynamic_movement_tracker(df, symbol):
    m = om_dynamic_movement(df, symbol)

    st.subheader("⚡ OM Dynamic Movement Tracker")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Status", m["status"])
    c2.metric("Side", m["side"])
    c3.metric("Confidence", f'{m["confidence"]}%')
    c4.metric("Move", f'{m["move_now"]:+.1f} pts')

    st.info(
        f'{m["warning"]}  |  {m["index"]}  |  '
        f'ATR: {m["atr"]:.1f}  |  '
        f'Range: {m["range_ratio"]:.1f}x  |  '
        f'Score: {m["score"]:+d}'
    )

    d1, d2, d3 = st.columns(3)
    d1.metric("Small expansion", m["small"])
    d2.metric("Medium expansion", m["medium"])
    d3.metric("Heavy expansion", m["large"])

    st.caption(
        "Reason: " + m["reason"] +
        " | Breakout: " + m["breakout"] +
        " | Dynamic volatility model — not a guaranteed prediction."
    )


# ============================================================
# IMPORTANT INTEGRATION NOTES
# ============================================================
#
# 1) Remove/stop using the OLD logic like:
#       if abs(price - previous_price) >= 10:
#           ...
#
# 2) Do NOT calculate movement direction from only:
#       price + 10 / price - 10
#
# 3) Call:
#       movement = om_dynamic_movement(df, symbol)
#
#    and show:
#       show_dynamic_movement_tracker(df, symbol)
#
# 4) For best live detection, feed this function 1-minute OHLC
#    when available. If 1m is unavailable, use 5m data.
#
# 5) The tracker now reacts to:
#       - ATR-normalized movement
#       - candle range expansion
#       - 3-candle velocity
#       - acceleration
#       - EMA9 slope / EMA9-EMA21 gap
#       - recent high/low breakout
#
# 6) This means a 10-point NIFTY move is NOT treated as a
#    universal trigger. A quiet market and a fast market get
#    different thresholds.
#
# 7) "HEAVY" means abnormal expansion is already visible.
#    "IGNITION" is the early-warning state.
#
# 8) This patch does not guarantee that the tracker will predict
#    a 400-point move before it happens. Its job is to detect the
#    acceleration early instead of waiting for an arbitrary
#    fixed 10-point threshold.
