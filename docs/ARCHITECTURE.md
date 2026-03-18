# PulseStream Architecture

## System Overview

PulseStream is a high-performance, event-driven platform for real-time event processing and analytics.
```
┌─────────────┐
│   Clients   │
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────┐
│     FastAPI Ingestion API       │
│  (Async, High-Throughput)       │
└────────────┬────────────────────┘
             │
             ▼
      ┌─────────────┐
      │Redis Streams│
      │(Event Queue)│
      └──────┬──────┘
             │
             ▼
┌────────────────────────────────┐
│    Consumer Workers (Async)    │
│  - Process events              │
│  - Batch inserts               │
│  - Update aggregations         │
└────────┬───────────────────────┘
         │
         ▼
  ┌─────────────┐
  │ PostgreSQL  │
  │ (Partitioned│
  │  TimeSeries)│
  └─────────────┘
```

## Components

### 1. FastAPI Application (`src/main.py`)
- Async web framework
- Event ingestion endpoints
- Query and analytics endpoints
- Health checks and monitoring
- API key authentication (X-API-Key header)

### 2. Redis Streams (`src/db/redis_client.py`)
- Event queue with consumer groups
- At-least-once delivery
- Horizontal scaling support
- Multiple streams per event category (user, activity, transaction, system)

### 3. PostgreSQL (`src/db/postgres.py`)
- Time-partitioned event storage
- JSONB for flexible schemas
- GIN indexes for fast queries
- AsyncPG for performance

### 4. Consumer Workers (`src/workers/`)
- Async event processing
- Batch database operations
- Graceful shutdown
- Error handling and retry

### 5. Aggregation Workers (`src/workers/aggregator.py`)
- Time-window aggregations (minute, hourly, daily)
- Real-time metrics
- Pre-computed analytics

## Data Flow

1. **Ingestion**: Client → FastAPI → Validation → Redis Streams
2. **Processing**: Redis Streams → Consumer Worker → PostgreSQL
3. **Aggregation**: PostgreSQL → Aggregator Worker → Aggregation Tables
4. **Query**: Client → FastAPI → PostgreSQL → Response

## Scaling Strategy

### Horizontal Scaling
- **API Servers**: Run multiple FastAPI instances behind a load balancer
- **Consumer Workers**: Add more workers to process events in parallel
- **Database**: Use read replicas for queries, write to primary

### Vertical Scaling
- Increase connection pool sizes
- Tune PostgreSQL parameters
- Add more Redis memory

## Performance Optimizations

1. **Async I/O**: All network operations are async
2. **Batch Processing**: Events processed in batches (configurable via `EVENT_BATCH_SIZE`)
3. **Connection Pooling**: Reuse database connections
4. **Partitioning**: Time-based table partitioning for events
5. **Indexing**: Strategic indexes on frequently queried fields
6. **JSONB**: Fast JSON operations with GIN indexes

## Monitoring

- Health check: `GET /health`
- System stats (admin): `GET /stats`
- Stream metrics (admin): `GET /streams`
- Real-time metrics: `GET /analytics/realtime`

## Configuration

All configuration comes from environment variables (e.g. via Bitwarden). No defaults. See `.github/BITWARDEN_SETUP.md` for setup.

## Production Considerations

1. **Authentication**: API key auth implemented (admin and user keys)
2. **Rate Limiting**: Configurable via `ENABLE_RATE_LIMITING` and `DEFAULT_RATE_LIMIT`
3. **Monitoring**: Add Prometheus/Grafana for production
4. **Logging**: Structured logging with configurable log level
5. **Backups**: Regular PostgreSQL backups
6. **Alerts**: Set up alerts for errors and latency
7. **Deployment**: CI/CD to Docker Hub; CD deploys to Oracle Cloud (see `.github/DEPLOY.md`)
