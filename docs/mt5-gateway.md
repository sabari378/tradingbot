# MT5 Gateway

MT5 runs on Windows next to the installed terminal. Nirv cloud services must call this gateway through a secure authenticated private connection. The gateway binds to `127.0.0.1:8100` initially, rejects non-demo orders, and keeps broker credentials on the Windows host. Move to a private tunnel or mutually authenticated service connection before remote use.

The backend and dashboard may run in WSL Ubuntu, but the gateway must run in Windows Python where the MetaTrader 5 terminal is installed. Do not install or run the gateway inside WSL unless it is only being used for import-level tests without MT5.
