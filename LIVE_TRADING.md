# Live Trading Integration Guardrails

Live trading is intentionally not enabled by default.

Before connecting a broker, the project needs:

- A broker adapter with explicit `place_order`, `cancel_order`, `query_positions`, and `query_orders` methods.
- A dry-run mode that logs the exact order payload without sending it.
- Account-level allowlists for symbols and markets.
- Max order amount, max daily turnover, and max position exposure limits.
- Manual confirmation for the first live order of every symbol.
- Immutable order/audit logs.

Recommended first adapters:

- QMT for local Chinese brokerage workflows.
- JoinQuant or another sandbox-first quant platform for strategy validation.
- A broker paper-trading API before any cash account.

Do not put broker passwords, tokens, or certificates in Git-tracked files. Use `.env` or the broker's own encrypted credential store.
