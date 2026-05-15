

# paco_stock_studio
Single stock analyzer, with recommendations to Buy, Hold or Skip
================================================================

# 📈 Paco's Stock Studio

command-line script that analyzes a single stock and produces two recommendations:

- 🟢 ** BUY / WATCH / SKIP ** — a signal built, using 8 weighted technical factors for the analysis (non traditional, considering recent price data or volume).
- ⏱️ ** LONG / MEDIUM / SHORT hold duration ** — a separate 6-factor model to estimates a reasonable holding window.

All results are printed to the terminal, to start (I like the terminal....). 
After this, the script will ask you if you want to save the output to a txt file with the name (`<TICKER>_analysis_YYYYMMDD.txt`) — you can type `y` to save it or press Enter to skip saving the report.

------------------
> ⚠️ **A very important note:** my script was created as a practice for python, based on my own knowledge on stocks investment done by myself, and should be considered for informational and educational purposes only. This is not intended to be financial advice. Always do your own research and due dilligence before making investment decisions.
------------------

## 🛠️ Requirements to run this script

- Python 3.10+ is required (script uses the `float | None` union type hint).
- Install the following libraries used (some you may already have):
```bash
pip install yfinance pandas numpy tabulate
```

| Library    | What is it used for                                  |
|------------|------------------------------------------------------|
| `yfinance` | Used to fetch historical price data and fundamentals |
| `pandas`   | Used for data manipulation and rolling calculations  |
| `numpy`    | Used for numerical operations                        |
| `tabulate` | Used to print terminal output with 'pretty' format   |

---

## 🚀 How to use/execute the script

```bash
# on execution, pass the ticker in the command
python3 paco_stock_studio.py AAPL

# you can declare a a specific period for historical data (6mo, 1y, 2y, 5y — default is 2y)
python3 paco_stock_studio.py AAPL --period 1y

# or you can execute with no arguments and the script will ask you for a ticker
python3 paco_stock_studio.py
```

I follow Yahoo Finance conventions for stock ticker, so stock exchange suffixes work as expected:

```bash
python3 paco_stock_studio.py GOOS.TO      # Toronto Stock Exchange
python3 paco_stock_studio.py ASML.AS      # Amsterdam (Euronext)
python3 paco_stock_studio.py 9984.T       # Tokyo Stock Exchange
```

---

## 📄 What is the output of the script

### 🖥️ In the Terminal

five sections printed in sequence:

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

### 💾 Saving to a text file

After the terminal output finished, the script will ask you:

```
Save report to a text file? [y/N]:
```

- Type **`y`** (or `yes`) and press Enter, this will save a txt copy to the working directory as `<TICKER>_analysis_YYYYMMDD.txt` — for example `AAPL_analysis_20260512.txt`.
- Press **Enter** or **N** (or type anything else) to skip saving and finish the analysis.

---

## 🔍 Explanation of the different output sections (I use investopedia.com and finviz.com to learn...)

### 🏢 Fundamentals 

Company and valuation data pulled from Yahoo Finance:

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

This is calculated from historical closing prices over the indicated historical period:

| Field           | Description                                                          |
|-----------------|----------------------------------------------------------------------|
| Current Price   | Most recent closing price                                            |
| Period          | Historical period based on calendar days                             |
| Total Return    | Raw price return over the full period                                |
| SPY Return      | S&P 500 (SPY) return over the same period,for comparison             |
| Ann. Return     | Total return converted to a per-year CAGR figure                     |
| Ann. Volatility | Daily return standard deviation scaled to annual                     |
| Sharpe Ratio    | Excess return per unit of risk (risk-free rate: 4.5%)                |
| Max Drawdown    | Largest peak-to-trough decline in the period                         |
| RSI (14)        | 14-day Relative Strength Index                                       |
| 50 / 200-day SMA| Simple moving averages used for trend context                        |

---

### 🛒 Buy/Skip Signals (Breakdown)

Eight technical signals are scored 0–100, and then combined into a unique weighted score. Based on this, the final score maps to a probable recommendation:

| Score    | Recommendation      |
|----------|---------------------|
| ≥ 65     | 🟢 **BUY**          |
| 48 – 64  | 🟡 **WATCH**        |
| < 48     | 🔴 **SKIP**         |

| Signal        | Weight | What it measures                                              |
|---------------|--------|---------------------------------------------------------------|
| RSI           | 15%    | Momentum oscillator — oversold favors buying, overbought warns|
| MA Trend      | 15%    | Price position relative to the 50-day and 200-day SMAs        |
| MACD          | 10%    | EMA convergence/divergence and histogram momentum direction   |
| Golden Cross  | 10%    | Whether the 50-SMA is above or below the 200-SMA              |
| Momentum      | 15%    | Price returns over 1-month, 3-month, and 6-month windows      |
| Sharpe        | 15%    | Risk-adjusted return quality over the lookback period         |
| Drawdown      | 10%    | Penalty for historically deep peak-to-trough drops            |
| Volume        | 10%    | On-balance volume trend (accumulation vs. distribution)       |

---

### ⏳ Hold Duration Signals (Breakdown)

Another model, based on six-factor estimates on how long it is reasonable to hold the stock. Each factor is scored and combined into a unique weighted composite:

| Composite score | Hold label        | Suggested window  |
|-----------------|-------------------|-------------------|
| ≥ 0.62          | 🟢 **LONG**       | 12 – 24+ months   |
| 0.42 – 0.61     | 🟡 **MEDIUM**     | 3 – 12 months     |
| < 0.42          | 🔴 **SHORT**      | 1 – 3 months      |

| Factor     | Weight | What it measures                                              |
|------------|--------|---------------------------------------------------------------|
| Volatility | 20%    | Low-volatility stocks which tolerate longer holds             |
| Beta       | 15%    | High beta amplifies market changes (suits shorter cycles)     |
| Sharpe     | 20%    | Strong risk-adjusted return (longer holdings)                 |
| Drawdown   | 15%    | Frequent deep drops shorten the safe holding window           |
| Trend      | 15%    | Aligned SMA uptrend (price > 50-SMA > 200-SMA) (long hold)    |
| Momentum   | 15%    | Consistent multi-timeframe gains, which signal a durable move |

---

### 🏁 BUY/SKIP and HOLD DURATION (final recommendation)

The last output section indicates both recommendations side-by-side with their scores:

```
══════════════════════════════════════════════════════════════
  BUY/SKIP                   HOLD DURATION
  ─────────────────────────  ─────────────────────────
  BUY                        LONG  (12–24+ months)
  Score: 71.4 / 100          Score: 68.2 / 100
══════════════════════════════════════════════════════════════
```

---

## ⚙️ Configuration of the scripts/Adjustments you can do

There are 2 constants at the top of the script that can be modified without affecting any logic:

```python
RISK_FREE_RATE = 0.045   # risk-free rate used in Sharpe ratio (default: 4.5%)
BENCHMARK      = "SPY"   # benchmark ticker used for performance comparison
```

Signal weight variables can also be modified in the `WEIGHTS` (buy/skip) and `_HOLD_WEIGHTS` (hold duration) dictionaries. Important: each set must sum to 100.

---

## 🎓 On to the fun... learning Python with this project

For me, the intention to create this script is to learn two thihngs: python development and stock investments. 
I believe this is a good example to study fundamentals python development patterns. This was a fun experience to code and experiment different topics in python development. The script has a lot of comments to help in understanding what each piece of code is doing.
Feel free to copy the code, test and modify for your own experience. 
Here, I am trying to describe what it is done in the script.

---

### 1. Python fundamentals

These are the basic building blocks everything else is built on. All these are within the script.

| Concept | Where to spot it in the code |
|---|---|
| Variables and constants | `RISK_FREE_RATE`, `BENCHMARK`, `WEIGHTS` — defined once at the top |
| `if / elif / else` | Every `score_*` function — a number comes in, a label and score come out |
| `for` loops | The `signal_rows` loop in `main()` builds the display table row by row |
| Functions (`def`) | Each `compute_*`, `score_*`, and `_hold_score_*` is its own small, focused function |
| Return values | Most functions return a `tuple` like `(0.85, "some explanation")` — a score and a human-friendly note |
| f-strings | Used everywhere in the script to embed values in text, e.g. `f"RSI {rsi:.1f} — oversold"` |
| String methods | `.strip()`, `.upper()`, `.replace()` clean up user input and format labels |

**What can you change:**
- Change `RISK_FREE_RATE` from `0.045` to `0.02` and re-run the script. Check if the Sharpe score change

---

### 2. Data structures management

Basic data management in python and different techniques.

| Structure | What it looks like | Where to find it |
|---|---|---|
| List `[]` | An ordered collection | `signal_rows`, `metrics`, `parts` — built up with `.append()` |
| Dictionary `{}` | Key → value pairs | `WEIGHTS`, `scores`, `sub` — signal names mapped to their scores |
| Tuple `()` | A fixed pair or group of values | Every `score_*` return: `(float, str)` — score plus description |
| List comprehension | A tiny loop that builds a list | `[v for v in (m1, m3, m6) if v is not None]` in `score_momentum()` |

**What can you change:**
- Create a dictionary with three made-up signal names and weights, then compute a simple weighted average.
- Modify one of the `for` loops in the script as a list comprehension.

---

### 3. Functions and type hints

You will see across the script, that function signatures look something like this:

```python
def momentum_return(prices: pd.Series, days: int) -> float | None:
    ...
```

The `: pd.Series` and `-> float | None` parts are **type hints**.

The `float | None` syntax means the function might return a number or `None` if there is not enough data.

**What can you change:**
- Add additional hints to functions in the script (not all of them have)

---

### 4. Working with different libraries

This script uses four different libraries. Pandas and Numpy are widely used:

```bash
pip install yfinance pandas numpy tabulate
```

| Library | What you can learn from it |
|---|---|
| `yfinance` | Interact with an external API to get data with one line of code |
| `pandas` | Widely used for data management and dataframes |
| `numpy` | Fast math on arrays |
| `tabulate` | Turning a plain list of lists into a 'pretty' formatted table |

If you are not very familiar with these, I recommend to read their documentation and look for what you need.

**What can you do:**
- Open a Python shell and run `import yfinance as yf; print(yf.Ticker("AAPL").info)`. You can check the dictionary that will return.

---

### 5. pandas

A lot of all the number-crunching in this script is done on `pd.Series` objects:

| What you need | How pandas does it | Example from the code |
|---|---|---|
| Rolling average | `.rolling(n).mean()` | `close.rolling(50).mean()` — 50-day SMA |
| Daily % change | `.pct_change()` | Used to compute daily returns |
| Running high | `.cummax()` | Used inside the max-drawdown formula |
| Filter by date | Boolean indexing | `bm_close[bm_close.index >= close.index[0]]` |
| Most recent value | `.iloc[-1]` | Gets the last row of any series |
| Drop missing values | `.dropna()` | Removes `NaN` (missing values) rows before doing math |

**What can you change:**
- Download a year of Apple data: `yf.Ticker("AAPL").history(period="1y")["Close"]`
- Compute its 20-day rolling average and find the single highest closing price.

---

### 6. User input and reading and writing files

#### Asking the user a yes/no question (user input)

The script ask the user if they want to save the report, and before saving the report, the script uses the built-in `input()` function to request user input:

```python
save = input("\nWould you like to save the report to a text file? [y/N]: ").strip().lower()
if save not in ("y", "yes"):
    print("Report was not saved. Analysis is complete.")
    return
```

Some notes from this feature:
- `input()` pauses execution, prints the argument as a prompt, and returns whatever the user typed as a string.
- `.strip()` removes any leading/trailing spaces or newline characters from the input (cleaning the string).
- `.lower()` converts the response to lowercase so `"Y"`, `"y"`, and `"yes"` all match the same condition.
- The `return` statement exits `main()` immediately — a clean and readable way to exit without deeply nested `else` blocks.

This pattern is a standard for any interactive yes/no question in a terminal script.

#### Writing the report into a file

Once the user select Yes, the script saves the report into a txtx file using Python's built-in `open()`:

```python
with open(outfile, "w", encoding="utf-8") as fh:
    fh.write("some text\n")
```

- `"w"` means *write mode* — it creates the file if it does not exist, or replaces it if it does.
- `encoding="utf-8"` to make sure that special characters (like the `═` border lines) are stored correctly.
- The `with` block automatically closes the file when it is done, even if something goes wrong — always use `with` when working with files.

**What can you change:**
- Add a second prompt that asks for a custom filename, and use that instead of the existing one.
- Change `"w"` to `"a"` (append mode) and run the script twice with the same ticker. Open the file and check what happened.
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
- `nargs="?"` makes the positional argument optional (the script will ask for it if not provided)
- `default="2y"` is used when `--period` is not provided

This pattern makes this script more flexible and reusable than hardcoding values.

**What can you change:**
- Add a `--output` flag that lets the user type a custom filename for the report.
- Add a `--no-file` flag using `action="store_true"` that skips saving the file entirely.

---

### 8. Math and statistics in Python. (the most complicated part for me...)

The performance section translates standard finance formulas directly into Python expressions. 
You don't need to have a finance background to follow the pattern. Each formula is just arithmetic:

| What it computes | The formula in code |
|---|---|
| Annualized return (CAGR) | `(1 + total_return) ** (365 / days) - 1` |
| Annualized volatility | `daily_returns.std() * (252 ** 0.5)` |
| Sharpe ratio | `(ann_return - RISK_FREE_RATE) / ann_vol` |
| Max drawdown | `((prices - prices.cummax()) / prices.cummax()).min()` |

The code try to resemble the mathematical notation, and that is one of Python's strengths.

**What can you change:**
- Compute the Sharpe ratio by hand for a simple set of numbers and verify you get the same result as the script.
- Try different values of `RISK_FREE_RATE` and check how buy/skip scores change.

---

### 9. To continue learning.... 

This is only my recommendation, to continue from here on a python deep dive:

1. **Python basics** — variables, types, `if/else`, loops, functions
2. **Data structures** — lists, dictionaries, tuples
3. **`pip` and virtual environments** — how to install libraries cleanly
4. **pandas fundamentals** — Series, DataFrame, filtering, rolling windows
5. **User input and File I/O** — `input()` for interactive prompts, reading and writing text files
6. **`argparse`** — building tools that accept arguments from the terminal
7. **NumPy basics** — vectorized operations, `np.sign`, `np.mean`
8. **Type hints** — making your function signatures self-documenting
9. **APIs and JSON** — understanding how `yfinance` fetches and returns data

As with everything, practice makes perfection. Repetition on these concepts will grow your learning.

---

### 📚 Some websites to keep learning

- [Python official tutorial](https://docs.python.org/3/tutorial/) — clear, comprehensive, written by the people who built the language
- [pandas getting started](https://pandas.pydata.org/docs/getting_started/index.html) — the "10 minutes to pandas" page is genuinely useful
- [Real Python](https://realpython.com/) — practical, well-written tutorials on every topic above
- [NumPy quickstart](https://numpy.org/doc/stable/user/quickstart.html) — a short intro to thinking in arrays
- [yfinance documentation](https://ranaroussi.github.io/yfinance/) — see what data is available and how to fetch it
- [Investopedia](https://www.investopedia.com/) — to find online financial resources and dictionaries
- [finviz](https://finviz.com/) — web-based financial visualizations and stock screenings
