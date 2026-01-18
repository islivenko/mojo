# Bitrix24 OCR Logging Architecture

## Overview

The Bitrix24 OCR system uses **centralized structured logging** to provide comprehensive visibility into all processing stages. All logs are output in JSON format for Cloud Logging, making them easy to filter, analyze, and monitor.

## Structured Logging Implementation

### Custom Log Handler

Located in `b24-ocr-worker/main.py`:

```python
class StructuredLogHandler(logging.Handler):
    """Custom handler that outputs structured JSON logs for Cloud Run"""
    def emit(self, record):
        log_entry = {
            "severity": record.levelname,
            "message": record.getMessage(),
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "logger": record.name,
        }
        print(json.dumps(log_entry, ensure_ascii=False, default=str), flush=True)
```

### Configuration

All Python loggers are automatically configured to use the structured handler:

```python
root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)
root_logger.handlers = []  # Clear default handlers
root_logger.addHandler(StructuredLogHandler())
```

## Service-Level Logging

### 1. Document AI Service (`document_ai.py`)

**Purpose:** OCR text extraction from passport images/PDFs

**Key Logs:**
- 🔤 OCR starting with file size and MIME type
- ⏱️ Processing time and characters per second
- 📄 Pages processed
- 📝 Text preview (first 200 chars)
- ✅ Completion status

**Example:**
```
🔤 OCR starting: 140362 bytes (137.1KB), mime: application/pdf
   Sending request to Document AI...
✅ OCR completed successfully:
   Pages processed: 1
   Text extracted: 1266 chars
   Processing time: 2.06s
   Chars per second: 616
```

### 2. Passport Parser Service (`document_parser.py`)

**Purpose:** Extract structured passport data using Gemini AI

**Key Logs:**
- 🤖 Parsing start with text length
- 🔧 Model configuration (temperature, top-p)
- ⏱️ API response time
- 📊 Extracted fields count
- 🔍 Individual field values (debug level)

**Example:**
```
🤖 Starting Gemini AI passport parsing: 1266 chars
   Sending request to Gemini AI...
✅ Gemini response received in 1.21s
✅ Successfully extracted 9 fields (removed 0 null values)
   Fields: passport_number, first_name, last_name, nationality, birth_date, issue_date, expiry_date, sex, issuing_country
```

### 3. Bitrix API Service (`bitrix_api.py`)

**Purpose:** Interact with Bitrix24 REST API

**Key Logs:**
- 📥 Item fetching with entity type and ID
- 📥 File download with size and MIME type
- 📤 Item updates with field list
- ✅ Success/failure status
- ❌ HTTP error details

**Example:**
```
📥 Fetching SPA item: entityTypeId=1054, id=6
✅ Item fetched successfully: 47 fields
📥 Downloading file from Bitrix24
   File ID: 9996
   File name: passport.pdf
   File size: 140362
✅ File downloaded successfully:
   Size: 140362 bytes (137.1KB)
   MIME type: application/pdf
```

### 4. Timeline Notifier Service (`timeline_notifier.py`)

**Purpose:** Post progress updates to Bitrix24 timeline

**Key Logs:**
- 📝 Initialization with configuration
- 🚀 Start with countdown settings
- ⏱️ Countdown lifecycle
- 🧹 Cleanup operations
- ✅ Success/failure message posting
- 🗑️ Comment deletion

**Example:**
```
📝 TimelineNotifier initialized:
   Entity: SPA 1054, Item: 6
   Countdown: 30s (step: 5s)
🚀 Starting timeline notifier for SPA 1054/6
   Posting start message...
   Posting ETA message...
⏱️ Countdown thread started (30s total)
⏱️ Countdown finished
🧹 Stopping countdown and cleaning up timeline for SPA 1054/6
✅ Timeline cleanup done. Deleted 3 comments.
✅ Success message posted. comment_id=7746
```

### 5. Main Worker (`main.py`)

**Purpose:** Orchestrate the entire OCR pipeline

**Key Logs:**
- 📨 Message received and parsed
- 🔍 Processing item ID
- ⬇️ Download status
- 🔤 OCR initiation
- 🤖 Parsing initiation
- ✅ Results posting
- ⏱️ Total execution time

**Example:**
```
==================================================
📨 New message received
📋 Message parsed
🔍 Processing item 6
📎 Found 1 file(s)
⬇️ Downloading file...
✅ File downloaded: 140362 bytes, type: application/pdf
🔤 Starting OCR...
✅ OCR completed in 2.45s, 1266 chars
🤖 Parsing with Gemini AI...
✅ Parsing completed in 1.46s
📊 Extracted fields: ['passport_number', 'first_name', ...]
✅ Results posted to timeline
✅ Processing completed in 6.39s
==================================================
```

## Log Levels

### INFO (Default)
- All major processing steps
- Success/failure status
- Timing information
- Extracted data summary

### DEBUG (Optional)
- Detailed configuration
- API request/response details
- Individual field values
- Internal state changes

### WARNING
- Non-critical issues
- Fallback behaviors
- Unexpected but handled situations

### ERROR
- Processing failures
- API errors
- Invalid data

## Viewing Logs in Cloud Console

### Filter by Service
```
resource.type="cloud_run_revision"
resource.labels.service_name="b24-ocr-worker"
jsonPayload.logger="b24-ocr-worker.document_ai"
```

### Filter by Severity
```
resource.labels.service_name="b24-ocr-worker"
severity="ERROR"
```

### Filter by Time Range
```
resource.labels.service_name="b24-ocr-worker"
timestamp>="2026-01-03T00:00:00Z"
```

### Filter by Message Content
```
resource.labels.service_name="b24-ocr-worker"
jsonPayload.message=~"OCR completed"
```

## Log Analysis Commands

### View all logs for a specific item
```bash
gcloud logging read \
  'resource.labels.service_name="b24-ocr-worker" AND jsonPayload.message=~"item 6"' \
  --project=bergermann \
  --limit=100 \
  --format="value(timestamp,jsonPayload.message)"
```

### Group logs by logger
```bash
gcloud logging read \
  'resource.labels.service_name="b24-ocr-worker"' \
  --project=bergermann \
  --limit=100 \
  --format=json | \
  python3 -c "
import sys, json
logs = json.load(sys.stdin)
by_logger = {}
for log in logs:
    jp = log.get('jsonPayload', {})
    if 'logger' in jp:
        logger = jp['logger'].split('.')[-1]
        by_logger.setdefault(logger, []).append(jp['message'])
for logger, messages in by_logger.items():
    print(f'{logger}: {len(messages)} logs')
"
```

## Best Practices

1. **Use Emoji Indicators**: Makes logs easier to scan visually
   - 🔤 OCR operations
   - 🤖 AI/ML operations
   - 📥 Data fetching
   - 📤 Data updates
   - ✅ Success
   - ❌ Errors
   - ⚠️ Warnings

2. **Include Context**: Always log relevant IDs, counts, sizes
   ```python
   logger.info(f"📥 Fetching SPA item: entityTypeId={entity_type_id}, id={item_id}")
   ```

3. **Log Timing**: Include execution time for performance monitoring
   ```python
   logger.info(f"✅ OCR completed in {ocr_time:.2f}s")
   ```

4. **Structured Data**: Use consistent field names
   ```python
   logger.info(f"   Pages processed: {page_count}")
   logger.info(f"   Text extracted: {text_length} chars")
   ```

5. **Error Details**: Include error types and messages
   ```python
   logger.error(f"❌ OCR failed: {type(e).__name__}: {e}")
   ```

## Monitoring and Alerts

### Key Metrics to Monitor

1. **Processing Time**: `jsonPayload.message=~"Processing completed"`
2. **Error Rate**: `severity="ERROR"`
3. **OCR Success Rate**: `jsonPayload.message=~"OCR completed"`
4. **Gemini API Time**: `jsonPayload.message=~"Gemini response received"`

### Example Alert Policy

Create alerts for:
- Processing time > 30 seconds
- Error rate > 5% in 5 minutes
- OCR failures
- Gemini API timeouts

## Troubleshooting

### No logs appearing?
- Check Cloud Run service is deployed
- Verify logging level is INFO or lower
- Ensure StructuredLogHandler is configured

### Logs not structured?
- Verify all loggers use the root logger configuration
- Check print() statements use flush=True

### Missing service logs?
- Ensure service imports logging module
- Verify logger.info() calls are present
- Check log level filtering

## Related Documentation

- [Bitrix24 OCR Architecture](./b24-ocr-architecture.md)
- [Cloud Logging Documentation](https://cloud.google.com/logging/docs)
- [Python Logging Best Practices](https://docs.python.org/3/howto/logging.html)

