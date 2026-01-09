# Invoices Service - Environment Configuration

Copy the variables below to your `.env` file and update with your values.

## Required Environment Variables

```env
# =====================================================
# Invoices Service API - Environment Configuration
# =====================================================

# Environment (local, dev, uat, production)
ENVIRONMENT=local

# =====================================================
# Database Configuration (straker_utils pattern)
# =====================================================

# Franchise Database (PRIMARY - used for invoices)
DB_HOST_franchise=local-percona
DB_PORT_franchise=3306
DB_USER_franchise=root
DB_PASSWORD_franchise=d3v3l0p
DB_NAME_franchise=franchise

# Franchise Readonly
DB_HOST_franchise_readonly=local-percona
DB_PORT_franchise_readonly=3306
DB_USER_franchise_readonly=root
DB_PASSWORD_franchise_readonly=d3v3l0p
DB_NAME_franchise_readonly=franchise

# Sitemanager Database
DB_HOST_sitemanager=local-percona
DB_PORT_sitemanager=3306
DB_USER_sitemanager=root
DB_PASSWORD_sitemanager=d3v3l0p
DB_NAME_sitemanager=sitemanager

# Sitemanager Readonly
DB_HOST_sitemanager_readonly=local-percona
DB_PORT_sitemanager_readonly=3306
DB_USER_sitemanager_readonly=root
DB_PASSWORD_sitemanager_readonly=d3v3l0p
DB_NAME_sitemanager_readonly=sitemanager

# =====================================================
# Redis Configuration
# =====================================================
REDIS_HOST=local-redis
REDIS_PORT=6379

# =====================================================
# Optional - Monitoring
# =====================================================
HEALTH_CHECK_PASSWORD=
ELASTIC_APM_SERVER_URL=
```

## Docker Network Hostnames

| Service | Hostname |
|---------|----------|
| MySQL/Percona | `local-percona` |
| Redis | `local-redis` |
