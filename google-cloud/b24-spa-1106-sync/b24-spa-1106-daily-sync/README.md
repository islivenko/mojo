# B24 SPA 1106 Daily Sync

## Overview

Scheduled Cloud Function that runs daily to synchronize all active Sprawy cudzoziemców (SPA 1106) items. The function fetches all active items from Bitrix24 and publishes individual sync messages to Pub/Sub for parallel processing by the worker.

## Architecture

```
Cloud Scheduler (daily at 03:00 Warsaw time)
           ↓
b24-spa-1106-daily-sync (HTTP Function)
           ↓ (publishes N messages)
Pub/Sub: b24-spa-1106-sync-events
           ↓
b24-spa-1106-sync-worker (processes each item)
```

## Configuration

### Environment Variables

- `PROJECT_ID`: `mojo-478621`
- `B24_DOMAIN`: `mojo.bitrix24.pl`
- `ACCESS_TOKEN_SECRET`: `b24-access-token`
- `TOPIC_NAME`: `b24-spa-1106-sync-events`
- `SPA_SPRAWY_ID`: `1106`

### Schedule

- **Cron**: `0 3 * * *` (03:00 every day)
- **Timezone**: Europe/Warsaw
- **Scheduler Job**: `b24-spa-1106-daily-sync-job`

### Resources

- **Memory**: 256MB
- **Timeout**: 300s (5 minutes)
- **Runtime**: Python 3.12
- **Region**: europe-central2

## Functionality

### 1. Fetch Active Items

The function fetches all Sprawy cudzoziemców from Bitrix24 and filters only **ACTIVE** items:

**Active stages**: NEW, IN_PROGRESS, and any non-final stages
**Final stages** (excluded): SUCCESS, FAIL, FAILURE, LOSE, APOLOGY

```python
def is_active_stage(stage_id: str) -> bool:
    """Check if stageId represents an active (non-final) stage."""
    if not stage_id:
        return True
    
    parts = stage_id.split(':')
    if len(parts) < 2:
        return True
    
    stage_name = parts[-1].upper()
    return stage_name not in FINAL_STAGES
```

### 2. Publish Sync Messages

For each active Sprawy, the function publishes a message to Pub/Sub:

```json
{
  "event": "daily_sync",
  "id": "18",
  "contact_id": "194",
  "entity_type_id": "1106",
  "is_contact_event": false,
  "bitrix_event": "DAILY_SYNC",
  "timestamp": 1768756789.123
}
```

### 3. Parallel Processing

The worker receives these messages and processes each Sprawy individually, performing full synchronization:

1. **Podstawy pobytu** (SPA 1042) - links + dates
2. **Uprawnienia do pracy** (SPA 1046) - links + dates
3. **Procesy legalizacyjne** (SPA 1110) - links
4. **Contact passport fields** - number + validity date

## Deployment

### Deploy Function

```bash
cd /Users/Dev/mojo_agency/google-cloud/b24-spa-1106-sync/b24-spa-1106-daily-sync
./deploy.sh
```

This will:
1. Deploy the Cloud Function
2. Create/update the Cloud Scheduler job
3. Configure the schedule and timezone

### Manual Testing

Test the function manually:

```bash
curl -X POST https://b24-spa-1106-daily-sync-4fobf7itaq-lm.a.run.app
```

Expected response:

```json
{
  "status": "ok",
  "total_active": 11,
  "published": 11,
  "elapsed_ms": 1418
}
```

### Run Scheduler Job Now

Trigger the scheduler job manually:

```bash
gcloud scheduler jobs run b24-spa-1106-daily-sync-job \
  --location=europe-central2 \
  --project=mojo-478621
```

## Monitoring

### Check Logs

View function logs:

```bash
gcloud functions logs read b24-spa-1106-daily-sync \
  --region=europe-central2 \
  --project=mojo-478621 \
  --limit=50
```

### Check Scheduler Status

View scheduler job status:

```bash
gcloud scheduler jobs describe b24-spa-1106-daily-sync-job \
  --location=europe-central2 \
  --project=mojo-478621
```

### View Execution History

```bash
gcloud scheduler jobs list \
  --location=europe-central2 \
  --project=mojo-478621
```

## Example Output

### Successful Execution

```
============================================================
=== B24 SPA 1106 DAILY SYNC STARTED ===
============================================================
📋 Fetching all Sprawy cudzoziemców from Bitrix24...
   Fetched 50 items (total: 50)
   Fetched 0 items (total: 50)
📊 Total: 50, Active: 11

📋 Items to sync:
   - ID=18: DARAI BISHNU LAL (contact: 194)
   - ID=22: KOWALSKI JAN (contact: 198)
   ... and 9 more

📤 Publishing 11 messages to Pub/Sub...
✅ Published 11/11 messages

============================================================
=== DAILY SYNC COMPLETED ===
   Total active: 11
   Published: 11
   Duration: 1418ms
============================================================
```

## Error Handling

### No Active Items

If no active Sprawy are found:

```json
{
  "status": "ok",
  "message": "No active items to sync",
  "total": 0,
  "elapsed_ms": 234
}
```

### API Error

If Bitrix24 API fails:

```json
{
  "status": "error",
  "message": "API Error: INVALID_TOKEN",
  "elapsed_ms": 567
}
```

### Pub/Sub Error

If message publishing fails, the function logs the error but continues with other items:

```
❌ Failed to publish for item 18: Timeout exceeded
✅ Published 10/11 messages
```

## Cost Estimation

### Daily Execution

- **Function invocations**: 1/day
- **Execution time**: ~1-2 seconds
- **Pub/Sub messages**: ~10-50/day (depends on active items)

### Monthly Cost

- **Cloud Functions**: ~$0.01/month
- **Cloud Scheduler**: $0.10/month
- **Pub/Sub**: ~$0.01/month
- **Total**: **~$0.12/month**

## Deployment Status

- **Function**: `b24-spa-1106-daily-sync`
- **URL**: https://b24-spa-1106-daily-sync-4fobf7itaq-lm.a.run.app
- **Revision**: `00002-coc`
- **Status**: ✅ Active
- **Deployed**: 2026-01-18 17:24:03 UTC
- **Scheduler**: ✅ Enabled (next run: 03:00 Warsaw time)

## Testing Results

**Test Date**: 2026-01-18 17:25:00 UTC

**Result**:
- ✅ Found 11 active Sprawy
- ✅ Published 11 messages to Pub/Sub
- ✅ Execution time: 1418ms
- ✅ All messages processed successfully by worker

## Troubleshooting

### Function Returns Error

1. Check access token in Secret Manager:
   ```bash
   gcloud secrets versions access latest --secret=b24-access-token --project=mojo-478621
   ```

2. Verify Bitrix24 domain is accessible:
   ```bash
   curl https://mojo.bitrix24.pl/rest/
   ```

3. Check function logs for detailed error messages

### Scheduler Not Running

1. Verify scheduler job is enabled:
   ```bash
   gcloud scheduler jobs describe b24-spa-1106-daily-sync-job \
     --location=europe-central2
   ```

2. Check scheduler execution history in Cloud Console

3. Manually trigger the job to test

### Worker Not Processing Messages

1. Check Pub/Sub topic exists and has messages
2. Verify worker is deployed and active
3. Check worker logs for processing errors

## Related Documentation

- [Worker Documentation](../b24-spa-1106-sync-worker/README.md)
- [HTTP Handler Documentation](../b24-spa-1106-http/README.md)
- [Date Synchronization](../PRACA_DATES_SYNC.md)
