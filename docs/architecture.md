# Nirv Architecture

Nirv is split into a FastAPI cloud backend, a Next.js dashboard, and a local Windows MT5 gateway. The backend owns analysis, deterministic risk, approval state, audit events, and paper execution. The gateway is the only component allowed to call the MetaTrader 5 Python API.

The control path is:

`market/news adapters -> specialist agents -> NirvMasterAgent -> signal/confluence -> risk policy -> user approval -> execution adapter -> journal/integrations`

The master agent never executes orders directly. Provider protocols keep market and news integrations replaceable. PostgreSQL is the durable store and Redis is event/cache infrastructure in deployment environments.
