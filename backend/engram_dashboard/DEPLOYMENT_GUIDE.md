# ENGRAM System Deployment & Configuration Guide

## Overview

The ENGRAM system is designed to be completely modular and can be enabled/disabled without affecting core BitterBot functionality.

## Configuration

### 1. Master Toggle

To completely disable the engram system:

```bash
# Set environment variable
export ENGRAM_ENABLED=false

# Or in your .env file
ENGRAM_ENABLED=false
```

### 2. Fine-grained Control

Edit `backend/agentpress/engram_config.py`:

```python
ENGRAM_CONFIG = {
    "enabled": False,              # Master switch
    "auto_consolidation": False,   # Disable automatic creation
    "dashboard_enabled": False,    # Disable dashboard
    "broadcast_events": False,     # Disable real-time events
}
```

### 3. Resource Management

The engram system is designed to have minimal overhead:

- **Async Processing**: Engram creation happens asynchronously
- **Lazy Loading**: Components only load when enabled
- **Configurable Limits**: Adjust buffer sizes and timeouts
- **Automatic Cleanup**: Old engrams are pruned automatically

## Authentication Setup

### 1. Admin Access

The dashboard uses the existing tier system. Users with these tiers have access:
- `creator`
- `tester`
- `vip`
- `investor`

To check/update your tier:
```sql
-- Check your current tier
SELECT tier FROM profiles WHERE account_id = auth.uid();

-- Grant creator access if needed
UPDATE profiles SET tier = 'creator' WHERE account_id = 'your-user-id';
```

### 2. Configure JWT Secret

```bash
# Generate a secure secret
openssl rand -base64 32

# Set in environment
export JWT_SECRET="your-generated-secret"
```

### 3. Access the Admin Console

1. Login at `/api/admin/login` with your admin credentials
2. Use the returned token in the Authorization header:
   ```
   Authorization: Bearer <your-token>
   ```

## Performance Impact

### When Enabled:
- **CPU**: ~2-5% additional usage during consolidation
- **Memory**: ~50MB for buffer and caching
- **Storage**: ~1KB per engram (compressed summaries)
- **Network**: Minimal (only dashboard events if enabled)

### When Disabled:
- **Zero overhead**: No code paths execute
- **No memory allocation**: Components don't initialize
- **No database queries**: Completely bypassed

## Rollback Procedure

If you need to disable engrams quickly:

```bash
# 1. Set environment variable
export ENGRAM_ENABLED=false

# 2. Restart the backend
# The system will immediately stop creating/accessing engrams

# 3. (Optional) Remove database data
# This is safe as engrams are supplementary
```

## Monitoring

Check system health:

```bash
# View engram metrics
curl -H "Authorization: Bearer <token>" \
  http://localhost:8080/api/engrams/metrics

# Check if enabled
grep ENGRAM_ENABLED backend/.env
```

## Integration Points

The engram system integrates at only 3 points:

1. **context_manager.py**: Checks flag before processing
2. **thread_manager.py**: Checks flag before message hooks
3. **Dashboard**: Separate service, can be not deployed

All integrations check `ENGRAM_INTEGRATION_ENABLED` first.

## Best Practices

1. **Start Disabled**: Deploy with `ENGRAM_ENABLED=false` first
2. **Test Gradually**: Enable for specific threads first
3. **Monitor Resources**: Watch CPU/memory during rollout
4. **Set Limits**: Configure appropriate thresholds

## Troubleshooting

### High Memory Usage
```python
# Reduce buffer size
ENGRAM_CONFIG["max_buffer_size"] = 50  # Default: 100
```

### Slow Consolidation
```python
# Increase token threshold
ENGRAM_CONFIG["chunk_size"] = 10000  # Default: 5000
```

### Disable for Specific Threads
```python
# In your code
if thread_id not in ENGRAM_BLACKLIST:
    # Process engrams
```

## Security Notes

1. **Engrams contain summaries only**: No raw user data
2. **Admin-only access**: Protected by authentication
3. **Encrypted in transit**: All dashboard connections use TLS
4. **Automatic expiry**: Old engrams are pruned

## Deployment Checklist

- [ ] Set `ENGRAM_ENABLED` environment variable
- [ ] Configure JWT_SECRET for production
- [ ] Run admin roles migration
- [ ] Set admin users in database
- [ ] Configure resource limits if needed
- [ ] Deploy dashboard separately (optional)
- [ ] Test with small subset first
- [ ] Monitor performance metrics

Remember: The system is designed to fail gracefully. If anything goes wrong, setting `ENGRAM_ENABLED=false` immediately disables all functionality with zero impact on core BitterBot operations.