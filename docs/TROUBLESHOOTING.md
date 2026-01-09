# Troubleshooting Guide

## ModuleNotFoundError: No module named 'elasticapm'

### Problem
When running the service, you get an error:
```
ModuleNotFoundError: No module named 'elasticapm'
```

### Solution

The issue is that dependencies haven't been installed or you're not using the pipenv virtual environment. Follow these steps:

#### Option 1: Install Dependencies (Recommended)

```bash
cd /Users/parm/Straker/deploy/straker_nexus/sup-invoices-service-api
pipenv install
```

This will install all dependencies including `elastic-apm`.

#### Option 2: Use Pipenv to Run (Recommended)

Always use `pipenv run` to ensure you're using the correct virtual environment:

```bash
pipenv run uvicorn src.main:app --reload --port 12346
```

#### Option 3: Activate Virtual Environment First

```bash
# Activate the virtual environment
pipenv shell

# Then run uvicorn normally
uvicorn src.main:app --reload --port 12346
```

### Why This Happens

- Running `uvicorn` directly (without `pipenv run`) uses your system Python, which doesn't have the dependencies installed
- The dependencies are installed in the pipenv virtual environment, not globally
- Always use `pipenv run` or activate the shell first

### Verify Installation

Check if dependencies are installed:

```bash
pipenv run python -c "import elasticapm; print('elasticapm installed')"
```

If this fails, run `pipenv install` again.

## PermissionError with .env file

### Problem
```
PermissionError: [Errno 1] Operation not permitted: '/Users/parm/Straker/deploy/straker_nexus/sup-invoices-service-api/.env'
```

### Solution

1. Check file permissions:
   ```bash
   ls -la .env
   ```

2. Fix permissions if needed:
   ```bash
   chmod 644 .env
   ```

3. Or create a new .env file:
   ```bash
   # Remove the problematic .env file
   rm .env

   # Create a new one
   touch .env
   # Then add your environment variables
   ```

## Database Connection Issues

### Problem 1: Missing Environment Variables
```
AssertionError: The DB_HOST_franchise environment variable is not set
```

### Solution

Ensure your `.env` file contains all required database variables:
- `DB_HOST_franchise`
- `DB_PORT_franchise`
- `DB_USER_franchise`
- `DB_PASSWORD_franchise`
- And the same for `franchise_readonly`, `sitemanager`, and `sitemanager_readonly`

See [RUNNING_THE_SERVICE.md](./RUNNING_THE_SERVICE.md) for the complete list.

### Problem 2: Access Denied for Database
```
Access denied for user 'root'@'192.168.65.1' to database 'sitemanager'
```

### Solution

The Invoice/Purchase Order Service primarily uses the `franchise` database. The `sitemanager` database is optional and only needed if you're doing user lookups.

**Option 1: Grant Permissions (Recommended if you need sitemanager access)**

Connect to MySQL and grant permissions:

```sql
-- For MySQL 8.0+ - Grant access from any host
CREATE USER IF NOT EXISTS 'root'@'%' IDENTIFIED BY 'your_password';
GRANT ALL PRIVILEGES ON franchise.* TO 'root'@'%';
GRANT ALL PRIVILEGES ON sitemanager.* TO 'root'@'%';
FLUSH PRIVILEGES;
```

Or for a specific IP (e.g., Docker network IP `192.168.65.1`):

```sql
CREATE USER IF NOT EXISTS 'root'@'192.168.65.1' IDENTIFIED BY 'your_password';
GRANT ALL PRIVILEGES ON franchise.* TO 'root'@'192.168.65.1';
GRANT ALL PRIVILEGES ON sitemanager.* TO 'root'@'192.168.65.1';
FLUSH PRIVILEGES;
```

**Option 2: Remove sitemanager from database pool (if not needed)**

If you don't need sitemanager access, you can modify `src/database.py` to only include franchise databases:

```python
engines = DBEnginePool(
    (
        "franchise",
        "franchise_readonly",
    ),
    dbapi="mysqlconnector",
)
```

**Note**: The health check has been updated to only check the `franchise` database, so the service will work even if `sitemanager` is not accessible.

### Problem 2b: Access Denied from Docker Network IP (192.168.65.1)

**Error**: `Access denied for user 'root'@'192.168.65.1' (using password: YES)`

This happens when your connection is being routed through Docker's network even though you're running locally. The IP `192.168.65.1` is Docker Desktop's gateway IP on macOS.

#### Solutions (Without Using GRANT):

**Option 1: Use 127.0.0.1 Explicitly**

In your `.env` file, use `127.0.0.1` instead of `localhost`:

```bash
DB_HOST_franchise=127.0.0.1
DB_HOST_franchise_readonly=127.0.0.1
```

**Option 2: Use a Different Database User**

If you have another MySQL user that already has `localhost` access, use that instead:

```bash
DB_USER_franchise=your_existing_user
DB_PASSWORD_franchise=your_existing_password
```

**Option 3: Check MySQL Bind Address**

Ensure MySQL is listening on the correct interface. Check your MySQL configuration:

```bash
# On macOS with Homebrew MySQL:
cat /opt/homebrew/etc/my.cnf
# or
cat /usr/local/etc/my.cnf
```

Look for `bind-address`. It should be:
```
bind-address = 127.0.0.1
```

If it's `0.0.0.0`, MySQL accepts connections from all interfaces, which might be causing the Docker routing issue.

**Option 4: Use Unix Socket (MySQL on Same Machine)**

If MySQL is running locally, you can connect via Unix socket instead of TCP/IP. However, this requires modifying the connection method, which `DBEnginePool` may not support directly.

**Option 5: Check Docker Network Interference**

If you have Docker Desktop running, it might be intercepting network connections. Try:

1. Stop Docker Desktop temporarily
2. Or disconnect from Docker networks:
   ```bash
   # Check if you're connected to Docker networks
   ifconfig | grep 192.168.65
   ```

**Option 6: Use SSH Tunneling**

If you have SSH access to a machine with MySQL access:

```bash
ssh -L 3306:localhost:3306 user@mysql-server
```

Then connect to `127.0.0.1:3306` in your `.env` file.

**Option 7: Verify Current MySQL User Permissions**

Check what hosts your current user can connect from:

```sql
SELECT user, host FROM mysql.user WHERE user = 'root';
```

If you see `root@localhost` but not `root@192.168.65.1`, that's why it's failing. You can either:
- Use a user that has `%` (any host) access
- Or ensure your connection uses `localhost`/`127.0.0.1` properly

### Problem 2c: Docker Intercepting Port 3306 (Confirmed)

**Error**: `Access denied for user 'root'@'192.168.65.1'` even with `127.0.0.1` in `.env`

**Diagnosis**: Run `lsof -i :3306` and you'll see `com.docker.backend` listening instead of `mysqld`.

**Root Cause**: Docker Desktop is intercepting MySQL connections on port 3306, routing them through Docker's network.

**Solutions (No GRANT Required)**:

1. **Stop Docker Desktop** (if you don't need it):
   - Quit Docker Desktop completely
   - Verify: `lsof -i :3306` should show `mysqld`, not `com.docker`
   - Restart your service

2. **Use Different MySQL Port** (if you need Docker):
   - Configure MySQL to use port 3307 (or another port)
   - Update your `.env` file with the new port
   - See `docs/DOCKER_PORT_3306_FIX.md` for detailed steps

3. **Configure Docker** to not intercept port 3306 (Docker Desktop Settings)

See `docs/DOCKER_PORT_3306_FIX.md` for complete instructions.

### Problem 2d: MySQL Running in Docker

**Error**: `Access denied for user 'root'@'192.168.65.1'` when MySQL is running in Docker

**Root Cause**: When MySQL runs in Docker, connections from your host machine appear to come from Docker's gateway IP (`192.168.65.1`). The MySQL user needs permissions for this IP, or you need to use a user with `%` (any host) permissions.

**Solutions (No GRANT Required)**:

1. **Use a MySQL user with '%' permissions**:
   ```bash
   # Check what users exist in MySQL container
   docker exec -it <mysql-container-name> mysql -u root -p -e "SELECT user, host FROM mysql.user WHERE host = '%';"
   ```
   Use a user that has `host = '%'` in your `.env` file.

2. **Use the MySQL root user** if it was set up with Docker environment variables (might already have permissions)

3. **Check MySQL container's bind-address** - should be `0.0.0.0` to accept external connections

4. **Run your service in Docker too** - then it can connect via Docker's internal network using container names

See `docs/MYSQL_IN_DOCKER_FIX.md` for detailed instructions.

### Problem 3: Unknown Column Error
```
Unknown column 'franchise.obj_tp_job_invoice.withholding_tax' in 'field list'
```

### Solution

This error occurs when the model includes columns that don't exist in the actual database table. The XML definitions may include properties that haven't been added to the database schema yet.

**Fixed**: The `withholding_tax` column has been removed from the Invoice and InvoiceGroup models as it doesn't exist in the database.

If you encounter similar errors for other columns:
1. Check if the column actually exists in the database
2. If it doesn't exist, comment it out in the model file (`src/invoices/models.py`)
3. Restart the service

To check what columns exist in a table:
```sql
DESCRIBE franchise.obj_tp_job_invoice;
-- or
SHOW COLUMNS FROM franchise.obj_tp_job_invoice;
```

## Port Already in Use

### Problem
```
Address already in use
```

### Solution

Use a different port:
```bash
pipenv run uvicorn src.main:app --reload --port 12347
```

Or find and kill the process using the port:
```bash
# Find the process
lsof -ti:12346

# Kill it
kill -9 $(lsof -ti:12346)
```

## Import Errors

### Problem
Various `ModuleNotFoundError` for different modules

### Solution

1. Ensure you're using pipenv:
   ```bash
   pipenv install
   ```

2. Verify the virtual environment is active:
   ```bash
   pipenv --venv
   ```

3. Reinstall dependencies:
   ```bash
   pipenv sync --dev
   ```

## Access to Straker Internal PyPI

### Problem
```
Could not find a version that satisfies the requirement straker-utils
```

### Solution

You need access to the Straker internal PyPI repository. The Pipfile includes:
```
[[source]]
url = "https://mgmt-k8s-pypi-fra02.straker.io/simple"
```

Ensure you have:
1. Network access to the internal PyPI server
2. Proper authentication if required
3. VPN connection if working remotely

