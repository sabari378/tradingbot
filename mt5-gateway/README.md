# Nirv MT5 Gateway

Windows-local FastAPI service for the MetaTrader 5 terminal. Bind to `127.0.0.1:8100` by default. It accepts only `DEMO` orders and requires `X-Nirv-Signature`; configure the secret locally and never expose this service directly to the public internet. The optional `MetaTrader5` import keeps Linux CI and development environments working without MT5.

Run on the MT5 Windows host:

```powershell
pip install -r requirements.txt
uvicorn nirv_mt5.main:app --host 127.0.0.1 --port 8100
```
