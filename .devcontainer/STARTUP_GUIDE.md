# 🚀 CogniForge Startup Guide

## ⏱️ Startup Timeline

When you open this project in GitHub Codespaces, the following happens:

1. **Container Creation** (0-30s)
   - Docker container is built and started
   - Dev Container configuration is applied

2. **Post-Create Hook** (30-45s)
   - Environment variables are generated from secrets
   - `.env` file is created automatically

3. **Post-Start Hook** (45-90s)
   - Background bootstrap process starts
   - Python dependencies are installed
   - Database migrations run
   - Admin user is seeded
   - Uvicorn server launches

4. **Application Ready** (90-120s)
   - Health check passes
   - Application is accessible at port 8000

## 🔍 Monitoring Startup

### Check Logs
```bash
tail -f .superhuman_bootstrap.log
```

### Check Application Status
```bash
curl http://localhost:8000/health
```

### Check Running Processes
```bash
ps aux | grep uvicorn
```

## ⚠️ Common Issues

### Issue: "Browser crashes immediately"
**Cause**: Multiple instances of the app running simultaneously
**Solution**: This has been fixed by removing duplicate startup commands

### Issue: "Application not responding"
**Cause**: Application still starting up
**Solution**: Wait 2-3 minutes after container creation, then refresh

### Issue: "Port 8000 not accessible"
**Cause**: Uvicorn hasn't started yet
**Solution**: Check logs with `tail -f .superhuman_bootstrap.log`

## 🎯 Best Practices

1. **Wait for Full Startup**: Don't open the browser until you see "Application is healthy and ready!" in logs
2. **Use Production Build**: The app now uses React production builds for better performance
3. **Monitor Resources**: Use `top` or `htop` to monitor CPU/memory usage
4. **Check Health Endpoint**: Always verify `/health` returns 200 before using the app

## 🛠️ Manual Start (if needed)

If automatic startup fails, you can manually start the application:

```bash
cd /app
bash scripts/setup_dev.sh
```

## 📊 Performance Optimizations Applied

- ✅ Removed duplicate startup commands
- ✅ Changed React from development to production build
- ✅ Changed auto-open browser to notification only
- ✅ Added health check wait before declaring ready
- ✅ Added 2-second initialization delay
- ✅ Optimized startup sequence

## 🔗 Useful Commands

```bash
# View application logs
tail -f .superhuman_bootstrap.log

# Restart application
pkill -f uvicorn && bash scripts/setup_dev.sh

# Check port status
netstat -tlnp | grep 8000

# View environment variables
env | grep -E "DATABASE|SECRET|ADMIN"
```

---

**Last Updated**: 2025-12-31
**Version**: v4.2-Optimized
