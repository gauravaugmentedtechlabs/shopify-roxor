# Shopify ↔ Roxor ERP Middleware

Production-grade FastAPI middleware for exchanging SAP-style XML IDOC files between Shopify and Roxor ERP over SFTP.

## Capabilities

- Shopify `orders/create` webhook → complete Shopify order fetch → ORDERS02 XML generation → SFTP upload to `/outbound/orders/`.
- Roxor SFTP polling every 30 seconds for DELVRY07 delivery confirmations, stock updates, and INVOIC02 invoices.
- Shopify GraphQL Admin API support for order lookup, inventory updates, fulfillments with tracking, and invoice metadata.
- PostgreSQL persistence for processed files, structured audit logs, order mappings, retry queue, and inventory mappings.
- SHA-256 file-hash idempotency, webhook idempotency via order mappings, retry queue with exponential backoff, and dead-letter state.
- Paramiko SFTP support for password and SSH private-key authentication.
- Docker and docker-compose deployment.

## Architecture

The implementation follows the approved architecture in [`docs/architecture.md`](docs/architecture.md):

```text
Shopify ↔ FastAPI Middleware ↔ SFTP ↔ Roxor ERP
```

Runtime modules are organized under:

- `app/api` — FastAPI health, webhook, and admin routes.
- `app/config` — Pydantic settings and structured logging.
- `app/db`, `app/models`, `app/repositories` — async SQLAlchemy persistence.
- `app/services/sftp` — Paramiko SFTP connection and file operations.
- `app/services/shopify` — GraphQL Admin API client, queries, mutations, and business operations.
- `app/services/xml` — secure XML parsing, IDOC detection, and validation helpers.
- `app/parsers` and `app/generators` — IDOC parsers and ORDERS02 generation.
- `app/processors` — order, delivery, stock, invoice, and inbound dispatch workflows.
- `app/pollers` and `app/workers` — SFTP polling and retry processing.

## Configuration

Copy `.env.example` to `.env` and configure:

```text
SHOPIFY_STORE
SHOPIFY_ACCESS_TOKEN
SHOPIFY_API_VERSION
SHOPIFY_LOCATION_ID
SHOPIFY_WEBHOOK_SECRET
POSTGRES_URL
SFTP_HOST
SFTP_PORT
SFTP_USERNAME
SFTP_PASSWORD
SFTP_PRIVATE_KEY
SFTP_OUTBOUND_ORDERS_PATH=/outbound/orders/
SFTP_INBOUND_DELIVERY_PATH=/inbound/delivery/
SFTP_INBOUND_STOCK_PATH=/inbound/stock/
SFTP_INBOUND_INVOICE_PATH=/inbound/invoice/
SFTP_ARCHIVE_PATH=/archive/
SFTP_ERROR_PATH=/error/
SFTP_POLL_INTERVAL_SECONDS=30
```

## Run with Docker

```bash
docker compose up --build
```

The app container runs Alembic migrations before starting Uvicorn.

## Local development

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload
```

Disable background workers in local tests with:

```bash
WORKERS_ENABLED=false
```

## Tests

```bash
pytest
```

## SFTP private keys and PuTTY `.ppk` files

Set `SFTP_PRIVATE_KEY` to either a filesystem path or the raw private-key contents. OpenSSH keys are loaded directly. PuTTY `.ppk` keys are also supported: the app first attempts Paramiko's key loaders and then falls back to `puttygen` conversion when needed. The Docker image installs `putty-tools` for that conversion path.

For encrypted private keys, set:

```text
SFTP_PRIVATE_KEY=/run/secrets/roxor_sftp_private_key.ppk
SFTP_PRIVATE_KEY_PASSPHRASE=your-key-passphrase
```

If you run outside Docker and use a `.ppk` key, install `putty-tools`/`puttygen` or export the key to OpenSSH format with PuTTYgen.
