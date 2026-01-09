# Troubleshooting MySQL Access in Docker Container

## Problem: Access Denied for root@localhost

When you run:
```bash
docker exec -it percona mysql -u root -p -e "SELECT user, host FROM mysql.user WHERE host = '%';"
```

And get: `ERROR 1045 (28000): Access denied for user 'root'@'localhost'`

## Solutions

### Solution 1: Try Without Password (If No Password Set)

Some MySQL containers don't require a password when connecting from within the container:

```bash
# Try without -p flag
docker exec -it percona mysql -u root -e "SELECT user, host FROM mysql.user;"
```

### Solution 2: Check Docker Environment Variables

The MySQL password might be set via environment variables. Check:

```bash
# Check container's environment variables
docker inspect percona | grep -A 30 "Env"

# Or check for MySQL-related env vars
docker exec percona env | grep -i mysql
```

Look for:
- `MYSQL_ROOT_PASSWORD`
- `MYSQL_PASSWORD`
- `MYSQL_ROOT_HOST` (might be set to `%`)

### Solution 3: Try Different Users

MySQL containers often create additional users. Try:

```bash
# Try without password
docker exec -it percona mysql -e "SELECT user, host FROM mysql.user;"

# Or try with a different user that might exist
docker exec -it percona mysql -u mysql -e "SELECT user, host FROM mysql.user;"
```

### Solution 4: Check Container's MySQL Configuration

The container might have a default password or no password. Check:

```bash
# Check if there's a my.cnf or configuration
docker exec percona cat /etc/mysql/my.cnf 2>/dev/null
docker exec percona cat /etc/my.cnf 2>/dev/null

# Check MySQL variables
docker exec percona mysql -u root -e "SHOW VARIABLES LIKE 'validate_password%';" 2>&1
```

### Solution 5: Connect via Docker Port Mapping

If the container has port mapping, you might be able to connect directly:

```bash
# Check port mapping
docker ps | grep percona

# If you see something like "0.0.0.0:3306->3306/tcp", try:
mysql -h 127.0.0.1 -P 3306 -u root -p
```

Use the password from your `.env` file or Docker environment variables.

### Solution 6: Check What Users Actually Exist

Try to see users without authentication:

```bash
# Try to connect and see what happens
docker exec -it percona mysql

# If that doesn't work, check container logs for setup info
docker logs percona | grep -i "root password\|GENERATED ROOT PASSWORD"
```

Many MySQL containers print the generated root password in the logs on first startup.

### Solution 7: Use the Password from Your .env File

If you have `DB_PASSWORD_franchise` in your `.env` file, try that:

```bash
# Use the password from your .env
docker exec -it percona mysql -u root -p<password-from-env> -e "SELECT user, host FROM mysql.user;"
```

Note: No space between `-p` and the password.

### Solution 8: Reset Root Password (If You Have Container Access)

If you can access the container's filesystem, you might be able to reset the password, but this is more complex and may require container restart.

## Most Likely Solutions

1. **Try without password first**:
   ```bash
   docker exec -it percona mysql -u root -e "SELECT user, host FROM mysql.user;"
   ```

2. **Check container logs for password**:
   ```bash
   docker logs percona | grep -i password
   ```

3. **Use password from your .env file** (the one you're using for `DB_PASSWORD_franchise`)

4. **Check Docker environment variables**:
   ```bash
   docker inspect percona | grep MYSQL_ROOT_PASSWORD
   ```

## Once You Find the Right Credentials

After you successfully connect and see the users, look for:
- Users with `host = '%'` (allows any IP)
- Users with `host = '192.168.%'` (allows Docker network)
- Users with `host = '172.%'` (allows Docker network range)

Use one of those users in your `.env` file.

