
# Gold & FX Intelligence — MVP

A NATT-inspired (not a copy) research dashboard for XAUUSD and FX pairs.
It combines a fundamental score with multi-timeframe technical analysis.

## Run
1. Install Python 3.10+
2. `pip install -r requirements.txt`
3. `uvicorn app:app --reload`
4. Open http://127.0.0.1:8000

## Current MVP
- XAUUSD + major/cross FX scanner
- MN/W1/D1/H4/H1/M15 technical timeframes
- EMA trend, RSI and MACD-histogram components
- Weighted multi-timeframe score
- Fundamental layer with neutral placeholders
- Scanner table and confidence
- Clean dashboard responsive on phone

## Production roadmap
Connect licensed/reliable data feeds for:
- Fed/ECB/BoE/BoJ/RBA/RBNZ/BoC/SNB policy and expectations
- CPI, NFP, unemployment, GDP, PMI, retail sales and economic surprises
- US 2Y/10Y yields, real yields and DXY
- Central-bank gold purchases
- COT/positioning
- Geopolitical/news sentiment
- Economic calendar/event-risk filter
- Real-time broker/market data
- Backtesting and walk-forward validation
- Alerts and MT5 integration

Do not use the output as guaranteed trade advice.
