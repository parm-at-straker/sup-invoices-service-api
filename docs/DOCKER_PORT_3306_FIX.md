# Fix: Docker Intercepting Port 3306

## Confirmed Issue

Your `lsof` output shows:
```
com.docke 70859 parm  206u  IPv6 ... TCP *:mysql (LISTEN)
```

This confirms Docker Desktop is intercepting MySQL connections on port 3306, which is why you're getting `192.168.65.1` errors.

## Solutions (No GRANT Required)

### Solution 1: Stop Docker Desktop (Simplest)

**If you don't need Docker running right now:**

1. Quit Docker Desktop completely
2. Verify it's stopped:
   ```bash
   lsof -i :3306
   # Should show mysqld, not com.docker
   ```
3. Restart your service

### Solution 2: Use Different MySQL Port (Recommended if you need Docker)

Configure MySQL to use a different port (e.g., 3307) to avoid Docker's interception:

**Step 1: Update MySQL Configuration**

```bash
# On macOS with Homebrew MySQL, edit the config:
nano /opt/homebrew/etc/my.cnf
# or
nano /usr/local/etc/my.cnf
```

Add or modify:
```ini
[mysqld]
port = 3307
```

**Step 2: Restart MySQL**

```bash
# Homebrew MySQL
brew services restart mysql
# or
mysql.server restart
```

**Step 3: Update Your .env File**

```bash
DB_PORT_franchise=3307
DB_PORT_franchise_readonly=3307
DB_PORT_sitemanager=3307
DB_PORT_sitemanager_readonly=3307
```

**Step 4: Verify New Port**

```bash
lsof -i :3307
# Should show mysqld
```

**Step 5: Test Connection**

```bash
mysql -h 127.0.0.1 -P 3307 -u root -p franchise
```

### Solution 3: Configure Docker to Not Intercept Port 3306

**Option A: Docker Desktop Settings**

1. Open Docker Desktop
2. Go to Settings (gear icon)
3. Navigate to Resources → Network
4. Check for port forwarding or network settings
5. Remove or disable port 3306 forwarding if present

**Option B: Docker Compose Network**

If you have a `docker-compose.yml` that's forwarding port 3306, modify it:

```yaml
services:
  # Remove or change the port mapping if it's forwarding 3306
  # ports:
  #   - "3306:3306"  # Remove this
```

### Solution 4: Use MySQL Socket (Advanced)

If MySQL is on the same machine, you could use Unix socket instead of TCP/IP, but this requires modifying the connection method and may not be supported by `DBEnginePool`.

### Solution 5: Temporary - Remove Sitemanager from Pool

Since you primarily need `franchise` database, you can temporarily remove `sitemanager` to avoid connection attempts:

```python
# In src/database.py
engines = DBEnginePool(
    (
        "franchise",
        "franchise_readonly",
    ),
    dbapi="mysqlconnector",
)
```

This won't fix the root cause but will allow the service to work if you only need franchise database.

## Recommended Approach

**If you need Docker running**: Use Solution 2 (different MySQL port) - it's the cleanest long-term solution.

**If you don't need Docker right now**: Use Solution 1 (stop Docker) - it's the quickest fix.

## Verify the Fix

After applying a solution, verify:

```bash
# Check what's on port 3306 (or your new port)
lsof -i :3306
# or
lsof -i :3307

# Test MySQL connection
mysql -h 127.0.0.1 -P 3306 -u root -p franchise
# or with new port
mysql -h 127.0.0.1 -P 3307 -u root -p franchise
```

Then restart your service - it should work!

