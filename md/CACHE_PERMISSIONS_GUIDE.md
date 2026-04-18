# Cache File Permission Issues - Troubleshooting Guide

## Problem
You're seeing errors like:
```
ERROR | Error loading cache file: [Errno 13] Permission denied
ERROR | Error saving cache file: [Errno 13] Permission denied
```

This happens when the cache file or directory doesn't have proper permissions for the user running the application.

## Solutions

### 1. Fix Existing Cache File Permissions (Quick Fix)

```bash
# Navigate to your project directory
cd /path/to/socialMediaJobs

# Fix permissions for the cache file
chmod 664 temp/cache.json

# Fix permissions for the temp directory
chmod 755 temp/

# If you need group access (recommended for servers)
chgrp your-group temp/cache.json
```

### 2. Fix Ownership (If file owned by different user)

```bash
# Change ownership to current user
sudo chown $USER:$USER temp/cache.json

# Or change to specific user/group
sudo chown username:groupname temp/cache.json
```

### 3. Complete Reset (If corrupted or inaccessible)

```bash
# Remove the cache file and let it recreate
rm temp/cache.json

# Ensure temp directory has proper permissions
chmod 755 temp/

# Run your application - it will create a new cache file
```

### 4. Set Up Proper Permissions for Production Server

```bash
# Create a dedicated group for your application
sudo groupadd socialmedia-app

# Add your application user to the group
sudo usermod -a -G socialmedia-app your-username

# Set directory ownership and permissions
sudo chown -R your-username:socialmedia-app temp/
sudo chmod 775 temp/
sudo chmod 664 temp/*.json

# Ensure new files inherit group ownership
sudo chmod g+s temp/
```

### 5. For Systemd Services

If running as a systemd service, ensure the service user has proper permissions:

```ini
[Service]
User=your-app-user
Group=your-app-group
UMask=0002
```

Then:
```bash
sudo chown -R your-app-user:your-app-group /path/to/socialMediaJobs/temp/
sudo chmod -R 775 /path/to/socialMediaJobs/temp/
```

## Verification

Check current permissions:
```bash
ls -la temp/cache.json
```

Expected output (good permissions):
```
-rw-rw-r-- 1 username groupname 12345 Sep 29 10:00 temp/cache.json
```

## Prevention

The cache now automatically sets proper permissions (0o664 for files, 0o755 for directories), but you need to ensure:

1. **Parent directory is writable** by the application user
2. **File is owned** by the application user or group
3. **umask** is set appropriately (usually 0002 or 0022)

## Common Scenarios

### Multiple Users/Processes
If multiple users need to access the cache:
```bash
# Use a common group
sudo chgrp shared-group temp/cache.json
sudo chmod 664 temp/cache.json
```

### Docker Containers
Ensure proper volume permissions:
```yaml
volumes:
  - ./temp:/app/temp:rw
```

### Cron Jobs
Ensure cron runs as the correct user:
```bash
# In crontab
0 * * * * /path/to/venv/bin/python /path/to/script.py
```

## Still Having Issues?

Check:
1. SELinux context (if enabled): `ls -Z temp/cache.json`
2. AppArmor profiles (if enabled)
3. Disk space: `df -h`
4. File system permissions: `mount | grep /path/to/project`

## Contact
If permission issues persist, check your server's security policies and consult your system administrator.
