# Fixing Database Connection Issues Without GRANT

If you're getting `Access denied for user 'root'@'192.168.65.1'` errors, here are solutions that don't require MySQL GRANT statements.

## Quick Fix: Use 127.0.0.1

The most common solution is to explicitly use `127.0.0.1` in your `.env` file:

```bash
# In your .env file
DB_HOST_franchise=127.0.0.1
DB_HOST_franchise_readonly=127.0.0.1
DB_HOST_sitemanager=127.0.0.1
DB_HOST_sitemanager_readonly=127.0.0.1
```

**Why this works**: `127.0.0.1` forces a direct localhost connection, bypassing Docker network routing that might be causing the `192.168.65.1` IP issue.

## Check Your Current Setup

1. **Verify your .env file**:
   ```bash
   cat .env | grep DB_HOST
   ```

2. **Check if Docker is interfering**:
   ```bash
   # Check if Docker Desktop is running
   docker ps

   # If Docker is running and you don't need it, stop it:
   # Docker Desktop -> Quit Docker Desktop
   ```

3. **Test direct MySQL connection**:
   ```bash
   mysql -h 127.0.0.1 -u root -p franchise
   ```

   If this works, your `.env` should use `127.0.0.1`.

## Alternative: Use Existing User with Localhost Access

If you have another MySQL user that already works with `localhost`, use that:

```bash
# In your .env file
DB_USER_franchise=your_working_user
DB_PASSWORD_franchise=your_working_password
DB_HOST_franchise=127.0.0.1
```

## Verify MySQL Configuration

Check if MySQL is configured to accept localhost connections:

```bash
# On macOS with Homebrew
cat /opt/homebrew/etc/my.cnf

# Look for bind-address - it should be:
# bind-address = 127.0.0.1
```

If `bind-address` is `0.0.0.0`, MySQL accepts connections from all interfaces, which might cause routing through Docker.

## Test Connection Before Running Service

Test your database connection settings:

```bash
# Load your .env file
export $(cat .env | xargs)

# Test connection
mysql -h ${DB_HOST_franchise} -P ${DB_PORT_franchise} -u ${DB_USER_franchise} -p${DB_PASSWORD_franchise} franchise -e "SELECT 1"
```

If this works, the service should work too.

## Most Likely Solution

For most cases, simply changing `localhost` to `127.0.0.1` in your `.env` file will fix the issue:

```bash
# Change this:
DB_HOST_franchise=localhost

# To this:
DB_HOST_franchise=127.0.0.1
```

Then restart your service.

## If You're Already Using 127.0.0.1

If you're already using `127.0.0.1` but still getting `192.168.65.1` errors, Docker Desktop is likely intercepting the connection. Try these solutions:

### Solution 1: Stop Docker Desktop

Docker Desktop on macOS can intercept localhost connections. Try stopping it:

```bash
# Check if Docker is running
docker ps

# Stop Docker Desktop:
# 1. Click Docker icon in menu bar
# 2. Select "Quit Docker Desktop"
# 3. Wait for it to fully quit
# 4. Restart your service
```

### Solution 2: Check MySQL's Actual Connection Source

MySQL might be seeing the connection differently. Check what MySQL sees:

```sql
-- Connect to MySQL and run:
SELECT user, host FROM mysql.user WHERE user = 'root';
SHOW PROCESSLIST;
```

This shows what hosts MySQL allows and what connections it sees.

### Solution 3: Use a Different MySQL User

If you have another user that works, use that:

```bash
# Check what users exist and what hosts they can connect from
mysql -u root -p -e "SELECT user, host FROM mysql.user;"

# Use a user that has '%' (any host) or 'localhost' access
DB_USER_franchise=existing_user_with_access
```

### Solution 4: Check Network Routing

On macOS, Docker can create network interfaces that intercept connections:

```bash
# Check network interfaces
ifconfig | grep -A 5 "192.168.65"

# If you see Docker interfaces, they might be routing your connections
```

### Solution 5: Force Direct Connection with Connection Arguments

You might need to add connection arguments to force a direct connection. However, `DBEnginePool` from `straker_utils` may not support this directly. Check if there's a way to pass connection arguments.

### Solution 6: Use MySQL Socket Instead of TCP/IP

If MySQL is on the same machine, you could use Unix socket, but this requires MySQL to be configured for socket connections and the connection library to support it.

### Solution 7: Check MySQL Bind Address

Verify MySQL is actually listening on 127.0.0.1:

```bash
# Check what MySQL is listening on
netstat -an | grep 3306
# or
lsof -i :3306
```

You should see `127.0.0.1:3306` or `*:3306`. If you see `0.0.0.0:3306`, MySQL is accepting from all interfaces.

### Solution 8: Stop Docker Desktop (Most Likely Fix)

**Root Cause Found**: Docker Desktop is intercepting port 3306 (MySQL port). The `lsof` command shows `com.docker.backend` is listening on port 3306, which routes all MySQL connections through Docker's network.

**Fix**: Stop Docker Desktop:

1. Click the Docker icon in your macOS menu bar
2. Select "Quit Docker Desktop"
3. Wait for it to fully quit (check Activity Monitor if needed)
4. Verify Docker is stopped:
   ```bash
   lsof -i :3306
   # Should NOT show com.docker.backend
   ```
5. Restart your service

**Alternative**: If you need Docker running, you can:
- Configure Docker to not intercept port 3306 (Docker Desktop Settings → Resources → Advanced)
- Or use a different MySQL port (requires MySQL configuration change)

### Solution 9: Temporary Workaround - Remove Sitemanager

Since the service primarily uses `franchise` database, you can temporarily remove `sitemanager` from the pool to avoid connection attempts:

```python
# In src/database.py, temporarily use only franchise:
engines = DBEnginePool(
    (
        "franchise",
        "franchise_readonly",
    ),
    dbapi="mysqlconnector",
)
```

This won't fix the root cause but will allow the service to work if you only need franchise database access.

