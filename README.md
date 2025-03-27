# Fast Resolver API

An asynchronous REST API for DNS and WHOIS operations, with API key authentication and rate limiting.

## Features

- DNS lookup (domain)
- Reverse DNS lookup (IP)
- PTR resolution (IP)
- WHOIS lookup (domain)
- DNSSEC validation support
- API key authentication with api_key/api_secret
- Rate limiting per API key
- Detailed request logging

## Requirements

- Python 3.8+
- Docker and Docker Compose

## Quick Start

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/fast-resolver.git
   cd fast-resolver
   ```

2. Build and run the Docker containers:
   ```
   docker-compose up -d
   ```

3. Access the API documentation:
   ```
   http://localhost:8000/docs
   ```

## Creating an API Key

Use the following endpoint to create a new API key. This requires admin authentication using the `X-Admin-Secret` header with the value from your `API_SECRET_KEY` environment variable:

```
POST /api/v1/admin/api-keys
Headers:
  X-Admin-Secret: your_api_secret_key

{
  "name": "Your API Key Name",
  "rate_limit": 100
}
```

The response will contain the `api_key` and `api_secret` that you need to use for authentication.

## Making API Requests

For regular API endpoints, include the API key and secret in the request headers:

```
X-API-Key: your_api_key
X-API-Secret: your_api_secret
```

For admin endpoints, include the admin secret:

```
X-Admin-Secret: your_api_secret_key
```

### Example Requests

#### DNS Lookup

```
GET /api/v1/dns/lookup?domain=example.com&record_type=A
```

#### DNS Lookup with DNSSEC Validation

```
GET /api/v1/dns/lookup?domain=example.com&record_type=A&dnssec=true
```

#### Reverse DNS Lookup

```
GET /api/v1/dns/reverse?ip=8.8.8.8
```

#### Reverse DNS Lookup with DNSSEC Validation

```
GET /api/v1/dns/reverse?ip=8.8.8.8&dnssec=true
```

#### PTR Resolution

```
GET /api/v1/dns/ptr?ip=8.8.8.8
```

#### PTR Resolution with DNSSEC Validation

```
GET /api/v1/dns/ptr?ip=8.8.8.8&dnssec=true
```

#### WHOIS Lookup

```
GET /api/v1/whois?domain=example.com
```

#### WHOIS Lookup with Full Data (Including Empty Fields)

```
GET /api/v1/whois?domain=example.com&exclude_empty=false
```

#### Admin Endpoints

##### Create API Key
```
POST /api/v1/admin/api-keys
Headers:
  X-Admin-Secret: your_api_secret_key
Body:
{
  "name": "Test API Key",
  "rate_limit": 100
}
```

##### List API Keys
```
GET /api/v1/admin/api-keys
Headers:
  X-Admin-Secret: your_api_secret_key
```

##### Deactivate API Key
```
DELETE /api/v1/admin/api-keys/{api_key}
Headers:
  X-Admin-Secret: your_api_secret_key
```

## Development

To run the application locally without Docker:

1. Create a virtual environment:
   ```
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Make sure Redis is running locally or update the environment variables to point to your Redis instance.

4. Run the application:
   ```
   uvicorn app.main:app --reload
   ```

## Environment Variables

- `REDIS_HOST`: Redis host (default: localhost)
- `REDIS_PORT`: Redis port (default: 6379)
- `API_SECRET_KEY`: Secret key for API key generation 

## Data Persistence

The application stores the following data in Redis:

1. API keys and their configurations (name, rate limits, etc.)
2. Rate limiting information for each API key
3. Indices for managing API keys

The Docker Compose configuration includes a persistent volume (`redis_data`) for Redis to ensure that API keys and other data are preserved across container restarts. Redis is configured with append-only file (AOF) persistence to provide durability.

If you're running outside of Docker, make sure to configure Redis with persistence:
```
redis-server --appendonly yes
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details. 