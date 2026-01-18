# Changelog

## 2026-01-18 - SPA 1106 Sync System & Improvements

### 🎉 New Features

#### 1. Uprawnienia do Pracy Date Synchronization
- ✅ Implemented date sync from "Data ważności" (SPA 1046) to Sprawy (SPA 1106)
- ✅ Dates are sorted to match the order of links
- ✅ Multiple dates field support with position-based mapping
- 📄 Documentation: `google-cloud/b24-spa-1106-sync/PRACA_DATES_SYNC.md`

#### 2. Daily Sync Service
- ✅ Created `b24-spa-1106-daily-sync` Cloud Function
- ✅ Scheduled to run daily at 03:00 Warsaw time
- ✅ Publishes sync messages for all active Sprawy to Pub/Sub
- ✅ Worker processes each Sprawy in parallel
- 📊 Test results: 11 active items, 436ms execution time

### 🐛 Bug Fixes

#### 1. Date Sorting Logic
- **Issue**: Dates were sorted independently, not matching link order
- **Fix**: Changed from `sorted(active_ids)` to position-based mapping
- **Impact**: Both `praca_sync.py` and `pobyt_sync.py`

#### 2. Order-Aware Comparison
- **Issue**: Used `set()` comparison which ignored order
- **Fix**: Changed to direct list comparison: `current_links == new_links`
- **Impact**: Now detects when order changes and updates accordingly

### 🔧 Improvements

#### 1. Project Structure Cleanup
- ✅ Moved `output/*.json` → `scripts/output/*.json`
- ✅ Updated all scripts to use new path
- ✅ Removed empty `output/` directory

#### 2. Environment Configuration
- ✅ Restructured `.env` file with clear sections
- ✅ Removed `GCP_PROJECT_ID` duplication (kept only `PROJECT_ID`)
- ✅ Added comprehensive documentation: `docs/instructions/env-configuration.md`
- ✅ Added inline comments and notes section

### 📚 Documentation

#### New Documents
1. `google-cloud/b24-spa-1106-sync/PRACA_DATES_SYNC.md` - Uprawnienia date sync
2. `google-cloud/b24-spa-1106-sync/b24-spa-1106-daily-sync/README.md` - Daily sync
3. `docs/instructions/env-configuration.md` - Environment variables guide

#### Removed Documents
- `google-cloud/b24-spa-1106-sync/BUGFIX_DATES_COMPARISON.md` (consolidated)
- `google-cloud/b24-spa-1106-sync/PODSTAWY_DATES_SYNC.md` (consolidated)

### 🚀 Deployments

#### Cloud Functions
1. **b24-spa-1106-sync-worker** (revision 00012-xoq)
   - Updated date sorting logic
   - Order-aware comparison
   - Unified logic across all sync services

2. **b24-spa-1106-daily-sync** (revision 00002-coc)
   - New service deployed
   - Scheduler configured (03:00 daily)
   - Successfully tested

### 📊 System Status

#### Active Services
- ✅ `b24-token-refresh` - Every 45 minutes
- ✅ `b24-spa-1106-http` - Webhook handler
- ✅ `b24-spa-1106-sync-worker` - Event processor
- ✅ `b24-spa-1106-daily-sync` - Daily full sync (03:00)

#### Synchronization Coverage
- ✅ Podstawy pobytu (links + dates) - sorted by ID
- ✅ Uprawnienia do pracy (links + dates) - sorted by ID
- ✅ Procesy legalizacyjne (links only)
- ✅ Contact passport fields (number + validity date)

### 🔍 Testing

#### Test Results
- ✅ Sprawy ID=18 (Contact 194)
- ✅ Links sorted correctly: `['26', '28', '34']`
- ✅ Dates match link order
- ✅ Daily sync: 11 active items processed
- ✅ Worker: All messages processed successfully

### 📝 Technical Details

#### Modified Files
- `google-cloud/b24-spa-1106-sync/b24-spa-1106-sync-worker/services/praca_sync.py`
- `google-cloud/b24-spa-1106-sync/b24-spa-1106-sync-worker/services/pobyt_sync.py`
- `google-cloud/b24-spa-1106-sync/b24-spa-1106-sync-worker/main.py`
- `google-cloud/b24-spa-1106-sync/b24-spa-1106-sync-worker/deploy.sh`
- `scripts/get_entity_structures.py`
- `scripts/get_spa_1042_structure.py`
- `.env` (restructured)

#### New Files
- `google-cloud/b24-spa-1106-sync/b24-spa-1106-daily-sync/main.py`
- `google-cloud/b24-spa-1106-sync/b24-spa-1106-daily-sync/requirements.txt`
- `google-cloud/b24-spa-1106-sync/b24-spa-1106-daily-sync/deploy.sh`
- `google-cloud/b24-spa-1106-sync/b24-spa-1106-daily-sync/README.md`
- `google-cloud/b24-spa-1106-sync/PRACA_DATES_SYNC.md`
- `docs/instructions/env-configuration.md`

### 🎯 Next Steps

Potential future improvements:
- [ ] Add monitoring and alerting for failed syncs
- [ ] Implement retry logic for failed Pub/Sub messages
- [ ] Add metrics dashboard in Cloud Console
- [ ] Consider adding sync for other date fields if needed

---

## Previous Changes

See git history for earlier changes.
