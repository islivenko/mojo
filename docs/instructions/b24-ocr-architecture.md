# Bitrix24 OCR Architecture

## Overview

System for automatic passport data extraction from files attached to Bitrix24 SPA "Załączniki" (entityTypeId: 1054).

## Business Requirements

### Input
- Files uploaded to field **Pliki** in SPA Załączniki (1054)
- File types: **Photos (JPEG, PNG)** or **PDF with photos**
- Documents: Passports from various countries

### Output - Extracted Fields
| Field (PL) | Field (EN) | Example |
|------------|------------|---------|
| Numer paszportu | Passport Number | `AB1234567` |
| Imię | First Name | `VAKHTANG` |
| Nazwisko | Last Name | `DALAKISHVILI` |
| Narodowość | Nationality | `GEORGIA` |
| Data urodzenia | Date of Birth | `1985-03-15` |
| Data wydania | Issue Date | `2020-01-10` |
| Data ważności | Expiry Date | `2030-01-10` |

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              BITRIX24                                        │
│  ┌─────────────────┐                                                        │
│  │  SPA Załączniki │  Webhook: ONCRMDYNAMICITEMADD / UPDATE                │
│  │  (Type 1054)    │────────────────────────────────────────────┐          │
│  │                 │                                             │          │
│  │  📎 Pliki       │                                             ▼          │
│  └─────────────────┘                                    ┌────────────────┐  │
│                                                         │  Automation    │  │
│                                                         │  Rule/Trigger  │  │
│                                                         └───────┬────────┘  │
└─────────────────────────────────────────────────────────────────┼───────────┘
                                                                  │
                                                                  ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           GOOGLE CLOUD                                       │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                    Cloud Functions (2nd gen)                          │ │
│  │                                                                       │ │
│  │   ┌─────────────────────┐         ┌─────────────────────────────┐    │ │
│  │   │ b24-ocr-http   │         │   b24-ocr-worker       │    │ │
│  │   │ (Webhook Handler)   │         │   (Pub/Sub Triggered)       │    │ │
│  │   │                     │         │                             │    │ │
│  │   │ • Receive webhook   │         │ 1. Download file from B24   │    │ │
│  │   │ • Validate request  │         │ 2. OCR via Document AI      │    │ │
│  │   │ • Publish to Pub/Sub│         │ 3. Parse via Gemini AI      │    │ │
│  │   │ • Return 200 fast   │         │ 4. Update Załączniki fields │    │ │
│  │   └──────────┬──────────┘         │ 5. Link to Cudzoziemcy?     │    │ │
│  │              │                    └──────────────┬──────────────┘    │ │
│  └──────────────┼───────────────────────────────────┼───────────────────┘ │
│                 │                                   │                     │
│                 ▼                                   │                     │
│  ┌──────────────────────────┐                       │                     │
│  │ Pub/Sub                  │                       │                     │
│  │ b24-ocr-events      │───────────────────────┘                     │
│  └──────────────────────────┘                                             │
│                                                                           │
│  ┌────────────────────────┐    ┌────────────────────────────────────────┐ │
│  │ Secret Manager         │    │ Document AI                            │ │
│  │ • b24-access-token     │    │ • OCR Processor                        │ │
│  │ • gemini-api-key       │    │ • $1.50/1000 pages                     │ │
│  └────────────────────────┘    └────────────────────────────────────────┘ │
│                                                                           │
│  ┌────────────────────────────────────────────────────────────────────┐   │
│  │ Gemini AI (gemini-2.0-flash)                                       │   │
│  │ • MRZ parsing (Machine Readable Zone)                              │   │
│  │ • Visual Zone parsing                                              │   │
│  │ • Multilingual support (Latin, Cyrillic, Arabic, etc.)            │   │
│  └────────────────────────────────────────────────────────────────────┘   │
│                                                                           │
│  ┌────────────────────────────────────────────────────────────────────┐   │
│  │ Firestore (optional)                                               │   │
│  │ • Idempotency (prevent duplicate processing)                       │   │
│  │ • Processing history                                               │   │
│  └────────────────────────────────────────────────────────────────────┘   │
└───────────────────────────────────────────────────────────────────────────┘
```

---

## Data Flow

```
1. User uploads passport file to SPA Załączniki (1054)
           ↓
2. Bitrix24 sends webhook to b24-ocr-http
           ↓
3. HTTP handler publishes message to Pub/Sub
   { "item_id": "6", "entity_type_id": "1054" }
           ↓
4. Worker function receives message
           ↓
5. Worker downloads file from Bitrix24 using REST API
   crm.item.get → get file URL → download
           ↓
6. Document AI performs OCR
   Returns raw text including MRZ zone
           ↓
7. Gemini AI parses passport data
   Extracts: passport_number, first_name, last_name,
             nationality, birth_date, issue_date, expiry_date
           ↓
8. Worker updates SPA Załączniki fields via REST API
   crm.item.update with extracted data
           ↓
9. (Optional) Link data to related Cudzoziemcy (SPA 1038)
```

---

## Project Structure

```
google-cloud/
└── b24-ocr/
    ├── b24-ocr-http/           # Webhook handler
    │   ├── main.py
    │   ├── requirements.txt
    │   └── deploy.sh
    │
    └── b24-ocr-worker/         # OCR processor
        ├── main.py
        ├── requirements.txt
        ├── deploy.sh
        └── services/
            ├── __init__.py
            ├── bitrix_api.py        # Bitrix24 REST API client
            ├── document_ai.py       # Document AI OCR
            ├── passport_parser.py   # Gemini AI passport parsing
            ├── token_store.py       # Secret Manager integration
            └── idempotency.py       # (optional) Firestore dedup
```

---

## Passport Parsing Strategy

### MRZ (Machine Readable Zone)
Most passports have a 2-line MRZ at the bottom:
```
P<GEODALAKISHVILI<<VAKHTANG<<<<<<<<<<<<<<<<<<<<
AB12345671GEO8503155M3001109<<<<<<<<<<<<<<06
```

**MRZ Structure:**
- Line 1: Document type, country code, surname, given names
- Line 2: Passport number, nationality, birth date, sex, expiry date, check digits

### Visual Zone
For passports without clear MRZ or as validation:
- Parse text fields from the visual zone
- Support multiple languages and scripts

### Gemini AI Prompt

```python
PASSPORT_EXTRACTION_PROMPT = """
Analyze this passport image/document and extract the following information.
The document may be from any country with text in various scripts (Latin, Cyrillic, Arabic, etc.).

IMPORTANT: If the document contains an MRZ (Machine Readable Zone) - the two lines at the bottom
with characters like P<GEODALAKISHVILI<<VAKHTANG - use it as the primary source of truth.

Extract the following fields:
- passport_number: The passport number (alphanumeric)
- first_name: Given name(s) in Latin characters
- last_name: Surname/family name in Latin characters
- nationality: Country of citizenship (3-letter ISO code or full name)
- birth_date: Date of birth (format: YYYY-MM-DD)
- issue_date: Date of passport issuance (format: YYYY-MM-DD)
- expiry_date: Date of passport expiration (format: YYYY-MM-DD)
- sex: M or F
- issuing_country: Country that issued the passport

Return ONLY valid JSON without any markdown formatting.
If a field cannot be determined, use null.

Document text:
{document_text}
"""
```

---

## Bitrix24 Field Mapping

### SPA Załączniki (1054) - Target Fields

| Extracted Field | Bitrix24 Field Code | Field Type |
|-----------------|---------------------|------------|
| passport_number | `ufCrm...` | String |
| first_name | `ufCrm...` | String |
| last_name | `ufCrm...` | String |
| nationality | `ufCrm...` | String |
| birth_date | `ufCrm...` | Date |
| issue_date | `ufCrm...` | Date |
| expiry_date | `ufCrm...` | Date |

> ⚠️ **TODO**: Получить актуальные коды полей из Bitrix24 API:
> ```bash
> curl "https://bergermann.bitrix24.pl/rest/crm.type.fields.get?entityTypeId=1054"
> ```

---

## Implementation Steps

### Phase 1: Setup (1-2 hours)
1. [ ] Create Document AI OCR processor in GCP
2. [ ] Store Gemini API key in Secret Manager
3. [ ] Get Załączniki (1054) field codes from Bitrix24

### Phase 2: HTTP Handler (1 hour)
1. [ ] Create `b24-ocr-http` Cloud Function
2. [ ] Parse webhook from Bitrix24
3. [ ] Publish to Pub/Sub topic `b24-ocr-events`

### Phase 3: Worker (3-4 hours)
1. [ ] Create `b24-ocr-worker` Cloud Function
2. [ ] Implement file download from Bitrix24
3. [ ] Integrate Document AI OCR
4. [ ] Create Gemini passport parsing prompt
5. [ ] Update Załączniki fields

### Phase 4: Bitrix24 Configuration (30 min)
1. [ ] Create automation rule for SPA Załączniki
2. [ ] Configure webhook on file upload event
3. [ ] Test end-to-end flow

### Phase 5: Testing & Refinement (2-3 hours)
1. [ ] Test with various passport types
2. [ ] Handle edge cases (poor quality, rotated images)
3. [ ] Add error handling and notifications

---

## Cost Estimation

| Service | Price | Estimated Usage | Monthly Cost |
|---------|-------|-----------------|--------------|
| Document AI OCR | $1.50/1000 pages | 500 pages | ~$0.75 |
| Gemini AI | ~$0.075/1M tokens | 50k tokens | ~$0.04 |
| Cloud Functions | $0.40/million invocations | 500 | ~$0.01 |
| Pub/Sub | $40/TB | <1MB | ~$0.01 |
| **Total** | | | **~$1/month** |

---

## Security Considerations

1. **Tokens**: All API tokens stored in Secret Manager
2. **Network**: Cloud Functions in same region as Document AI (europe-central2)
3. **Data**: No passport images stored after processing
4. **Access**: Functions use service account with minimal permissions

---

## Future Enhancements

1. **Auto-link to Cudzoziemcy**: Automatically match passport to existing person
2. **Validation**: Cross-check extracted data with MRZ checksums
3. **Multiple pages**: Handle multi-page PDF with multiple passports
4. **ID cards support**: Extend to ID cards, residence permits
5. **Quality check**: Detect blurry or incomplete scans before processing

---

## Related Documents

- [sync-architecture.md](./sync-architecture.md) - SPA 1038 synchronization
- [bitrix24.md](./bitrix24.md) - Bitrix24 API reference
- [google-cloud.md](./google-cloud.md) - GCP infrastructure

