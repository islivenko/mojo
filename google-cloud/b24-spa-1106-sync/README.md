# B24 SPA 1106 Sync Service

> **Сервис синхронизации Sprawy cudzoziemców (SPA 1106)**
>
> Автоматическая синхронизация связей между Sprawy cudzoziemców и связанными объектами

---

## 🎯 Назначение

Сервис обеспечивает автоматическую синхронизацию данных между главной сущностью **Sprawy cudzoziemców (SPA 1106)** и связанными объектами:

- **Podstawy pobytu (SPA 1042)** - Основания пребывания
- **Uprawnienia do pracy (SPA 1046)** - Разрешения на работу
- **Procesy legalizacyjne (SPA 1110)** - Процессы легализации
- **Klient/Projekt (SPA 1098)** - Клиент/Проект
- **Contact** - Персональные данные кандидата

---

## 🏗️ Архитектура

```
┌─────────────────────────────────────────────────────────────────────────┐
│                              BITRIX24                                    │
│                                                                          │
│  ┌──────────────┐  ┌──────────┐  ┌────────┐  ┌────────┐  ┌─────────┐  │
│  │   Contact    │  │Podstawy  │  │ Praca  │  │Procesy │  │ Klient  │  │
│  │              │  │  (1042)  │  │ (1046) │  │ (1110) │  │ (1098)  │  │
│  └──────┬───────┘  └────┬─────┘  └───┬────┘  └───┬────┘  └────┬────┘  │
│         │               │             │            │            │       │
│         │               └─────────────┼────────────┼────────────┘       │
│         │                             │            │                    │
│         │                             ▼            ▼                    │
│         │                    ┌─────────────────────────┐               │
│         └───────────────────►│  Sprawy cudzoziemców   │               │
│                               │       (SPA 1106)        │               │
│                               └──────────┬──────────────┘               │
│                                          │                              │
│                                          │ Webhook                      │
└──────────────────────────────────────────┼──────────────────────────────┘
                                           │
                                           ▼
                              ┌─────────────────────────┐
                              │  b24-spa-1106-http      │
                              │  (HTTP Handler)         │
                              └────────────┬────────────┘
                                           │
                                           ▼
                              ┌─────────────────────────┐
                              │  Pub/Sub Topic          │
                              │  b24-spa-1106-sync-     │
                              │  events                 │
                              └────────────┬────────────┘
                                           │
                                           ▼
                              ┌─────────────────────────┐
                              │  b24-spa-1106-sync-     │
                              │  worker                 │
                              │  (Async Processing)     │
                              └─────────────────────────┘
```

---

## 📦 Компоненты

### 1. b24-spa-1106-http

**Тип:** Cloud Function (HTTP)
**Назначение:** Прием webhook от Bitrix24 и публикация в Pub/Sub

**Обрабатываемые события:**
- `ONCRMDYNAMICITEMADD[1106|1042|1046|1110|1098]` - Создание элемента
- `ONCRMDYNAMICITEMUPDATE[1106|1042|1046|1110|1098]` - Обновление элемента
- `ONCRMDYNAMICITEMDELETE[1106|1042|1046|1110|1098]` - Удаление элемента
- `ONCRMCONTACTADD` - Создание контакта
- `ONCRMCONTACTUPDATE` - Обновление контакта
- `ONCRMCONTACTDELETE` - Удаление контакта

**Endpoint:** `https://[REGION]-[PROJECT_ID].cloudfunctions.net/b24-spa-1106-http`

### 2. b24-spa-1106-sync-worker

**Тип:** Cloud Function (Pub/Sub triggered)
**Назначение:** Асинхронная обработка событий и синхронизация данных

**Сервисы синхронизации:**
- `podstawy_sync.py` - Синхронизация Podstawy pobytu (1042)
- `praca_sync.py` - Синхронизация Uprawnienia do pracy (1046)
- `procesy_sync.py` - Синхронизация Procesy legalizacyjne (1110)
- `contact_fields_sync.py` - Синхронизация полей Contact

### 3. b24-spa-1106-daily-sync

**Тип:** Cloud Function (Cloud Scheduler triggered)
**Назначение:** Ежедневная полная синхронизация всех данных

**Расписание:** 03:00 UTC

---

## 🔄 Логика синхронизации

### Podstawy pobytu (SPA 1042)

**Направление:** Podstawy pobytu → Sprawy cudzoziemców

**Логика:**
1. При создании/обновлении Podstawy проверяется статус (stageId)
2. Если статус **активный** (не SUCCESS/FAIL/COMPLETED):
   - ID добавляется в поле `ufCrm38_1768737959` всех связанных Sprawy
3. Если статус **финальный** (SUCCESS/FAIL/COMPLETED):
   - ID удаляется из поля всех связанных Sprawy
4. При удалении Podstawy - удаляется из всех связанных Sprawy

**Поле связи:** `ufCrm38_1768737959` (Aktualne Podstawy pobytu)

### Uprawnienia do pracy (SPA 1046)

**Направление:** Praca → Sprawy cudzoziemców

**Логика:** Аналогична Podstawy pobytu (только активные элементы)

**Поле связи:** `ufCrm38_1768738112` (Aktualne uprawnienia do pracy)

### Procesy legalizacyjne (SPA 1110)

**Направление:** Procesy → Sprawy cudzoziemców

**Логика:** Аналогична Podstawy pobytu (только активные элементы)

**Поле связи:** `ufCrm38_1768738413` (Aktualne procesy legalizacyjne)

### Contact Fields (Персональные данные)

**Направление:** Contact → Sprawy cudzoziemców

**Синхронизируемые поля:**
- `Contact.UF_CRM_*` → `Sprawy.ufCrm38_1764509760429` (nr paszportu)
- `Contact.BIRTHDATE` → `Sprawy.ufCrm38_*` (Data urodzenia)
- `Contact.[LAST_NAME + NAME]` → `Sprawy.TITLE` (Заголовок дела)

---

## 🚀 Развертывание

### Предварительные требования

1. Google Cloud Project с включенными API:
   - Cloud Functions
   - Pub/Sub
   - Secret Manager

2. Bitrix24 OAuth токен в Secret Manager:
   - Secret ID: `b24-access-token`

3. Переменные окружения в `.env`:
   ```bash
   PROJECT_ID=mojo-478621
   GCP_REGION=europe-central2
   GCP_RUNTIME=python312
   ```

### Развертывание всех компонентов

```bash
cd /Users/Dev/mojo_agency/google-cloud/b24-spa-1106-sync

# HTTP Handler
cd b24-spa-1106-http
chmod +x deploy.sh
./deploy.sh

# Worker
cd ../b24-spa-1106-sync-worker
chmod +x deploy.sh
./deploy.sh

# Daily Sync
cd ../b24-spa-1106-daily-sync
chmod +x deploy.sh
./deploy.sh
```

---

## 🔧 Конфигурация

### Переменные окружения (Worker)

```bash
PROJECT_ID=mojo-478621
B24_DOMAIN=mojo.bitrix24.pl
ACCESS_TOKEN_SECRET=b24-access-token

# SPA Entity Type IDs
SPA_SPRAWY_1106_ID=1106
SPA_PODSTAWY_POBYTU_1042_ID=1042
SPA_PRACA_ID=1046
SPA_PROCESY_LEGALIZACYJNE_ID=1110
SPA_KLIENT_PROJEKT_ID=1098

# Link Fields in Sprawy (1106)
FIELD_SPRAWY_PODSTAWY=ufCrm38_1768737959
FIELD_SPRAWY_PRACA=ufCrm38_1768738112
FIELD_SPRAWY_PROCESY=ufCrm38_1768738413
FIELD_SPRAWY_KLIENT=ufCrm38_1764509491
```

### Коды полей связей

| Поле | Код | Связь с |
|------|-----|---------|
| Aktualne Podstawy pobytu | `ufCrm38_1768737959` | SPA 1042 |
| Aktualne uprawnienia do pracy | `ufCrm38_1768738112` | SPA 1046 |
| Aktualne procesy legalizacyjne | `ufCrm38_1768738413` | SPA 1110 |
| Klient użytkownik (Projekt) | `ufCrm38_1764509491` | SPA 1098 |

---

## 📊 Мониторинг

### Cloud Logging

```bash
# Логи HTTP handler
gcloud logging read "resource.type=cloud_function AND resource.labels.function_name=b24-spa-1106-http" --limit 50

# Логи Worker
gcloud logging read "resource.type=cloud_function AND resource.labels.function_name=b24-spa-1106-sync-worker" --limit 50
```

---

## 🐛 Troubleshooting

### Проблема: Podstawy pobytu не синхронизируются

**Проверить:**
1. Webhook настроен для событий SPA 1042
2. Переменная `FIELD_SPRAWY_PODSTAWY` содержит правильный код поля
3. Contact ID присутствует в Podstawy
4. Логи Worker на наличие ошибок

---

## 📚 Документация

- [Sprawy cudzoziemców (SPA 1106)](../../docs/bitrix24/objects/sprawy-cudzoziemcow-1106.md)
- [Legalizacja Module](../../docs/bitrix24/legalizacja-module.md)
- [Architecture Overview](../../docs/bitrix24/architecture.md)

---

**Автор:** KeyFrame Lab
**Версия:** 1.0
**Дата создания:** 2026-01-18
**Проект:** mojo_agency
