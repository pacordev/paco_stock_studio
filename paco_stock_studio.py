"""
paco_stock_studio.py — stock analyzer with buy/skip and hold-duration recommendations. Intended for a unique ticket at the time.

how to use this file:
    python3 paco_stock_studio.py AAPL       # analyze one stock with a default 2-year retroactive info
    python3 paco_stock_studio.py AAPL --period 2y   # execute with a specific retroactive info period
    python3 paco_stock_studio.py            # prompts for ticker

Install libraries used:
pip3 install yfinance pandas tabulate

Important Note:
This script is intended for testing and educational purposes only — This is not financial advice at all.
"""

import sys
import argparse
import warnings
from datetime import date
import yfinance as yf
import pandas as pd
import numpy as np
from tabulate import tabulate

warnings.filterwarnings("ignore")

# ── Global constants ──────────────────────────────────────────────────────────
# RISK_FREE_RATE is subtracted from the annualized return when computing Sharpe,
# representing what you'd earn in a risk-free instrument.
RISK_FREE_RATE = 0.045
BENCHMARK      = "SPY"   # index used as a market reference for relative comparison

# ── Buy/Skip model weights ────────────────────────────────────────────────────
# Each key maps to the percentage contribution that signal has in the composite
# buy/skip score.  Values must sum to 100.
WEIGHTS = {
    "rsi":          15,   # momentum oscillator — measures recent price velocity
    "ma_trend":     15,   # price position relative to 50-day and 200-day SMAs
    "macd":         10,   # MACD crossover — short vs long EMA divergence
    "golden_cross": 10,   # structural trend: 50-SMA above/below 200-SMA
    "momentum":     15,   # raw 1M / 3M / 6M price returns
    "sharpe":       15,   # risk-adjusted return quality over the lookback period
    "drawdown":     10,   # penalty for historically deep peak-to-trough drops
    "volume":       10,   # on-balance volume trend (accumulation vs distribution)
}

# ── Hold-duration model weights ───────────────────────────────────────────────
# Separate set of weights for the long/medium/short hold recommendation.
# Higher composite score = longer recommended hold.
_HOLD_WEIGHTS = {
    "volatility":  20,   # low vol stocks tolerate long holds better
    "beta":        15,   # high beta = amplified market moves, suits shorter cycles
    "sharpe":      20,   # strong risk-adjusted return justifies holding longer
    "drawdown":    15,   # frequent deep drops shorten the safe holding window
    "trend":       15,   # aligned SMA uptrend supports extended commitment
    "momentum":    15,   # consistent multi-timeframe gains indicate a durable move
}


# ══════════════════════════════════════════════════════════════════════════════
# TECHNICAL INDICATOR FUNCTIONS
# Each returns a pd.Series aligned to the input price series.
# ══════════════════════════════════════════════════════════════════════════════

def compute_rsi(series: pd.Series, period: int = 14) -> pd.Series:
    # RSI measures the speed and magnitude of recent price changes.
    # Values above 70 suggest overbought conditions; below 30 suggests oversold.
    delta = series.diff()
    gain  = delta.clip(lower=0).rolling(period).mean()   # average up-moves
    loss  = (-delta.clip(upper=0)).rolling(period).mean() # average down-moves
    rs    = gain / loss.replace(0, np.nan)               # relative strength ratio
    return 100 - (100 / (1 + rs))


def compute_macd(series: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9):
    # MACD captures the convergence/divergence of two exponential moving averages.
    # The histogram shows the gap between MACD and its signal line —
    # expanding histogram = accelerating momentum in that direction.
    ema_fast    = series.ewm(span=fast,   adjust=False).mean()
    ema_slow    = series.ewm(span=slow,   adjust=False).mean()
    macd_line   = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    histogram   = macd_line - signal_line
    return macd_line, signal_line, histogram


def compute_bollinger(series: pd.Series, period: int = 20, std: float = 2.0):
    # Bollinger Bands place an upper and lower envelope 2 standard deviations
    # around a rolling mean.  Price touching the lower band often signals
    # oversold conditions; touching the upper band signals overbought.
    mid  = series.rolling(period).mean()
    band = series.rolling(period).std()
    return mid - std * band, mid, mid + std * band


# ══════════════════════════════════════════════════════════════════════════════
# CORE STATISTICAL METRICS
# ══════════════════════════════════════════════════════════════════════════════

def annualized_return(total_return: float, days: int) -> float:
    # Converts a raw total return over N calendar days into a per-year figure
    # using the compound annual growth rate formula.
    return (1 + total_return) ** (365 / max(days, 1)) - 1


def annualized_volatility(daily_returns: pd.Series) -> float:
    # Scales daily standard deviation to an annual figure.
    # 252 is the conventional number of trading days per year.
    return daily_returns.std() * (252 ** 0.5)


def sharpe_ratio(ann_return: float, ann_vol: float) -> float:
    # Excess return per unit of risk.  Values above 1.0 are generally considered
    # good; above 1.5 is excellent.
    return (ann_return - RISK_FREE_RATE) / ann_vol if ann_vol else float("nan")


def max_drawdown(prices: pd.Series) -> float:
    # Largest percentage drop from any historical peak to the subsequent trough.
    # A value of -0.35 means the stock fell 35% from its high at its worst point.
    return ((prices - prices.cummax()) / prices.cummax()).min()


def momentum_return(prices: pd.Series, days: int) -> float | None:
    # Simple price return over the last N trading days.
    # Returns None when the history is shorter than the requested window.
    if len(prices) < days:
        return None
    return prices.iloc[-1] / prices.iloc[-days] - 1


# ══════════════════════════════════════════════════════════════════════════════
# BUY/SKIP SCORING FUNCTIONS
# Each returns (score_0_to_1, human_readable_detail_string).
# A score of 1.0 is maximally bullish; 0.0 is maximally bearish.
# ══════════════════════════════════════════════════════════════════════════════

def score_rsi(rsi: float) -> tuple[float, str]:
    # Deeply oversold RSI is a buy signal (mean-reversion potential).
    # Overbought RSI warns that a pullback may be near.
    if rsi < 25:
        return 1.0,  f"RSI {rsi:.1f} — deeply oversold (strong buy signal)"
    if rsi < 40:
        return 0.8,  f"RSI {rsi:.1f} — oversold (bullish)"
    if rsi < 55:
        return 0.6,  f"RSI {rsi:.1f} — neutral"
    if rsi < 70:
        return 0.35, f"RSI {rsi:.1f} — overbought territory (caution)"
    return 0.1,      f"RSI {rsi:.1f} — strongly overbought (bearish)"


def score_ma_trend(price: float, sma50: float, sma200: float) -> tuple[float, str]:
    # Price above both SMAs = healthy uptrend.
    # A very wide gap above the 200-SMA often signals the stock is overextended
    # and due for a reversion, so we apply a small penalty there.
    above_50  = price > sma50
    above_200 = price > sma200
    if above_50 and above_200:
        gap = (price - sma200) / sma200 * 100
        if gap > 30:                        # overextended — trim score slightly
            return 0.55, f"Price above both SMAs but extended +{gap:.1f}% above 200-SMA"
        return 0.9, f"Price above both 50-SMA & 200-SMA (+{gap:.1f}% above 200-SMA)"
    if above_200 and not above_50:
        return 0.5,  "Price below 50-SMA but above 200-SMA (pullback within uptrend)"
    if above_50 and not above_200:
        return 0.45, "Price above 50-SMA but below 200-SMA (recovering, uncertain)"
    return 0.15,     "Price below both 50-SMA & 200-SMA (downtrend)"


def score_macd(macd: float, signal: float, histogram: pd.Series) -> tuple[float, str]:
    # MACD above its signal line = bullish bias.
    # An expanding histogram (today's bar taller than yesterday's) means the
    # bullish or bearish momentum is still accelerating.
    if macd > signal and histogram.iloc[-1] > histogram.iloc[-2]:
        return 0.9,  "MACD above signal and histogram expanding (bullish momentum)"
    if macd > signal:
        return 0.65, "MACD above signal line (mildly bullish)"
    if macd < signal and histogram.iloc[-1] < histogram.iloc[-2]:
        return 0.15, "MACD below signal and histogram contracting (bearish momentum)"
    return 0.35,     "MACD below signal line (mildly bearish)"


def score_golden_cross(sma50: float, sma200: float) -> tuple[float, str]:
    # Golden cross (50-SMA crosses above 200-SMA) is a classic long-term
    # bullish signal; death cross is the bearish counterpart.
    ratio = sma50 / sma200
    if ratio >= 1.0:
        return 0.85, f"Golden cross: 50-SMA {ratio:.3f}× above 200-SMA"
    return 0.2,      f"Death cross: 50-SMA {ratio:.3f}× below 200-SMA"


def score_momentum(m1, m3, m6) -> tuple[float, str]:
    # Counts how many of the three time windows show positive returns.
    # A stock winning across all three windows has broad-based momentum.
    vals = [v for v in (m1, m3, m6) if v is not None]
    if not vals:
        return 0.5, "Insufficient history for momentum"
    positive = sum(1 for v in vals if v > 0)
    avg      = np.mean(vals) * 100
    score    = positive / len(vals)            # fraction of windows in the green
    parts    = []
    if m1 is not None: parts.append(f"1M {m1*100:+.1f}%")
    if m3 is not None: parts.append(f"3M {m3*100:+.1f}%")
    if m6 is not None: parts.append(f"6M {m6*100:+.1f}%")
    return score, f"Momentum: {', '.join(parts)} (avg {avg:+.1f}%)"


def score_sharpe(sharpe: float) -> tuple[float, str]:
    # Higher Sharpe = more return earned per unit of risk taken.
    # Scores decay quickly below 0.5 because poor risk-adjusted returns
    # suggest the gains may not justify the volatility experienced.
    if sharpe >= 1.5:
        return 1.0,  f"Sharpe {sharpe:.2f} — excellent risk-adjusted return"
    if sharpe >= 1.0:
        return 0.8,  f"Sharpe {sharpe:.2f} — good risk-adjusted return"
    if sharpe >= 0.5:
        return 0.6,  f"Sharpe {sharpe:.2f} — acceptable"
    if sharpe >= 0.0:
        return 0.35, f"Sharpe {sharpe:.2f} — poor risk-adjusted return"
    return 0.1,      f"Sharpe {sharpe:.2f} — negative risk-adjusted return"


def score_drawdown(mdd: float) -> tuple[float, str]:
    # A history of deep drawdowns signals higher tail risk — the stock has
    # crashed badly before and may do so again.
    if mdd >= -0.10:
        return 1.0,  f"Max drawdown {mdd*100:.1f}% — very low downside risk"
    if mdd >= -0.20:
        return 0.75, f"Max drawdown {mdd*100:.1f}% — moderate downside risk"
    if mdd >= -0.35:
        return 0.45, f"Max drawdown {mdd*100:.1f}% — significant drawdown history"
    return 0.15,     f"Max drawdown {mdd*100:.1f}% — high drawdown risk"


def score_volume(volume: pd.Series, price: pd.Series) -> tuple[float, str]:
    # On-Balance Volume (OBV) accumulates volume on up-days and subtracts it on
    # down-days.  A rising OBV trend means more volume is flowing in on advances
    # than on declines — a sign of institutional accumulation.
    obv     = (np.sign(price.diff()) * volume).fillna(0).cumsum()
    obv_sma = obv.rolling(20).mean()                # smooth OBV to reduce noise
    if len(obv_sma.dropna()) < 2:
        return 0.5, "Insufficient data for volume analysis"
    trend            = obv_sma.iloc[-1] > obv_sma.iloc[-20]   # OBV direction over last 20 days
    recent_vol_ratio = volume.iloc[-10:].mean() / volume.iloc[-60:-10].mean()   # recent vs baseline
    if trend and recent_vol_ratio > 1.1:
        return 0.85, f"OBV rising, recent volume {recent_vol_ratio:.1f}× avg (accumulation)"
    if trend:
        return 0.65, f"OBV rising but volume not expanding (mild bullish)"
    if recent_vol_ratio > 1.2:
        return 0.25, f"OBV falling with elevated volume {recent_vol_ratio:.1f}× (distribution)"
    return 0.4, "OBV declining (mild bearish volume signal)"


def compute_score(scores: dict[str, tuple[float, str]]) -> float:
    # Weighted average of all signal scores, expressed as a 0–100 number.
    total = sum(WEIGHTS[k] * scores[k][0] for k in WEIGHTS)
    return total / sum(WEIGHTS.values()) * 100


# ══════════════════════════════════════════════════════════════════════════════
# HOLD-DURATION MODEL
# Six sub-factors vote on how long it is reasonable to hold the stock.
# Composite score > 0.62 → LONG  |  0.42–0.62 → MEDIUM  |  < 0.42 → SHORT
# ══════════════════════════════════════════════════════════════════════════════

def _hold_score_volatility(ann_vol: float) -> tuple[float, str]:
    # High-volatility stocks swing widely day-to-day.  Holding them long-term
    # requires a stomach for large unrealised losses; shorter holds cut that risk.
    if ann_vol < 0.18:
        return 0.9,  f"Low volatility {ann_vol*100:.1f}% — stable, suits long hold"
    if ann_vol < 0.30:
        return 0.6,  f"Moderate volatility {ann_vol*100:.1f}% — medium hold tolerable"
    if ann_vol < 0.45:
        return 0.35, f"High volatility {ann_vol*100:.1f}% — shorter hold reduces risk"
    return 0.1,      f"Very high volatility {ann_vol*100:.1f}% — speculative, short-term only"


def _hold_score_beta(beta) -> tuple[float, str]:
    # Beta measures sensitivity to broad market moves.  A beta of 2 means the
    # stock typically moves twice as much as the market — great in bull runs,
    # painful in corrections, so shorter hold cycles limit exposure.
    if beta is None or str(beta) == "nan":
        return 0.5, "Beta unavailable — neutral"
    b = float(beta)
    if b < 0.8:
        return 0.9,  f"Beta {b:.2f} — defensive, suits long hold"
    if b < 1.2:
        return 0.65, f"Beta {b:.2f} — market-neutral, medium hold"
    if b < 1.8:
        return 0.4,  f"Beta {b:.2f} — above-market sensitivity, monitor closely"
    return 0.15,     f"Beta {b:.2f} — highly sensitive to market swings, short-term"


def _hold_score_sharpe(sharpe: float) -> tuple[float, str]:
    # A high Sharpe ratio means the stock has historically rewarded patience —
    # good returns relative to the pain of holding through its swings.
    if sharpe >= 1.5:
        return 1.0,  f"Sharpe {sharpe:.2f} — excellent reward/risk, strong long-hold case"
    if sharpe >= 1.0:
        return 0.75, f"Sharpe {sharpe:.2f} — good reward/risk, long hold supported"
    if sharpe >= 0.5:
        return 0.5,  f"Sharpe {sharpe:.2f} — marginal, medium hold preferable"
    if sharpe >= 0.0:
        return 0.25, f"Sharpe {sharpe:.2f} — poor reward/risk, shorter hold advised"
    return 0.05,     f"Sharpe {sharpe:.2f} — negative reward/risk, avoid extended exposure"


def _hold_score_drawdown(mdd: float) -> tuple[float, str]:
    # Stocks that have historically crashed 40%+ demand active monitoring;
    # a shorter hold horizon limits how much of a future drawdown you absorb.
    if mdd >= -0.12:
        return 0.9, f"Max drawdown {mdd*100:.1f}% — minimal downside history"
    if mdd >= -0.22:
        return 0.7, f"Max drawdown {mdd*100:.1f}% — manageable dips, long hold viable"
    if mdd >= -0.38:
        return 0.4, f"Max drawdown {mdd*100:.1f}% — deep drawdowns, medium hold safer"
    return 0.1,     f"Max drawdown {mdd*100:.1f}% — severe drawdowns, short hold only"


def _hold_score_trend(sma50: float, sma200: float, price: float) -> tuple[float, str]:
    # An aligned uptrend (price > 50-SMA > 200-SMA) means all three time horizons
    # agree the stock is moving up — the strongest structural case for a long hold.
    above_both = price > sma50 > sma200
    golden     = sma50 > sma200              # golden cross = long-term bullish structure
    if above_both and golden:
        return 0.9,  "Price > 50-SMA > 200-SMA — strong aligned uptrend, long hold"
    if golden and price > sma200:
        return 0.65, "Golden cross intact, price above 200-SMA — medium-long hold"
    if golden:
        return 0.45, "Golden cross but price pulling back — wait, medium hold"
    return 0.1,      "Death cross / price below 200-SMA — avoid long commitment"


def _hold_score_momentum(m1, m3, m6) -> tuple[float, str]:
    # Consistent positive momentum across all three windows signals a durable move
    # worth staying in.  A spike only in the 1M window suggests a short-term pop
    # rather than a sustained trend, favouring a shorter hold.
    vals      = [(m6, "6M"), (m3, "3M"), (m1, "1M")]
    available = [(v, lbl) for v, lbl in vals if v is not None]
    if not available:
        return 0.5, "Insufficient momentum data"
    parts    = [f"{lbl} {v*100:+.1f}%" for v, lbl in available]
    positive = sum(1 for v, _ in available if v > 0)
    # reward when the longer window (6M) leads the shorter window (1M) — steady climb
    long_leading = (m6 is not None and m1 is not None and m6 > 0 and abs(m6) >= abs(m1 or 0))
    score = positive / len(available)
    if score == 1.0 and long_leading:
        return 0.95, f"Consistent positive momentum: {', '.join(parts)} — long hold"
    if score >= 0.67:
        return 0.65, f"Mostly positive: {', '.join(parts)} — medium-long hold"
    if score == 0.5:
        return 0.45, f"Mixed signals: {', '.join(parts)} — medium hold"
    return 0.2,      f"Mostly negative: {', '.join(parts)} — short hold or stay out"


def hold_duration_analysis(ann_vol: float, beta, sharpe: float, mdd: float,
                            rsi_val: float, sma50: float, sma200: float,
                            price: float, m1, m3, m6) -> tuple[str, str, list, float]:
    """Run all six hold-duration sub-factors and return (label, hint, rows, score)."""
    sub = {
        "volatility": _hold_score_volatility(ann_vol),
        "beta":       _hold_score_beta(beta),
        "sharpe":     _hold_score_sharpe(sharpe),
        "drawdown":   _hold_score_drawdown(mdd),
        "trend":      _hold_score_trend(sma50, sma200, price),
        "momentum":   _hold_score_momentum(m1, m3, m6),
    }
    # weighted average of sub-factor scores, normalised to 0–1
    composite = sum(_HOLD_WEIGHTS[k] * sub[k][0] for k in _HOLD_WEIGHTS) / sum(_HOLD_WEIGHTS.values())

    if composite >= 0.62:
        label, hint = "LONG",   "12–24+ months"
    elif composite >= 0.42:
        label, hint = "MEDIUM", "3–12 months"
    else:
        label, hint = "SHORT",  "1–3 months"

    # build display rows for the terminal table
    rows = [
        (k.title(), f"{_HOLD_WEIGHTS[k]}%", f"{sub[k][0]*100:.0f}%", sub[k][1])
        for k in _HOLD_WEIGHTS
    ]
    return label, hint, rows, composite * 100


# ══════════════════════════════════════════════════════════════════════════════
# FUNDAMENTALS HELPER
# ══════════════════════════════════════════════════════════════════════════════

def get_fundamentals(info: dict) -> list[tuple[str, str]]:
    # Pull key fundamental fields from yfinance's .info dict.
    # val == val guards against NaN (NaN != NaN in Python).
    def fmt(val, fmt_str=".2f", suffix=""):
        return f"{val:{fmt_str}}{suffix}" if val is not None and val == val else "N/A"

    return [
        ("Sector",         info.get("sector", "N/A")),
        ("Market Cap",     f"${info.get('marketCap', 0)/1e9:.1f}B" if info.get("marketCap") else "N/A"),
        ("P/E (TTM)",      fmt(info.get("trailingPE"))),
        ("Forward P/E",    fmt(info.get("forwardPE"))),
        ("P/S Ratio",      fmt(info.get("priceToSalesTrailing12Months"))),
        ("EPS (TTM)",      fmt(info.get("trailingEps"))),
        ("Div. Yield",     f"{info.get('dividendYield', 0)*100:.2f}%" if info.get("dividendYield") else "None"),
        ("52W High",       fmt(info.get("fiftyTwoWeekHigh"))),
        ("52W Low",        fmt(info.get("fiftyTwoWeekLow"))),
        ("Analyst Target", fmt(info.get("targetMeanPrice"))),
        ("Analyst Rating", info.get("recommendationKey", "N/A").upper()),
        ("Beta",           fmt(info.get("beta"))),
    ]


# ══════════════════════════════════════════════════════════════════════════════
# MAIN — data pipeline, scoring, and terminal output
# ══════════════════════════════════════════════════════════════════════════════

def main():
    # ── Argument parsing ──────────────────────────────────────────────────────
    parser = argparse.ArgumentParser(description="Single stock buy/skip analysis")
    parser.add_argument("ticker", nargs="?", help="Stock ticker (e.g. AAPL)")
    parser.add_argument("--period", default="2y",
                        help="Lookback period: 6mo, 1y, 2y, 5y (default: 2y)")
    args   = parser.parse_args()
    ticker = (args.ticker or input("Enter ticker symbol: ")).strip().upper()

    # ── Data fetching ─────────────────────────────────────────────────────────
    print(f"\nFetching data for {ticker} ({args.period})...")
    stock = yf.Ticker(ticker)
    hist  = stock.history(period=args.period, auto_adjust=True)   # OHLCV with splits/divs adjusted
    if hist.empty:
        sys.exit(f"No data found for '{ticker}'. Check the symbol and try again.")

    # Fetch benchmark for relative-performance comparison
    bm_raw   = yf.download(BENCHMARK, period=args.period, auto_adjust=True, progress=False)
    bm_close = bm_raw["Close"].squeeze() if not bm_raw.empty else pd.Series(dtype=float)

    # ── Timezone normalisation ────────────────────────────────────────────────
    # yfinance may return tz-aware or tz-naive indices depending on the source.
    # Strip timezone info from both series so they can be compared and plotted
    # on the same axis without pandas raising a TypeError.
    def tz_strip(s: pd.Series) -> pd.Series:
        if hasattr(s.index, "tz") and s.index.tz is not None:
            s = s.copy()
            s.index = s.index.tz_convert("UTC").tz_localize(None)
        s.index = s.index.normalize()   # truncate to midnight so dates align
        return s

    hist       = hist.copy()
    hist.index = hist.index.tz_localize(None) if hist.index.tz is not None else hist.index
    hist.index = hist.index.normalize()
    bm_close   = tz_strip(bm_close)

    # ── Core metric computation ───────────────────────────────────────────────
    close      = hist["Close"]
    volume     = hist["Volume"]
    daily_rets = close.pct_change().dropna()

    days      = (close.index[-1] - close.index[0]).days or 1
    total_ret = (close.iloc[-1] / close.iloc[0]) - 1
    ann_ret   = annualized_return(total_ret, days)
    ann_vol   = annualized_volatility(daily_rets)
    sharpe    = sharpe_ratio(ann_ret, ann_vol)
    mdd       = max_drawdown(close)
    current   = close.iloc[-1]
    sma50     = close.rolling(50).mean().iloc[-1]
    sma200    = close.rolling(200).mean().iloc[-1]
    rsi_val   = compute_rsi(close).iloc[-1]
    macd_l, macd_s, macd_h = compute_macd(close)

    # Momentum over three windows: ~1 month, ~1 quarter, ~6 months
    m1 = momentum_return(close, 21)
    m3 = momentum_return(close, 63)
    m6 = momentum_return(close, 126)

    # ── Benchmark return over the same period ─────────────────────────────────
    bm_total_ret = None
    if not bm_close.empty:
        bm_aligned = bm_close[bm_close.index >= close.index[0]]
        if not bm_aligned.empty:
            bm_total_ret = bm_aligned.iloc[-1] / bm_aligned.iloc[0] - 1

    # ── Run buy/skip scoring model ────────────────────────────────────────────
    scores = {
        "rsi":          score_rsi(rsi_val),
        "ma_trend":     score_ma_trend(current, sma50, sma200),
        "macd":         score_macd(macd_l.iloc[-1], macd_s.iloc[-1], macd_h),
        "golden_cross": score_golden_cross(sma50, sma200),
        "momentum":     score_momentum(m1, m3, m6),
        "sharpe":       score_sharpe(sharpe),
        "drawdown":     score_drawdown(mdd),
        "volume":       score_volume(volume, close),
    }
    final_score = compute_score(scores)

    # Map composite score to a buy/skip label with a terminal colour code
    if final_score >= 65:
        recommendation = "BUY"
        verdict_color  = "\033[92m"   # green
    elif final_score >= 48:
        recommendation = "WATCH"
        verdict_color  = "\033[93m"   # yellow
    else:
        recommendation = "SKIP"
        verdict_color  = "\033[91m"   # red
    reset = "\033[0m"

    # ── Run hold-duration model ───────────────────────────────────────────────
    beta_val = stock.info.get("beta")
    hold_label, hold_hint, hold_rows, hold_score = hold_duration_analysis(
        ann_vol, beta_val, sharpe, mdd, rsi_val, sma50, sma200, current, m1, m3, m6
    )
    hold_color = "\033[92m" if hold_label == "LONG" else ("\033[93m" if hold_label == "MEDIUM" else "\033[91m")

    # ── Terminal output ───────────────────────────────────────────────────────
    info = stock.info

    print(f"\n{'═'*58}")
    print(f"  {ticker}  —  {info.get('longName', ticker)}")
    print(f"{'═'*58}")

    # Fundamentals block — static company/valuation data from yfinance
    print("\n── Fundamentals ─────────────────────────────────────────")
    print(tabulate(get_fundamentals(info), tablefmt="simple", colalign=("left", "right")))

    # Performance metrics block — calculated from historical price series
    print("\n── Performance Metrics ──────────────────────────────────")
    metrics = [
        ("Current Price",       f"${current:.2f}"),
        ("Period",              f"{args.period}  ({days} days)"),
        ("Total Return",        f"{total_ret*100:+.2f}%"),
        (f"{BENCHMARK} Return", f"{bm_total_ret*100:+.2f}%" if bm_total_ret is not None else "N/A"),
        ("Ann. Return",         f"{ann_ret*100:+.2f}%"),
        ("Ann. Volatility",     f"{ann_vol*100:.2f}%"),
        ("Sharpe Ratio",        f"{sharpe:.2f}"),
        ("Max Drawdown",        f"{mdd*100:.2f}%"),
        ("RSI (14)",            f"{rsi_val:.1f}"),
        ("50-day SMA",          f"${sma50:.2f}"),
        ("200-day SMA",         f"${sma200:.2f}"),
    ]
    print(tabulate(metrics, tablefmt="simple", colalign=("left", "right")))

    # Buy/skip signal table — shows each factor's weight, score, progress bar, and detail
    print("\n── Buy/Skip Signal Breakdown  (8 weighted signals) ─────")
    signal_rows = []
    for factor, (s, note) in scores.items():
        bar    = "█" * int(s * 10) + "░" * (10 - int(s * 10))   # ASCII progress bar
        label  = factor.replace("_", " ").title()
        weight = f"{WEIGHTS[factor]}%"
        signal_rows.append([label, weight, f"{s*100:.0f}%", bar, note])
    print(tabulate(signal_rows,
                   headers=["Factor", "Weight", "Score", "Visual", "Detail"],
                   tablefmt="rounded_outline"))

    # Hold-duration signal table — separate six-factor breakdown
    print("\n── Hold Duration Signal Breakdown  (6 weighted factors) ─")
    print(tabulate(hold_rows,
                   headers=["Factor", "Weight", "Score", "Detail"],
                   tablefmt="rounded_outline"))

    # Final verdict block — both recommendations side-by-side
    w = 62
    print(f"\n{'═'*w}")
    print(f"  {'BUY/SKIP':25}  {'HOLD DURATION':25}")
    print(f"  {'─'*25}  {'─'*25}")
    print(f"  {verdict_color}{recommendation:25}{reset}  {hold_color}{hold_label + '  (' + hold_hint + ')':25}{reset}")
    print(f"  {'Score: ' + str(round(final_score, 1)) + ' / 100':25}  {'Score: ' + str(round(hold_score, 1)) + ' / 100':25}")
    print(f"{'═'*w}")
    print("  Buy/Skip:  ≥65 = BUY  |  48–64 = WATCH  |  <48 = SKIP")
    print("  Hold:      ≥62 = LONG (12-24m+)  |  42-61 = MEDIUM (3-12m)  |  <42 = SHORT (1-3m)")
    print(f"\n  ⚠  Not financial advice. Do your own research.")
    print(f"{'═'*w}\n")

    # ── Save report to text file ──────────────────────────────────────────────
    save = input("\nWould you like to save the report to a text file? [y/N]: ").strip().lower()
    if save not in ("y", "yes"):
        print("Report was not saved. Analysis is complete.")
        return

    today   = date.today().strftime("%Y%m%d")
    outfile = f"{ticker.upper()}_analysis_{today}.txt"
    with open(outfile, "w", encoding="utf-8") as fh:
        fh.write(f"\n{'═'*58}\n")
        fh.write(f"  {ticker}  —  {info.get('longName', ticker)}\n")
        fh.write(f"  Generated: {today}\n")
        fh.write(f"{'═'*58}\n")
        fh.write("\n── Fundamentals ─────────────────────────────────────────\n")
        fh.write(tabulate(get_fundamentals(info), tablefmt="simple", colalign=("left", "right")))
        fh.write("\n\n── Performance Metrics ──────────────────────────────────\n")
        fh.write(tabulate(metrics, tablefmt="simple", colalign=("left", "right")))
        fh.write("\n\n── Buy/Skip Signal Breakdown  (8 weighted signals) ─────\n")
        fh.write(tabulate(signal_rows,
                          headers=["Factor", "Weight", "Score", "Visual", "Detail"],
                          tablefmt="rounded_outline"))
        fh.write("\n\n── Hold Duration Signal Breakdown  (6 weighted factors) ─\n")
        fh.write(tabulate(hold_rows,
                          headers=["Factor", "Weight", "Score", "Detail"],
                          tablefmt="rounded_outline"))
        fh.write(f"\n\n{'═'*w}\n")
        fh.write(f"  {'BUY/SKIP':25}  {'HOLD DURATION':25}\n")
        fh.write(f"  {'─'*25}  {'─'*25}\n")
        fh.write(f"  {recommendation:25}  {hold_label + '  (' + hold_hint + ')':25}\n")
        fh.write(f"  {'Score: ' + str(round(final_score, 1)) + ' / 100':25}"
                 f"  {'Score: ' + str(round(hold_score, 1)) + ' / 100':25}\n")
        fh.write(f"{'═'*w}\n")
        fh.write("  Buy/Skip:  >=65 = BUY  |  48-64 = WATCH  |  <48 = SKIP\n")
        fh.write("  Hold:      >=62 = LONG (12-24m+)  |  42-61 = MEDIUM (3-12m)  |  <42 = SHORT (1-3m)\n")
        fh.write(f"\n  Not financial advice. Do your own research.\n")
        fh.write(f"{'═'*w}\n")
    print(f"\nReport saved to {outfile}")


if __name__ == "__main__":
    main()
