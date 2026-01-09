# Fix: Docker Intercepting MySQL Connections

## Problem

You're getting `Access denied for user 'root'@'192.168.65.1'` even though you're using `127.0.0.1` in your `.env` file.

## Root Cause

Docker Desktop is intercepting MySQL connections on port 3306. When you check what's listening on port 3306:

```bash
lsof -i :3306
```

You'll see `com.docker.backend` is listening, which means Docker is routing all MySQL connections through its network (hence the `192.168.65.1` IP).

## Solution: Stop Docker Desktop

The simplest fix is to stop Docker Desktop:

1. **Quit Docker Desktop**:
   - Click Docker icon in macOS menu bar
   - Select "Quit Docker Desktop"
   - Wait for it to fully quit

2. **Verify Docker is stopped**:
   ```bash
   lsof -i :3306
   ```

   You should now see MySQL (mysqld) listening, not Docker.

3. **Restart your service**:
   ```bash
   pipenv run uvicorn src.main:app --reload --port 12346
   ```

## Alternative: Keep Docker Running

If you need Docker running, you have these options:

### Option A: Configure Docker to Not Intercept Port 3306

1. Open Docker Desktop
2. Go to Settings → Resources → Advanced
3. Check port forwarding/exposure settings
4. Ensure port 3306 is not being forwarded/intercepted

### Option B: Use a Different MySQL Port

1. Configure MySQL to listen on a different port (e.g., 3307)
2. Update your `.env` file:
   ```bash
   DB_PORT_franchise=3307
   DB_PORT_franchise_readonly=3307
   ```

### Option C: Use MySQL in Docker

If MySQL is actually running in Docker, connect to it properly:
- Use Docker's network IP
- Or use Docker's port mapping
- Or connect via Docker exec

## Verify the Fix

After stopping Docker Desktop, test the connection:

```bash
# Should work now
mysql -h 127.0.0.1 -u root -p franchise
```

Then restart your service - it should work!

