# PulseStream API Documentation

## Base URL
```
http://localhost:8000
```
Or use `BASE_URL` from your environment (e.g. `https://pulsestream.duckdns.org`).

## Authentication

All endpoints except `GET /` and `GET /health` require API key authentication.

**Header:** `X-API-Key`

**Example:**
```
X-API-Key: NSjCWUmg6q0s67BXaLdNEg==
```

Admin endpoints (`/stats`, `/streams`) require the admin API key. Ingestion and query endpoints accept either admin or user API key.

---

## Miscellaneous Endpoints

### GET /
Root endpoint with API information.

**Response (200 OK):**
```json
{
  "service": "PulseStream",
  "version": "0.1.0",
  "environment": "development",
  "docs": "/docs"
}
```

---

### GET /health
Health check endpoint. No authentication required.

**Response (200 OK / 503 Service Unavailable):**
```json
{
  "status": "healthy",
  "service": "pulsestream",
  "version": "0.1.0",
  "environment": "development",
  "dependencies": {
    "redis": "healthy",
    "database": "healthy"
  }
}
```

---

## Event Ingestion Endpoints

### POST /events
Ingest a single event.

**Headers:** `X-API-Key` (required)

**Request Body:**
```json
{
  "event_type": "user.login",
  "user_id": "user_123",
  "session_id": "session_abc",
  "timestamp": "2026-02-10T10:30:00Z",
  "metadata": {
    "ip_address": "192.168.1.1",
    "user_agent": "Mozilla/5.0"
  },
  "properties": {
    "login_method": "password",
    "success": true
  }
}
```

**Response (202 Accepted):**
```json
{
  "event_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "accepted",
  "timestamp": "2026-02-10T10:30:00Z"
}
```

---

### POST /events/batch
Ingest multiple events in a batch.

**Headers:** `X-API-Key` (required)

**Request Body:**
```json
{
  "events": [
    {
      "event_type": "activity.page_view",
      "user_id": "user_123",
      "properties": {
        "page_url": "/dashboard",
        "page_title": "Dashboard"
      }
    },
    {
      "event_type": "activity.click",
      "user_id": "user_123",
      "properties": {
        "button": "submit"
      }
    }
  ]
}
```

**Response (202 Accepted):**
```json
{
  "accepted": 2,
  "rejected": 0,
  "event_ids": [
    "550e8400-e29b-41d4-a716-446655440000",
    "550e8400-e29b-41d4-a716-446655440001"
  ]
}
```

---

## Query Endpoints

### GET /events
Query events with filters.

**Headers:** `X-API-Key` (required)

**Query Parameters:**
- `event_type` (optional): Filter by event type
- `user_id` (optional): Filter by user ID
- `session_id` (optional): Filter by session ID
- `start_time` (optional): Start time (ISO 8601)
- `end_time` (optional): End time (ISO 8601)
- `limit` (optional): Max results (default: 100, max: 1000)
- `offset` (optional): Pagination offset (default: 0)

**Example:**
```
GET /events?event_type=user.login&limit=10
```

**Response (200 OK):**
```json
[
  {
    "event_id": "550e8400-e29b-41d4-a716-446655440000",
    "event_type": "user.login",
    "user_id": "user_123",
    "session_id": "session_abc",
    "timestamp": "2026-02-10T10:30:00Z",
    "metadata": {},
    "properties": {},
    "created_at": "2026-02-10T10:30:01Z"
  }
]
```

---

### GET /events/{event_id}
Get a specific event by ID.

**Headers:** `X-API-Key` (required)

**Response (200 OK):**
```json
{
  "event_id": "550e8400-e29b-41d4-a716-446655440000",
  "event_type": "user.login",
  "user_id": "user_123",
  "session_id": "session_abc",
  "timestamp": "2026-02-10T10:30:00Z",
  "metadata": {},
  "properties": {},
  "created_at": "2026-02-10T10:30:01Z"
}
```

---

### GET /analytics/realtime
Get real-time metrics and statistics.

**Headers:** `X-API-Key` (required)

**Response (200 OK):**
```json
{
  "timestamp": "2026-02-10T10:35:00Z",
  "events_per_second": 125.5,
  "active_users_1min": 45,
  "active_users_5min": 150,
  "active_users_1hour": 1200,
  "top_events": [
    {"event_type": "activity.page_view", "count": 5000},
    {"event_type": "user.login", "count": 1200}
  ],
  "error_rate": 0.02,
  "avg_processing_latency_ms": 15.5
}
```

---

## Admin Endpoints

Admin endpoints require the **admin API key**.

### GET /stats
Get system-wide statistics.

**Headers:** `X-API-Key` (admin key required)

**Response (200 OK):**
```json
{
  "total_events": 1000000,
  "total_users": 5000,
  "events_by_type": {
    "user.login": 25000,
    "activity.page_view": 500000,
    "transaction.created": 10000
  },
  "streams": {
    "total_streams": 4,
    "total_messages": 100,
    "total_consumers": 0,
    "total_pending_messages": 0,
    "total_backlog": 100,
    "streams": [
      {
        "stream_key": "events:user",
        "length": 25,
        "first_entry_id": "1675000000000-0",
        "last_entry_id": "1675000100000-0",
        "groups": 1
      }
    ]
  },
  "aggregations_1min_count": 1440,
  "aggregations_hourly_count": 24,
  "aggregations_daily_count": 30
}
```

---

### GET /streams
Get Redis Streams information.

**Headers:** `X-API-Key` (admin key required)

**Response (200 OK):**
```json
{
  "total_streams": 4,
  "total_messages": 100,
  "total_consumers": 0,
  "total_pending_messages": 0,
  "total_backlog": 100,
  "streams": [
    {
      "stream_key": "events:user",
      "length": 25,
      "first_entry_id": "1675000000000-0",
      "last_entry_id": "1675000100000-0",
      "groups": 1
    },
    {
      "stream_key": "events:activity",
      "length": 50,
      "first_entry_id": null,
      "last_entry_id": null,
      "groups": 0
    }
  ]
}
```

---

## Event Types

### User Events
- `user.registered` - New user registration
- `user.login` - User authentication
- `user.logout` - Session end
- `user.profile_updated` - Profile changes

### Activity Events
- `activity.page_view` - Page/content views
- `activity.click` - Button/link clicks
- `activity.search` - Search queries
- `activity.feature_used` - Feature interactions

### Transaction Events
- `transaction.created` - New transaction
- `transaction.completed` - Successful completion
- `transaction.failed` - Failed transaction
- `transaction.refunded` - Refund processed

### System Events
- `system.error` - Application errors
- `system.performance` - Performance metrics
- `system.api_call` - API usage tracking

---

## Error Codes

- `200 OK` - Successful query
- `202 Accepted` - Event accepted for processing
- `401 Unauthorized` - Missing or invalid API key
- `403 Forbidden` - Admin permission required
- `404 Not Found` - Resource not found
- `422 Unprocessable Entity` - Validation error
- `500 Internal Server Error` - Server error
- `503 Service Unavailable` - Service unhealthy
