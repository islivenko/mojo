# Instructions & Guides

> **Quick reference for project setup and configuration**

---

## 📚 Available Guides

### 🔧 Setup & Configuration

1. **[Environment Setup (.env)](./env-setup.md)** ⭐ START HERE
   - Complete guide for `.env` configuration
   - Required and optional variables
   - Security best practices
   - Validation and troubleshooting
   - **Time:** 15-20 minutes

2. **[OAuth Setup](./oauth-setup.md)**
   - Bitrix24 OAuth application setup
   - Token management
   - Authentication flow
   - **Time:** 10-15 minutes

### 📊 Architecture & Development

3. **[B24 OCR Architecture](./b24-ocr-architecture.md)**
   - Document OCR system overview
   - Component architecture
   - Data flow diagrams
   - **Time:** 10 minutes (reading)

4. **[Logging Guide](./logging-guide.md)**
   - Structured logging practices
   - Cloud Logging integration
   - Log levels and formatting
   - **Time:** 5-10 minutes

5. **[Mermaid in Cursor](./mermaid-cursor.md)**
   - Creating diagrams with Mermaid
   - Best practices for documentation
   - Examples and templates
   - **Time:** 15 minutes

---

## 🚀 Quick Start

### New to the project?

Follow this order:

```
1. Environment Setup (.env)     ← Start here
   └─ Create and configure .env file
   └─ Validate configuration
   
2. OAuth Setup                  ← If using Bitrix24
   └─ Create OAuth application
   └─ Get credentials
   
3. Deploy Services              ← Deploy to Cloud Functions
   └─ cd google-cloud/SERVICE
   └─ ./deploy.sh
   
4. Test Integration             ← Verify everything works
   └─ Check Cloud Logging
   └─ Test webhooks
```

### Already set up?

**Quick reference:**
- Validate `.env`: `./scripts/validate-env.sh`
- Deploy service: `cd google-cloud/SERVICE && ./deploy.sh`
- Check logs: `gcloud functions logs read FUNCTION_NAME`
- View docs: `docs/bitrix24/` or `docs/instructions/`

---

## 📋 Checklist for New Developers

- [ ] Clone repository
- [ ] Create `.env` file (see [env-setup.md](./env-setup.md))
- [ ] Set file permissions: `chmod 600 .env`
- [ ] Fill in required variables
- [ ] Run validation: `./scripts/validate-env.sh`
- [ ] Authenticate with GCP: `gcloud auth login`
- [ ] Set GCP project: `gcloud config set project PROJECT_ID`
- [ ] Read architecture docs: `docs/bitrix24/architecture.md`
- [ ] Deploy a test service
- [ ] Verify logs in Cloud Console

---

## 🔍 Finding What You Need

### By Topic

| Topic | Guide | Quick Link |
|-------|-------|------------|
| **Environment variables** | env-setup.md | [Link](./env-setup.md) |
| **Bitrix24 authentication** | oauth-setup.md | [Link](./oauth-setup.md) |
| **Document processing** | b24-ocr-architecture.md | [Link](./b24-ocr-architecture.md) |
| **Logging & debugging** | logging-guide.md | [Link](./logging-guide.md) |
| **Creating diagrams** | mermaid-cursor.md | [Link](./mermaid-cursor.md) |

### By Use Case

| I want to... | See |
|--------------|-----|
| Set up my development environment | [env-setup.md](./env-setup.md) |
| Connect to Bitrix24 API | [oauth-setup.md](./oauth-setup.md) |
| Understand the OCR system | [b24-ocr-architecture.md](./b24-ocr-architecture.md) |
| Debug Cloud Functions | [logging-guide.md](./logging-guide.md) |
| Document a new feature | [mermaid-cursor.md](./mermaid-cursor.md) |
| Deploy a service | [env-setup.md](./env-setup.md) + Service README |

---

## 🛠️ Common Tasks

### Validate Environment Configuration
```bash
./scripts/validate-env.sh
```

### Deploy a Service
```bash
cd google-cloud/b24-spa-1038-sync/b24-spa-1038-sync-worker
./deploy.sh
```

### Check Service Logs
```bash
gcloud functions logs read FUNCTION_NAME \
  --region=europe-central2 \
  --limit=50
```

### Test Bitrix24 Connection
```bash
# With OAuth token
curl "https://bergermann.bitrix24.pl/rest/crm.contact.list.json?auth=YOUR_TOKEN"

# With webhook
curl "https://bergermann.bitrix24.pl/rest/USER_ID/WEBHOOK_CODE/crm.contact.list.json"
```

---

## 📞 Getting Help

### Documentation Structure

```
docs/
├── instructions/          ← You are here
│   ├── README.md         ← This file
│   ├── env-setup.md      ← Environment configuration ⭐
│   ├── oauth-setup.md    ← Bitrix24 OAuth
│   ├── logging-guide.md  ← Logging practices
│   └── ...
│
├── bitrix24/             ← Business logic documentation
│   ├── architecture.md   ← System architecture
│   ├── objects/          ← Entity documentation
│   └── ...
│
└── notes.md              ← Project notes
```

### Support Channels

1. **Documentation** - Check relevant guide first
2. **Code Comments** - Look at inline documentation
3. **Git History** - Check commit messages for context
4. **Team** - Contact: info@keyframelab.com

---

## 🔄 Keeping Documentation Updated

When you make changes:

1. **Update relevant guides** if you change configuration
2. **Add examples** for new features
3. **Update diagrams** if architecture changes
4. **Keep README files** in sync with code

**Documentation is code!** Keep it up to date.

---

## 📚 Related Documentation

- [Project README](../../README.md) - Project overview
- [Bitrix24 Architecture](../bitrix24/architecture.md) - System design
- [Service READMEs](../../google-cloud/) - Individual service docs

---

**Last Updated:** 2026-01-04  
**Maintainer:** KeyFrame Lab



