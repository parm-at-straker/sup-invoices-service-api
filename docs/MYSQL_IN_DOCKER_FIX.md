# Fix: Connecting to MySQL Running in Docker

## Problem

You're getting `Access denied for user 'root'@'192.168.65.1'` when MySQL is running in Docker.

## Understanding the Setup

When MySQL runs in Docker:
- `192.168.65.1` is Docker Desktop's gateway IP (this is normal)
- Connections from your host machine appear to come from this IP
- MySQL needs to allow connections from this IP

## Solutions (Without Using GRANT)

### Solution 1: Use a MySQL User with '%' (Any Host) Permissions

If MySQL was set up with a user that has `%` host permissions, use that user:

**Step 1: Check existing users in MySQL container**

```bash
# Connect to MySQL container
docker exec -it <mysql-container-name> mysql -u root -p

# In MySQL, check users:
SELECT user, host FROM mysql.user;
```

Look for a user with `host = '%'` (allows connections from any host).

**Step 2: Use that user in your .env**

```bash
DB_USER_franchise=user_with_percent_host
DB_PASSWORD_franchise=password
DB_HOST_franchise=127.0.0.1
```

### Solution 2: Use Docker's Internal Network IP

If your MySQL container is on a Docker network, you can connect via that network:

**Step 1: Find MySQL container's network**

```bash
# Find MySQL container
docker ps | grep mysql

# Inspect the container to see its network
docker inspect <mysql-container-name> | grep -A 10 "Networks"
```

**Step 2: Use the container's IP or network alias**

If MySQL is on `local-straker` network (as per docker-compose.yml), you might be able to use:
- Container name as hostname (if on same network)
- Container IP address

However, since you're running the service locally (not in Docker), this won't work directly.

### Solution 3: Use host.docker.internal (If MySQL Container Allows It)

Some Docker setups allow connections via `host.docker.internal`:

```bash
# In your .env, try:
DB_HOST_franchise=host.docker.internal
```

This tells Docker to route to the host machine, which might work if MySQL container is configured for it.

### Solution 4: Check MySQL Container's bind-address

The MySQL container might be configured to only accept connections from specific hosts. Check the container's MySQL config:

```bash
# Check MySQL container's bind-address
docker exec -it <mysql-container-name> cat /etc/mysql/my.cnf
# or
docker exec -it <mysql-container-name> mysql -u root -p -e "SHOW VARIABLES LIKE 'bind_address';"
```

If `bind_address` is `127.0.0.1`, MySQL only accepts connections from within the container. It should be `0.0.0.0` to accept external connections.

### Solution 5: Use MySQL Root User with Existing Permissions

If the MySQL container was set up with environment variables, the root user might already have the right permissions. Try:

```bash
# Use the root password from when the container was created
DB_USER_franchise=root
DB_PASSWORD_franchise=<container-root-password>
DB_HOST_franchise=127.0.0.1
```

### Solution 6: Connect via Docker Port Mapping

If MySQL container has port mapping (e.g., `3306:3306`), you should be able to connect via `127.0.0.1:3306`. The issue is the user permissions.

**Check port mapping:
```bash
docker ps | grep mysql
# Look for "0.0.0.0:3306->3306/tcp" or similar
```

If port is mapped, `127.0.0.1:3306` should work, but you need a user with the right permissions.

### Solution 7: Use a Different MySQL User from Environment

Many MySQL Docker images create users based on environment variables. Check:

```bash
# Check MySQL container's environment
docker inspect <mysql-container-name> | grep -A 20 "Env"
```

Look for `MYSQL_USER`, `MYSQL_PASSWORD`, etc. These users might have broader permissions.

### Solution 8: Run Your Service in Docker Too

If you run the invoices service in Docker (using docker-compose), it can connect to MySQL via Docker's internal network:

```yaml
# In docker-compose.yml, add your service:
services:
  invoices-service:
    # ... your service config
    networks:
      - local-straker  # Same network as MySQL
    environment:
      DB_HOST_franchise: <mysql-container-name>  # Use container name
```

Then connect using the MySQL container's name as the hostname.

## Most Likely Solution

Since MySQL is in Docker and you can't use GRANT:

1. **Find a user with '%' permissions**:
   ```bash
   docker exec -it <mysql-container-name> mysql -u root -p -e "SELECT user, host FROM mysql.user WHERE host = '%';"
   ```

2. **Use that user in your .env file**

3. **Or check the MySQL container's setup** - it might have been configured with a user that already has the right permissions

## Finding Your MySQL Container

```bash
# List all containers
docker ps -a

# Find MySQL container (look for mysql image or name containing 'mysql')
docker ps | grep -i mysql

# Get container name
# Then use it in the commands above
```

## Troubleshooting: Access Denied for root@localhost

If you get `ERROR 1045 (28000): Access denied for user 'root'@'localhost'` when trying to connect:

1. **Try without password**:
   ```bash
   docker exec -it percona mysql -u root -e "SELECT user, host FROM mysql.user;"
   ```

2. **Check container logs for password**:
   ```bash
   docker logs percona | grep -i "root password\|GENERATED"
   ```

3. **Check environment variables**:
   ```bash
   docker inspect percona | grep MYSQL_ROOT_PASSWORD
   ```

4. **Use password from your .env file** (the one in `DB_PASSWORD_franchise`)

5. **Try connecting via port mapping**:
   ```bash
   mysql -h 127.0.0.1 -P 3306 -u root -p
   ```

See `docs/MYSQL_DOCKER_TROUBLESHOOTING.md` for more detailed troubleshooting steps.

## Test Connection

Once you have the right user, test:

```bash
mysql -h 127.0.0.1 -P 3306 -u <user> -p franchise
```

If this works, update your `.env` and restart the service.

