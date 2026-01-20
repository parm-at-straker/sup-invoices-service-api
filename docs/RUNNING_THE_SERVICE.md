# Running the Invoice/Purchase Order Service

This guide explains how to set up and run the Invoice/Purchase Order Service API.

## Prerequisites

- Python 3.12+
- Pipenv (for dependency management)
- MySQL database with `franchise` and `sitemanager` databases
- Access to Straker internal PyPI repository (for `straker-utils` and `buglog` packages)

## Quick Start

### 1. Install Dependencies

```bash
cd /Users/parm/Straker/deploy/straker_nexus/sup-invoices-service-api
pipenv sync --dev
```

This will install all required packages including:
- FastAPI and related dependencies
- SQLAlchemy for database ORM
- MySQL connector
- Testing tools (pytest, coverage)
- Development tools (ruff, mypy)

### 2. Set Up Environment Variables

Create a `.env` file in the project root with the following variables:

```bash
# Environment
ENVIRONMENT=local

# Database - Franchise (primary database for invoices/POs)
DB_HOST_franchise=localhost
DB_PORT_franchise=3306
DB_USER_franchise=root
DB_PASSWORD_franchise=your_password

# Database - Franchise Read-only (for read operations)
DB_HOST_franchise_readonly=localhost
DB_PORT_franchise_readonly=3306
DB_USER_franchise_readonly=root
DB_PASSWORD_franchise_readonly=your_password

# Database - Sitemanager (if needed for user lookups)
DB_HOST_sitemanager=localhost
DB_PORT_sitemanager=3306
DB_USER_sitemanager=root
DB_PASSWORD_sitemanager=your_password

# Database - Sitemanager Read-only
DB_HOST_sitemanager_readonly=localhost
DB_PORT_sitemanager_readonly=3306
DB_USER_sitemanager_readonly=root
DB_PASSWORD_sitemanager_readonly=your_password

# Optional: Health check password (required in production)
HEALTH_CHECK_PASSWORD=

# Optional: Elastic APM for monitoring
ELASTIC_APM_SERVER_URL=
```

**Note**: If running in Docker, use `uat-portal-db-fra02-01.straker.io` or the Docker network IP instead of `localhost` for database connections.

### 3. Run the Service

#### Option A: Direct Python (Recommended for Development)

```bash
pipenv run uvicorn src.main:app --reload --port 12345
```

The `--reload` flag enables auto-reload on code changes, which is useful during development.

#### Option B: Using Pipenv Shell

```bash
# Enter the virtual environment
pipenv shell

# Run the service
uvicorn src.main:app --reload --port 12345
```

### 4. Verify the Service is Running

1. **Health Check**:
   ```bash
   curl http://localhost:12345/health
   ```

2. **API Documentation**:
   Open http://localhost:12345/docs in your browser to see the interactive Swagger UI

3. **Root Endpoint**:
   ```bash
   curl http://localhost:12345/
   # Should return: {"message": "OK"}
   ```

## Running with Docker

### 1. Build the Docker Image

```bash
docker compose build
```

### 2. Run with Docker Compose

```bash
docker compose up -d
```

This will:
- Build the Docker image
- Start the container on port 12345
- Use the `.env` file for environment variables
- Connect to the `local-straker` Docker network

### 3. View Logs

```bash
docker compose logs -f
```

### 4. Stop the Service

```bash
docker compose down
```

## Testing the API

### Using curl

#### List Invoices
```bash
curl -X GET "http://localhost:12345/v1/invoices?page=1&page_size=25" \
  -H "Authorization: Bearer your-token-here"
```

#### Get Invoice by UUID
```bash
curl -X GET "http://localhost:12345/v1/invoices/{invoice-uuid}" \
  -H "Authorization: Bearer your-token-here"
```

#### Create Invoice
```bash
curl -X POST "http://localhost:12345/v1/invoices" \
  -H "Authorization: Bearer your-token-here" \
  -H "Content-Type: application/json" \
  -d '{
    "jobid": 123,
    "currency": "USD",
    "amount": 1000.00,
    "status": "Draft"
  }'
```

#### List Purchase Orders
```bash
curl -X GET "http://localhost:12345/v1/purchase-orders?page=1&page_size=25" \
  -H "Authorization: Bearer your-token-here"
```

### Using the Interactive API Docs

1. Navigate to http://localhost:12345/docs
2. Click "Authorize" and enter your Bearer token
3. Try out the endpoints directly from the browser

## Common Issues and Solutions

### Issue: Database Connection Error

**Error**: `AssertionError: The DB_HOST_franchise environment variable is not set`

**Solution**: Ensure all database environment variables are set in your `.env` file.

### Issue: Access Denied for Database User

**Error**: `Access denied for user 'root'@'192.168.65.1' to database 'franchise'`

**Solution**: Grant permissions to the database user from the Docker network IP:

```sql
-- For MySQL 8.0+
CREATE USER IF NOT EXISTS 'root'@'%' IDENTIFIED BY 'your_password';
GRANT ALL PRIVILEGES ON franchise.* TO 'root'@'%';
GRANT ALL PRIVILEGES ON sitemanager.* TO 'root'@'%';
FLUSH PRIVILEGES;
```

Or for a specific IP (e.g., Docker network):
```sql
CREATE USER IF NOT EXISTS 'root'@'192.168.65.1' IDENTIFIED BY 'your_password';
GRANT ALL PRIVILEGES ON franchise.* TO 'root'@'192.168.65.1';
GRANT ALL PRIVILEGES ON sitemanager.* TO 'root'@'192.168.65.1';
FLUSH PRIVILEGES;
```

### Issue: Module Not Found

**Error**: `ModuleNotFoundError: No module named 'straker_utils'`

**Solution**: Ensure you have access to the Straker internal PyPI repository and that `pipenv sync` completed successfully.

### Issue: Port Already in Use

**Error**: `Address already in use`

**Solution**: Use a different port:
```bash
pipenv run uvicorn src.main:app --reload --port 12346
```

## Development Workflow

1. **Make code changes** in the `src/` directory
2. **The service auto-reloads** (if using `--reload` flag)
3. **Test your changes** using the `/docs` endpoint or curl
4. **Run tests**:
   ```bash
   pipenv run pytest
   ```

## Production Deployment

For production deployment:

1. Set `ENVIRONMENT=production` in your environment variables
2. Set a secure `HEALTH_CHECK_PASSWORD`
3. Configure `ELASTIC_APM_SERVER_URL` for monitoring
4. Use proper database credentials with limited permissions
5. Run without `--reload` flag:
   ```bash
   uvicorn src.main:app --host 0.0.0.0 --port 80
   ```

## API Endpoints Summary

### Invoices
- `GET /v1/invoices` - List invoices (with filtering & pagination)
- `GET /v1/invoices/{uuid}` - Get invoice by UUID
- `POST /v1/invoices` - Create new invoice
- `PUT /v1/invoices/{uuid}` - Update invoice
- `DELETE /v1/invoices/{uuid}` - Delete invoice (soft delete)
- `POST /v1/invoices/{uuid}/approve` - Approve invoice

### Purchase Orders
- `GET /v1/purchase-orders` - List purchase orders (with filtering & pagination)
- `GET /v1/purchase-orders/{uuid}` - Get purchase order by UUID
- `POST /v1/purchase-orders` - Create new purchase order
- `PUT /v1/purchase-orders/{uuid}` - Update purchase order
- `DELETE /v1/purchase-orders/{uuid}` - Delete purchase order (soft delete)
- `POST /v1/purchase-orders/{uuid}/approve` - Approve purchase order for payment

### Health & Documentation
- `GET /health` - Health check endpoint
- `GET /docs` - Interactive API documentation (Swagger UI)
- `GET /redoc` - Alternative API documentation (ReDoc)
- `GET /` - Root endpoint

## Next Steps

- Review the [changelog.md](./changelog.md) for recent changes
- Check the [README.md](../README.md) for more information
- Explore the API using the interactive docs at `/docs`

