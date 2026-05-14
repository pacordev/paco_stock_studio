<<<<<<< HEAD
# paco_stock_analyzer
Single stock analyzer, with recoomendation to Buy, Hold or Skip
=======
# 📈 Paco's Stock Studio

A command-line tool that analyzes a single stock and produces two recommendations:

- 🟢 **BUY / WATCH / SKIP** — a composite signal built from 8 weighted technical factors
- ⏱️ **LONG / MEDIUM / SHORT hold duration** — a separate 6-factor model that estimates a reasonable holding window

Results are printed to the terminal. At the end, the script asks whether you want to save a plain-text report file (`<TICKER>_analysis_YYYYMMDD.txt`) — type `y` to save or press Enter to skip.

> ⚠️ **Disclaimer:** Stock Studio is for informational purposes only. It is not financial advice. Always do your own research before making investment decisions.

---

## 🛠️ Requirements

Python 3.10+ is required (uses the `float | None` union type hint).

Install dependencies:

```bash
pip install yfinance pandas numpy tabulate
```

| Library    | Purpose                                              |
|------------|------------------------------------------------------|
| `yfinance` | Fetches historical OHLCV price data and fundamentals |
| `pandas`   | Time-series manipulation and rolling calculations    |
| `numpy`    | Numerical operations (OBV, clipping, sign)           |
| `tabulate` | Formats terminal and file output tables              |

---

## 🚀 Usage

```bash
# Pass the ticker directly
python3 paco_stock_studio.py AAPL

# Specify a lookback period (6mo, 1y, 2y, 5y — default is 2y)
python3 paco_stock_studio.py AAPL --period 1y

# Run without arguments — the script will prompt for a ticker
python3 paco_stock_studio.py
```

Tickers follow Yahoo Finance conventions, so exchange suffixes work as expected:

```bash
python3 paco_stock_studio.py GOOS.TO      # Toronto Stock Exchange
python3 paco_stock_studio.py ASML.AS      # Amsterdam (Euronext)
python3 paco_stock_studio.py 9984.T       # Tokyo Stock Exchange
```

---

## 📄 Output

### 🖥️ Terminal

Five sections are printed in sequence:

```
══════════════════════════════════════════════════════════
  AAPL  —  Apple Inc.
══════════════════════════════════════════════════════════

── Fundamentals ──────────────────────────────────────────
── Performance Metrics ───────────────────────────────────
── Buy/Skip Signal Breakdown  (8 weighted signals) ───────
── Hold Duration Signal Breakdown  (6 weighted factors) ──

══════════════════════════════════════════════════════════
  BUY/SKIP                   HOLD DURATION
  ...
══════════════════════════════════════════════════════════
```

### 💾 Text file

After the terminal output, the script prompts:

```
Save report to a text file? [y/N]:
```

- Type **`y`** (or `yes`) and press Enter to save an identical plain-text copy (no color codes) to the working directory as `<TICKER>_analysis_YYYYMMDD.txt` — for example `AAPL_analysis_20260512.txt`.
- Press **Enter** (or type anything else) to skip saving and exit cleanly.

---

## 🔍 Output sections explained

### 🏢 Fundamentals

Static company and valuation data pulled directly from Yahoo Finance:

| Field           | Description                              |
|-----------------|------------------------------------------|
| Sector          | Industry classification                  |
| Market Cap      | Total market capitalization              |
| P/E (TTM)       | Trailing price-to-earnings ratio         |
| Forward P/E     | Forward-looking P/E estimate             |
| P/S Ratio       | Price-to-sales (trailing 12 months)      |
| EPS (TTM)       | Earnings per share (trailing 12 months)  |
| Div. Yield      | Annual dividend yield                    |
| 52W High / Low  | 52-week price range                      |
| Analyst Target  | Mean analyst price target                |
| Analyst Rating  | Consensus analyst recommendation         |
| Beta            | Market sensitivity coefficient           |

---

### 📊 Performance Metrics

Calculated from historical closing prices over the selected lookback period:

| Field           | Description                                                          |
|-----------------|----------------------------------------------------------------------|
| Current Price   | Most recent closing price                                            |
| Period          | Lookback period and number of calendar days                          |
| Total Return    | Raw price return over the full period                                |
| SPY Return      | S&P 500 (SPY) return over the same period for comparison             |
| Ann. Return     | Total return converted to a per-year CAGR figure                     |
| Ann. Volatility | Daily return standard deviation scaled to annual (×√252)             |
| Sharpe Ratio    | Excess return per unit of risk (risk-free rate: 4.5%)                |
| Max Drawdown    | Largest peak-to-trough decline in the period                         |
| RSI (14)        | 14-day Relative Strength Index                                       |
| 50 / 200-day SMA| Simple moving averages used for trend context                        |

---

### 🛒 Buy/Skip Signal Breakdown

Eight technical signals are each scored 0–100 and then combined into a weighted composite score. The final score maps to a recommendation:

| Score    | Recommendation      |
|----------|---------------------|
| ≥ 65     | 🟢 **BUY**          |
| 48 – 64  | 🟡 **WATCH**        |
| < 48     | 🔴 **SKIP**         |

| Signal        | Weight | What it measures                                              |
|---------------|--------|---------------------------------------------------------------|
| RSI           | 15%    | Momentum oscillator — oversold favors buying, overbought warns |
| MA Trend      | 15%    | Price position relative to the 50-day and 200-day SMAs        |
| MACD          | 10%    | EMA convergence/divergence and histogram momentum direction    |
| Golden Cross  | 10%    | Whether the 50-SMA is above or below the 200-SMA              |
| Momentum      | 15%    | Price returns over 1-month, 3-month, and 6-month windows      |
| Sharpe        | 15%    | Risk-adjusted return quality over the lookback period         |
| Drawdown      | 10%    | Penalty for historically deep peak-to-trough drops            |
| Volume        | 10%    | On-balance volume trend (accumulation vs. distribution)       |

---

### ⏳ Hold Duration Signal Breakdown

A separate six-factor model estimates how long it is reasonable to hold the stock. Each factor is scored and combined into a weighted composite:

| Composite score | Hold label        | Suggested window  |
|-----------------|-------------------|-------------------|
| ≥ 0.62          | 🟢 **LONG**       | 12 – 24+ months   |
| 0.42 – 0.61     | 🟡 **MEDIUM**     | 3 – 12 months     |
| < 0.42          | 🔴 **SHORT**      | 1 – 3 months      |

| Factor     | Weight | What it measures                                              |
|------------|--------|---------------------------------------------------------------|
| Volatility | 20%    | Low-volatility stocks tolerate longer holds                   |
| Beta       | 15%    | High beta amplifies market swings, suits shorter cycles       |
| Sharpe     | 20%    | Strong risk-adjusted return supports holding longer           |
| Drawdown   | 15%    | Frequent deep drops shorten the safe holding window           |
| Trend      | 15%    | Aligned SMA uptrend (price > 50-SMA > 200-SMA) supports long hold |
| Momentum   | 15%    | Consistent multi-timeframe gains signal a durable move        |

---

### 🏁 BUY/SKIP and HOLD DURATION (final verdict)

The last block displays both recommendations side-by-side with their composite scores:

```
══════════════════════════════════════════════════════════════
  BUY/SKIP                   HOLD DURATION
  ─────────────────────────  ─────────────────────────
  BUY                        LONG  (12–24+ months)
  Score: 71.4 / 100          Score: 68.2 / 100
══════════════════════════════════════════════════════════════
```

---

## ⚙️ Configuration

Two constants at the top of `paco_stock_studio.py` can be adjusted without touching any logic:

```python
RISK_FREE_RATE = 0.045   # risk-free rate used in Sharpe ratio (default: 4.5%)
BENCHMARK      = "SPY"   # benchmark ticker for relative performance comparison
```

Signal weights can also be tuned in the `WEIGHTS` (buy/skip) and `_HOLD_WEIGHTS` (hold duration) dictionaries. Each set must sum to 100.

---

## 🎓 Learning Python with this project

This script is a great example to study if you are picking up Python. Every section uses real, practical patterns — not toy examples. Work through the topics below and use the code as a reference you can actually run and experiment with.

Don't worry if you don't understand everything at once. Start with the fundamentals, run the script, change something small, and see what happens. That curiosity-driven tinkering is how most programmers learn best.

---

### 1. Python fundamentals

These are the building blocks everything else is built on. You will find all of them somewhere in this script.

| Concept | Where to spot it in the code |
|---|---|
| Variables and constants | `RISK_FREE_RATE`, `BENCHMARK`, `WEIGHTS` — defined once at the top so they are easy to find and change |
| `if / elif / else` | Every `score_*` function — a number comes in, a label and score come out |
| `for` loops | The `signal_rows` loop in `main()` builds the display table row by row |
| Functions (`def`) | Each `compute_*`, `score_*`, and `_hold_score_*` is its own small, focused function |
| Return values | Most functions return a `tuple` like `(0.85, "some explanation")` — a score plus a human-readable note |
| f-strings | Used everywhere to embed values in text, e.g. `f"RSI {rsi:.1f} — oversold"` |
| String methods | `.strip()`, `.upper()`, `.replace()` clean up user input and format labels |

**Try it yourself:**
- Change `RISK_FREE_RATE` from `0.045` to `0.02` and re-run the script. Does the Sharpe score change?
- Write a tiny function that takes a grade (0–100) and returns `"Pass"` or `"Fail"` using `if/else`.

---

### 2. Data structures

Python gives you a few essential ways to group related data. This script uses all of them.

| Structure | What it looks like | Where to spot it |
|---|---|---|
| List `[]` | An ordered collection you can loop over | `signal_rows`, `metrics`, `parts` — built up with `.append()` |
| Dictionary `{}` | Key → value pairs, great for named settings | `WEIGHTS`, `scores`, `sub` — signal names mapped to their scores |
| Tuple `()` | A fixed pair or group of values | Every `score_*` return: `(float, str)` — score plus description |
| List comprehension | A compact one-liner loop that builds a list | `[v for v in (m1, m3, m6) if v is not None]` in `score_momentum()` |

**Try it yourself:**
- Create a dictionary with three made-up signal names and weights, then compute a simple weighted average.
- Rewrite one of the short `for` loops in the script as a list comprehension.

---

### 3. Functions and type hints

You will notice that function signatures in this script look like this:

```python
def momentum_return(prices: pd.Series, days: int) -> float | None:
    ...
```

The `: pd.Series` and `-> float | None` parts are **type hints** — they tell you (and your editor) what type each argument should be and what the function will return. Python does not enforce them at runtime, but they make code much easier to read and catch mistakes before you even run anything.

The `float | None` syntax (available in Python 3.10+) means the function might return a number, or it might return `None` if there is not enough data.

**Try it yourself:**
- Find a function in the script that is missing type hints and add them.
- Write a function with a `str | None` return type that returns a string when given valid input and `None` otherwise.

---

### 4. Working with external libraries

One of Python's biggest strengths is its ecosystem of libraries. This script uses four:

```bash
pip install yfinance pandas numpy tabulate
```

| Library | What you learn from it |
|---|---|
| `yfinance` | How to pull data from an external API with one line of code |
| `pandas` | The go-to tool for working with tables and time-series data |
| `numpy` | Fast math on arrays — much quicker than writing loops by hand |
| `tabulate` | Turning a plain list of lists into a nicely formatted table |

You do not need to understand every function in these libraries right away. Get comfortable reading their documentation and looking up what you need — that is a skill every developer uses daily.

**Try it yourself:**
- Open a Python shell and run `import yfinance as yf; print(yf.Ticker("AAPL").info)`. Explore the dictionary it returns.
- Look up `pandas.DataFrame` and understand how it differs from `pd.Series`.

---

### 5. pandas and time-series data

Almost all the number-crunching in this script happens on `pd.Series` objects — essentially a list of values with a date attached to each one. pandas makes common operations very concise:

| What you want | How pandas does it | Example from the code |
|---|---|---|
| Rolling average | `.rolling(n).mean()` | `close.rolling(50).mean()` — 50-day SMA |
| Daily % change | `.pct_change()` | Used to compute daily returns |
| Running high | `.cummax()` | Used inside the max-drawdown formula |
| Filter by date | Boolean indexing | `bm_close[bm_close.index >= close.index[0]]` |
| Most recent value | `.iloc[-1]` | Gets the last row of any series |
| Drop missing values | `.dropna()` | Removes `NaN` rows before doing math |

**Try it yourself:**
- Download a year of Apple data: `yf.Ticker("AAPL").history(period="1y")["Close"]`
- Compute its 20-day rolling average and find the single highest closing price.

---

### 6. User input and reading and writing files

#### Asking the user a yes/no question

Before saving the report, the script uses the built-in `input()` function to ask whether the user wants a file:

```python
save = input("\nSave report to a text file? [y/N]: ").strip().lower()
if save not in ("y", "yes"):
    print("Report not saved. Done.")
    return
```

A few things worth noticing here:
- `input()` pauses execution, prints its argument as a prompt, and returns whatever the user typed as a string.
- `.strip()` removes any accidental leading/trailing spaces or newline characters from the input.
- `.lower()` converts the response to lowercase so `"Y"`, `"y"`, and `"yes"` all match the same condition.
- The `return` statement exits `main()` immediately — a clean and readable way to bail out without deeply nested `else` blocks.

This pattern — prompt → normalise → branch — is the standard recipe for any interactive yes/no question in a terminal script.

#### Writing the report file

If the user confirms, the script saves the report using Python's built-in `open()`:

```python
with open(outfile, "w", encoding="utf-8") as fh:
    fh.write("some text\n")
```

- `"w"` means *write mode* — it creates the file if it does not exist, or replaces it if it does.
- `encoding="utf-8"` makes sure special characters (like the `═` border lines) are stored correctly.
- The `with` block automatically closes the file when it is done, even if something goes wrong — always use `with` when working with files.

**Try it yourself:**
- Add a second prompt that asks for a custom filename, and use that instead of the auto-generated one.
- Change `"w"` to `"a"` (append mode) and run the script twice with the same ticker. Open the file — what happened?
- Add a line to the file that records how many signals scored above 60.

---

### 7. Command-line arguments (`argparse`)

Instead of hardcoding the ticker symbol, the script accepts it as a command-line argument:

```python
parser = argparse.ArgumentParser(description="Single-stock buy/skip analyzer")
parser.add_argument("ticker", nargs="?", help="Stock ticker (e.g. AAPL)")
parser.add_argument("--period", default="2y", help="Lookback period")
args = parser.parse_args()
```

- **Positional argument** (`ticker`) — provided by position: `python3 script.py AAPL`
- **Optional flag** (`--period`) — provided by name: `python3 script.py AAPL --period 1y`
- `nargs="?"` makes the positional argument optional (the script will ask for it interactively if omitted)
- `default="2y"` is used when `--period` is not passed at all

This pattern makes scripts far more flexible and reusable than hardcoding values.

**Try it yourself:**
- Add a `--output` flag that lets the user choose a custom filename for the report.
- Add a `--no-file` flag using `action="store_true"` that skips saving the file entirely.

---

### 8. Math and statistics in Python

The performance section translates standard finance formulas directly into Python expressions. You do not need a finance background to follow the pattern — each formula is just arithmetic:

| What it computes | The formula in code |
|---|---|
| Annualized return (CAGR) | `(1 + total_return) ** (365 / days) - 1` |
| Annualized volatility | `daily_returns.std() * (252 ** 0.5)` |
| Sharpe ratio | `(ann_return - RISK_FREE_RATE) / ann_vol` |
| Max drawdown | `((prices - prices.cummax()) / prices.cummax()).min()` |

Notice how closely the code resembles the mathematical notation. This is one of Python's great strengths for data science work.

**Try it yourself:**
- Compute the Sharpe ratio by hand for a simple set of numbers and verify you get the same result as the script.
- Try different values of `RISK_FREE_RATE` and observe how buy/skip scores shift.

---

### 9. Suggested learning path

If you are brand new to Python and want to use this project as a guide, here is a sensible order to work through things:

1. **Python basics** — variables, types, `if/else`, loops, functions
2. **Data structures** — lists, dictionaries, tuples
3. **`pip` and virtual environments** — how to install libraries cleanly
4. **pandas fundamentals** — Series, DataFrame, filtering, rolling windows
5. **User input and File I/O** — `input()` for interactive prompts, reading and writing text files
6. **`argparse`** — building tools that accept arguments from the terminal
7. **NumPy basics** — vectorized operations, `np.sign`, `np.mean`
8. **Type hints** — making your function signatures self-documenting
9. **APIs and JSON** — understanding how `yfinance` fetches and returns data

You do not need to master each step before moving on. Come back to earlier topics as you encounter them in the code — the repetition will make them stick.

---

### 📚 Good places to keep learning

- [Python official tutorial](https://docs.python.org/3/tutorial/) — clear, comprehensive, written by the people who built the language
- [pandas getting started](https://pandas.pydata.org/docs/getting_started/index.html) — the "10 minutes to pandas" page is genuinely useful
- [Real Python](https://realpython.com/) — practical, well-written tutorials on every topic above
- [NumPy quickstart](https://numpy.org/doc/stable/user/quickstart.html) — a short intro to thinking in arrays
- [yfinance documentation](https://ranaroussi.github.io/yfinance/) — see what data is available and how to fetch it
>>>>>>> f1eefca (First commit of my stock analyzer project)
