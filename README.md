# PulseStream

High-performance, event-driven backend platform for ingesting, processing, and analyzing large-scale event data in real-time.

## 🚀 Features

- **Real-time Event Ingestion** - Sub-10ms latency event ingestion
- **Scalable Processing** - Redis Streams with consumer groups
- **Time-Series Storage** - PostgreSQL with automatic partitioning
- **Real-time Analytics** - Live aggregations and metrics
- **High Performance** - Async architecture with connection pooling

## 📋 Tech Stack

- **FastAPI** - Async web framework
- **Redis Streams** - Event streaming
- **PostgreSQL 16** - Time-series storage
- **AsyncPG** - High-performance database driver
- **Poetry** - Dependency management

## 🎯 Event Types

- **User Events**: `user.registered`, `user.login`, `user.logout`, `user.profile_updated`
- **Activity Events**: `activity.page_view`, `activity.click`, `activity.search`, `activity.feature_used`
- **Transaction Events**: `transaction.created`, `transaction.completed`, `transaction.failed`, `transaction.refunded`
- **System Events**: `system.error`, `system.performance`, `system.api_call`

## 🛠️ Setup

### Prerequisites

- Python 3.14+
- Poetry
- Docker & Docker Compose

### Installation

```bash
# Clone repository
git clone <repository-url>
cd PulseStream

# Install dependencies
poetry install

# Create .env from Bitwarden or copy .env.example and fill all values (no defaults)
# See .github/BITWARDEN_SETUP.md for the full config JSON structure

# Start infrastructure
docker-compose up -d

# Run migrations
poetry run alembic upgrade head

# Start API server
make run

# In separate terminals, start workers
make worker-base        # Event consumer (Redis → PostgreSQL)
make worker-aggregator  # Aggregation worker (1min, hourly, daily)
```

### Docker (full stack)

```bash
# Build and run all services (API, workers, Postgres, Redis)
docker-compose up -d --build

# Run migrations (first time only)
docker-compose run --rm api alembic upgrade head

# API: http://localhost:8000
# Docs: http://localhost:8000/docs
```

## 📚 API Documentation

Once running, visit:

- **API Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

**Note:** Docs are only enabled in development. All endpoints require the `X-API-Key` header (admin key for `/stats`, `/streams`; user key for others).

## 🧪 Testing

```bash
# Run tests (requires Redis and PostgreSQL)
make test

# Run tests with coverage
make test-cov
```

## 🔐 CI/CD (GitHub Actions + Bitwarden)

CI runs on push/PR to `main` and `dev`. Secrets are pulled from **Bitwarden Secrets Manager**.

**Setup:** See [.github/BITWARDEN_SETUP.md](.github/BITWARDEN_SETUP.md) for:
- Creating secrets in Bitwarden
- Configuring `BW_ACCESS_TOKEN` in GitHub
- Updating Secret IDs in the workflow

## 🏗️ Project Structure

```
PulseStream/
├── src/
│   ├── auth/           # API key authentication
│   ├── models/         # Pydantic and SQLAlchemy models
│   ├── routes/         # API endpoints (misc, ingestion, query, admin)
│   ├── services/      # Business logic (event producer)
│   ├── db/             # Database and Redis clients
│   ├── workers/        # Consumer and aggregation workers
│   └── utils/          # Logging and utilities
├── scripts/            # CLI (api, worker)
├── migrations/         # Alembic DB migrations
├── tests/              # Tests
└── pyproject.toml      # Poetry config
```

## 🔧 Commands

```bash
make install            # Install dependencies (no dev)
make install-dev        # Install with dev dependencies
make run                # Run API server (dev mode with reload)
make api                # Run API server (production)
make worker-base        # Run event consumer worker
make worker-aggregator  # Run aggregation worker
make test               # Run tests
make test-cov           # Run tests with coverage
make build              # Build distribution packages
make clean              # Remove cache and build artifacts
```

## 📈 Performance Targets

- **Ingestion**: < 10ms latency
- **Processing**: < 100ms latency
- **Queries**: < 50ms latency
- **Throughput**: 10K+ events/second

## 📝 License

MIT License

## 🖋️ Author
- Muzaffar Shaikh - [muzaffarshaikh0201@gmail.com](mailto:"Muzaffar%20Shaikh"<muzaffarshaikh0201@gmail.com>)