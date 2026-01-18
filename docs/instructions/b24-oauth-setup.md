# Bitrix24 OAuth Setup & Token Refresh Guide

> **Глобальная инструкция по настройке OAuth интеграции с Bitrix24 и автоматического обновления токенов через Google Cloud**
>
> Версия: 2.0 | Последнее обновление: 2026-01-04

---

## 🎯 Назначение

Эта инструкция описывает полный процесс настройки OAuth авторизации для интеграции с Bitrix24 и создания автоматического сервиса обновления токенов в Google Cloud Platform.

**Применимо для:**
- Всех текущих и будущих проектов интеграции с Bitrix24
- Любых Cloud Functions, требующих доступа к Bitrix24 REST API
- Проектов, где необходим долгосрочный доступ без повторной авторизации

---

## 📋 Содержание

1. [Часть 1: Настройка OAuth в Bitrix24](#часть-1-настройка-oauth-в-bitrix24)
2. [Часть 2: Получение токенов](#часть-2-получение-токенов)
3. [Часть 3: Настройка Google Cloud](#часть-3-настройка-google-cloud)
4. [Часть 4: Деплой Token Refresh сервиса](#часть-4-деплой-token-refresh-сервиса)
5. [Часть 5: Настройка Cloud Scheduler](#часть-5-настройка-cloud-scheduler)
6. [Часть 6: Тестирование](#часть-6-тестирование)
7. [Использование в других сервисах](#использование-в-других-сервисах)

---

## Часть 1: Настройка OAuth в Bitrix24

### 1.1. Создание серверного приложения

1. Перейдите на портал Bitrix24:
   ```
   https://[YOUR_DOMAIN].bitrix24.pl/marketplace/local/
   ```

2. Нажмите **"Создать приложение"**

3. Выберите тип: **"Серверное"** (Server-side application)

4. Заполните настройки:

   | Поле | Значение |
   |------|----------|
   | **Название** | `KeyFrame OAuth Connector` (или любое другое) |
   | **Redirect URI** | `https://localhost/oauth` |
   | **Права доступа** | Выберите необходимые (например: `crm`, `disk`, `user`) |

5. Сохраните приложение

### 1.2. Получение Client ID и Client Secret

После создания приложения скопируйте:

- **Client ID** (например: `local.69064be83f1cf1.26554014`)
- **Client Secret** (например: `gr6wR3EVK2K4ePRR4LwJBiohizf8tYfdiqGml96Sbd1WxSeKBA`)

⚠️ **Важно:** Сохраните эти значения в безопасном месте. Они понадобятся для следующих шагов.

---

## Часть 2: Получение токенов

### 2.1. Получение Authorization Code

1. Откройте в браузере URL (замените `CLIENT_ID` и `DOMAIN`):

```
https://[YOUR_DOMAIN].bitrix24.pl/oauth/authorize/?client_id=[CLIENT_ID]&response_type=code&redirect_uri=https://localhost/oauth
```

**Пример:**
```
https://b24-n1mv3w.bitrix24.pl/oauth/authorize/?client_id=local.69064be83f1cf1.26554014&response_type=code&redirect_uri=https://localhost/oauth
```

2. Авторизуйтесь в Bitrix24 (если не авторизованы)

3. Нажмите **"Разрешить"** для предоставления доступа

4. После редиректа на `https://localhost/oauth?code=...` скопируйте значение параметра `code` из адресной строки

**Пример URL после редиректа:**
```
https://localhost/oauth?code=abc123def456&domain=b24-n1mv3w.bitrix24.pl&...
```

Скопируйте: `abc123def456`

### 2.2. Обмен кода на токены

Выполните в терминале (замените значения):

```bash
curl -X POST https://oauth.bitrix.info/oauth/token/ \
  -d "grant_type=authorization_code" \
  -d "client_id=[CLIENT_ID]" \
  -d "client_secret=[CLIENT_SECRET]" \
  -d "code=[AUTHORIZATION_CODE]" \
  -d "redirect_uri=https://localhost/oauth"
```

**Пример:**
```bash
curl -X POST https://oauth.bitrix.info/oauth/token/ \
  -d "grant_type=authorization_code" \
  -d "client_id=local.69064be83f1cf1.26554014" \
  -d "client_secret=gr6wR3EVK2K4ePRR4LwJBiohizf8tYfdiqGml96Sbd1WxSeKBA" \
  -d "code=abc123def456" \
  -d "redirect_uri=https://localhost/oauth"
```

### 2.3. Ответ с токенами

В ответ вы получите JSON:

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "b3c65f0fbb3e8b5d1f12b5a8c9d4e6f7...",
  "expires_in": 3600,
  "scope": "crm,disk,user",
  "domain": "b24-n1mv3w.bitrix24.pl",
  "member_id": "abc123..."
}
```

**Сохраните:**
- `access_token` - используется для API запросов (действует 1 час)
- `refresh_token` - используется для получения нового access_token (действует постоянно)

---

## Часть 3: Настройка Google Cloud

### 3.1. Создание Secret Manager секретов

Сохраните полученные данные в Secret Manager:

```bash
# Установите PROJECT_ID
export PROJECT_ID="your-project-id"

# 1. Client ID
echo -n "local.69064be83f1cf1.26554014" | \
  gcloud secrets create b24-client-id \
    --project=$PROJECT_ID \
    --replication-policy="automatic" \
    --data-file=-

# 2. Client Secret
echo -n "gr6wR3EVK2K4ePRR4LwJBiohizf8tYfdiqGml96Sbd1WxSeKBA" | \
  gcloud secrets create b24-client-secret \
    --project=$PROJECT_ID \
    --replication-policy="automatic" \
    --data-file=-

# 3. Access Token (начальный)
echo -n "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." | \
  gcloud secrets create b24-access-token \
    --project=$PROJECT_ID \
    --replication-policy="automatic" \
    --data-file=-

# 4. Refresh Token
echo -n "b3c65f0fbb3e8b5d1f12b5a8c9d4e6f7..." | \
  gcloud secrets create b24-refresh-token \
    --project=$PROJECT_ID \
    --replication-policy="automatic" \
    --data-file=-
```

### 3.2. Проверка созданных секретов

```bash
gcloud secrets list --project=$PROJECT_ID
```

Должны быть созданы:
- `b24-client-id`
- `b24-client-secret`
- `b24-access-token`
- `b24-refresh-token`

### 3.3. Создание Pub/Sub топика

```bash
gcloud pubsub topics create b24-token-refresh-trigger \
  --project=$PROJECT_ID
```

---

## Часть 4: Деплой Token Refresh сервиса

### 4.1. Структура проекта

Создайте следующую структуру:

```
google-cloud/
└── b24-token-refresh/
    ├── main.py              # Основной код функции
    ├── requirements.txt     # Зависимости Python
    ├── deploy.sh           # Скрипт деплоя
    └── .gcloudignore       # Исключения для деплоя
```

### 4.2. Файл main.py

Создайте файл `main.py`:

```python
"""
Bitrix24 OAuth Token Refresher
Refreshes Bitrix24 OAuth tokens on a schedule via Cloud Scheduler
Stores tokens in Secret Manager with automatic cleanup of old versions
"""
import os
import time
import requests
import functions_framework
from google.cloud import secretmanager
from google.api_core import exceptions as api_exceptions

# Google Cloud Logging integration
import google.cloud.logging
try:
    client = google.cloud.logging.Client()
    client.setup_logging()
except Exception as e:
    print(f"Warning: Could not setup Cloud Logging: {e}")

import logging
logger = logging.getLogger('b24-token-refresh')
logger.setLevel(logging.DEBUG)

# Configuration
PROJECT_ID = os.getenv("PROJECT_ID")
B24_CLIENT_ID = os.getenv("B24_CLIENT_ID")
B24_CLIENT_SECRET = os.getenv("B24_CLIENT_SECRET")
ACCESS_TOKEN_SECRET = os.getenv("ACCESS_TOKEN_SECRET", "b24-access-token")
REFRESH_TOKEN_SECRET = os.getenv("REFRESH_TOKEN_SECRET", "b24-refresh-token")

logger.info("=" * 60)
logger.info("=== B24 Token Refresh initialized ===")
logger.info(f"Config: PROJECT_ID={PROJECT_ID}")


class SecretManagerTokenStore:
    """Bitrix24 token manager using Secret Manager with auto-cleanup"""

    def __init__(self, project_id: str):
        self.project_id = project_id
        self._client = None

    @property
    def client(self) -> secretmanager.SecretManagerServiceClient:
        if self._client is None:
            self._client = secretmanager.SecretManagerServiceClient()
        return self._client

    def _get_secret_path(self, secret_name: str, version: str = "latest") -> str:
        return f"projects/{self.project_id}/secrets/{secret_name}/versions/{version}"

    def _get_secret_parent(self, secret_name: str) -> str:
        return f"projects/{self.project_id}/secrets/{secret_name}"

    def get_secret(self, secret_name: str) -> str:
        """Gets the latest version of a secret"""
        logger.debug(f"Getting secret: {secret_name}")
        name = self._get_secret_path(secret_name, "latest")
        response = self.client.access_secret_version(request={"name": name})
        return response.payload.data.decode("UTF-8")

    def save_secret(self, secret_name: str, value: str) -> str:
        """Saves a new version of a secret and deletes old versions"""
        logger.info(f"Saving new version of secret: {secret_name}")
        parent = self._get_secret_parent(secret_name)

        response = self.client.add_secret_version(
            request={
                "parent": parent,
                "payload": {"data": value.encode("UTF-8")}
            }
        )

        # Cleanup old versions
        self._cleanup_old_versions(secret_name, keep_latest=1)
        return response.name

    def _cleanup_old_versions(self, secret_name: str, keep_latest: int = 1) -> int:
        """Destroys old secret versions, keeping only the latest N"""
        logger.info(f"Cleaning up old versions of '{secret_name}'")
        parent = self._get_secret_parent(secret_name)

        versions = list(self.client.list_secret_versions(request={"parent": parent}))
        enabled_versions = [
            v for v in versions
            if v.state == secretmanager.SecretVersion.State.ENABLED
        ]
        enabled_versions.sort(key=lambda v: v.create_time, reverse=True)

        destroyed_count = 0
        for version in enabled_versions[keep_latest:]:
            self.client.destroy_secret_version(request={"name": version.name})
            destroyed_count += 1

        logger.info(f"Destroyed {destroyed_count} old versions")
        return destroyed_count

    def refresh_tokens(self, client_id: str, client_secret: str) -> dict:
        """Refreshes OAuth tokens via Bitrix24 OAuth server"""
        logger.info("Starting token refresh process...")

        # Get current refresh token
        refresh_token = self.get_secret(REFRESH_TOKEN_SECRET)
        if not refresh_token:
            raise ValueError("No refresh_token found in Secret Manager")

        # Request new tokens from Bitrix24
        logger.info("Requesting new tokens from Bitrix24...")
        payload = {
            "grant_type": "refresh_token",
            "client_id": client_id,
            "client_secret": client_secret,
            "refresh_token": refresh_token,
        }

        response = requests.post(
            "https://oauth.bitrix.info/oauth/token/",
            data=payload,
            timeout=30
        )
        response.raise_for_status()
        new_tokens = response.json()

        if "access_token" not in new_tokens:
            raise ValueError(f"Token refresh failed: {new_tokens}")

        # Preserve refresh_token if not returned
        if "refresh_token" not in new_tokens:
            new_tokens["refresh_token"] = refresh_token

        # Save new tokens
        logger.info("Saving new tokens to Secret Manager...")
        self.save_secret(ACCESS_TOKEN_SECRET, new_tokens["access_token"])
        self.save_secret(REFRESH_TOKEN_SECRET, new_tokens["refresh_token"])

        logger.info("✅ Token refresh completed successfully!")
        return new_tokens


@functions_framework.cloud_event
def main(cloud_event):
    """Pub/Sub triggered token refresh handler"""
    logger.info("=== TOKEN REFRESH REQUEST RECEIVED ===")

    # Validate configuration
    if not all([PROJECT_ID, B24_CLIENT_ID, B24_CLIENT_SECRET]):
        missing = []
        if not PROJECT_ID: missing.append("PROJECT_ID")
        if not B24_CLIENT_ID: missing.append("B24_CLIENT_ID")
        if not B24_CLIENT_SECRET: missing.append("B24_CLIENT_SECRET")
        raise ValueError(f"Missing required env vars: {', '.join(missing)}")

    try:
        token_store = SecretManagerTokenStore(project_id=PROJECT_ID)
        token_store.refresh_tokens(B24_CLIENT_ID, B24_CLIENT_SECRET)
        logger.info("=" * 60)
    except Exception as e:
        logger.error(f"❌ Token refresh failed: {e}", exc_info=True)
        raise
```

### 4.3. Файл requirements.txt

```txt
functions-framework==3.*
google-cloud-secret-manager>=2.16.0
google-cloud-logging>=3.5.0
requests>=2.28.0
```

### 4.4. Файл deploy.sh

```bash
#!/bin/bash
# Deploy script for B24 Token Refresh

set -e

# Load environment variables from .env
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="$SCRIPT_DIR/../../.env"

if [ -f "$ENV_FILE" ]; then
    echo "📦 Loading config from $ENV_FILE"
    source "$ENV_FILE"
else
    echo "❌ Error: .env file not found at $ENV_FILE"
    exit 1
fi

# Configuration
FUNCTION_NAME="b24-token-refresh"
TOPIC_NAME="b24-token-refresh-trigger"

echo "🚀 Deploying $FUNCTION_NAME to $PROJECT_ID..."

gcloud config set project $PROJECT_ID

gcloud functions deploy $FUNCTION_NAME \
  --gen2 \
  --runtime=$GCP_RUNTIME \
  --region=$GCP_REGION \
  --source=. \
  --entry-point=main \
  --trigger-topic=$TOPIC_NAME \
  --memory=256MB \
  --timeout=120s \
  --set-env-vars="PROJECT_ID=$PROJECT_ID,ACCESS_TOKEN_SECRET=b24-access-token,REFRESH_TOKEN_SECRET=b24-refresh-token" \
  --set-secrets="B24_CLIENT_ID=b24-client-id:latest,B24_CLIENT_SECRET=b24-client-secret:latest"

echo ""
echo "✅ Deployment completed!"
echo ""
echo "📋 Next step: Set up Cloud Scheduler"
echo "   See Part 5 of oauth-setup.md"
```

### 4.5. Файл .env (в корне проекта)

Создайте файл `.env` в корне проекта (если еще не создан):

```bash
# Google Cloud Configuration
PROJECT_ID="your-project-id"
GCP_REGION="europe-central2"
GCP_RUNTIME="python312"

# Bitrix24 Configuration
B24_DOMAIN="b24-n1mv3w.bitrix24.pl"
```

### 4.6. Выполнение деплоя

```bash
cd google-cloud/b24-token-refresh
chmod +x deploy.sh
./deploy.sh
```

---

## Часть 5: Настройка Cloud Scheduler

### 5.1. Создание задачи для автоматического обновления

Токены Bitrix24 действуют 1 час. Рекомендуется обновлять их каждые 30 минут:

```bash
gcloud scheduler jobs create pubsub b24-token-refresh-job \
  --project=$PROJECT_ID \
  --schedule='*/30 * * * *' \
  --topic=b24-token-refresh-trigger \
  --message-body='{}' \
  --location=$GCP_REGION \
  --description="Refresh Bitrix24 OAuth tokens every 30 minutes"
```

### 5.2. Альтернативные расписания

```bash
# Каждые 15 минут
--schedule='*/15 * * * *'

# Каждый час
--schedule='0 * * * *'

# Каждые 45 минут
--schedule='*/45 * * * *'
```

### 5.3. Проверка созданной задачи

```bash
gcloud scheduler jobs list --project=$PROJECT_ID --location=$GCP_REGION
```

---

## Часть 6: Тестирование

### 6.1. Ручной запуск обновления токенов

```bash
gcloud scheduler jobs run b24-token-refresh-job \
  --project=$PROJECT_ID \
  --location=$GCP_REGION
```

### 6.2. Просмотр логов

```bash
gcloud functions logs read b24-token-refresh \
  --project=$PROJECT_ID \
  --region=$GCP_REGION \
  --limit=50
```

### 6.3. Проверка токенов в Secret Manager

```bash
# Проверить версии access token
gcloud secrets versions list b24-access-token --project=$PROJECT_ID

# Получить текущий access token (для тестирования)
gcloud secrets versions access latest --secret=b24-access-token --project=$PROJECT_ID
```

### 6.4. Тестовый запрос к Bitrix24 API

```bash
# Получить access token
ACCESS_TOKEN=$(gcloud secrets versions access latest --secret=b24-access-token --project=$PROJECT_ID)

# Тестовый запрос
curl "https://[YOUR_DOMAIN].bitrix24.pl/rest/user.current.json?auth=$ACCESS_TOKEN"
```

Если получили JSON с данными пользователя - всё работает! ✅

---

## Использование в других сервисах

### Вариант 1: Через Secret Manager (рекомендуется)

В вашей Cloud Function используйте Secret Manager для получения токена:

```python
from google.cloud import secretmanager

def get_bitrix_token(project_id: str) -> str:
    """Get current Bitrix24 access token from Secret Manager"""
    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/{project_id}/secrets/b24-access-token/versions/latest"
    response = client.access_secret_version(request={"name": name})
    return response.payload.data.decode("UTF-8")

# Использование
PROJECT_ID = os.getenv("PROJECT_ID")
access_token = get_bitrix_token(PROJECT_ID)

# API запрос
response = requests.post(
    f"https://{B24_DOMAIN}/rest/crm.deal.get.json",
    json={"id": deal_id, "auth": access_token}
)
```

### Вариант 2: Через переменные окружения

В `deploy.sh` вашей функции:

```bash
gcloud functions deploy my-function \
  --set-secrets="B24_ACCESS_TOKEN=b24-access-token:latest"
```

В коде:

```python
access_token = os.getenv("B24_ACCESS_TOKEN")
```

### Вариант 3: Создание сервисного модуля

Создайте файл `services/token_store.py`:

```python
"""Token Store service for Bitrix24 OAuth tokens"""
import os
from google.cloud import secretmanager

class TokenStore:
    def __init__(self, project_id: str):
        self.project_id = project_id
        self._client = None

    @property
    def client(self):
        if self._client is None:
            self._client = secretmanager.SecretManagerServiceClient()
        return self._client

    def get_access_token(self) -> str:
        """Get current Bitrix24 access token"""
        name = f"projects/{self.project_id}/secrets/b24-access-token/versions/latest"
        response = self.client.access_secret_version(request={"name": name})
        return response.payload.data.decode("UTF-8")

# Использование
token_store = TokenStore(project_id=os.getenv("PROJECT_ID"))
access_token = token_store.get_access_token()
```

---

## 🔒 Безопасность

### Лучшие практики

1. **Никогда не коммитьте токены в Git**
   - Добавьте `.env` в `.gitignore`
   - Используйте только Secret Manager для хранения

2. **Ограничьте права доступа**
   ```bash
   # Дайте минимальные необходимые права
   gcloud secrets add-iam-policy-binding b24-access-token \
     --member="serviceAccount:YOUR_SERVICE_ACCOUNT" \
     --role="roles/secretmanager.secretAccessor"
   ```

3. **Мониторинг доступа**
   - Включите аудит логи для Secret Manager
   - Настройте алерты на частые обращения

4. **Ротация Client Secret**
   - Периодически обновляйте Client Secret в Bitrix24
   - Обновляйте секрет в Secret Manager

---

## 🐛 Troubleshooting

### Проблема: "Token refresh failed"

**Причины:**
1. Истёк refresh_token (требуется повторная авторизация)
2. Неверный Client ID или Client Secret
3. Приложение удалено или деактивировано в Bitrix24

**Решение:**
1. Проверьте логи: `gcloud functions logs read b24-token-refresh`
2. Повторите [Часть 2](#часть-2-получение-токенов)
3. Обновите секреты в Secret Manager

### Проблема: "Permission denied" при доступе к Secret Manager

**Решение:**
```bash
# Дайте права сервисному аккаунту
SERVICE_ACCOUNT="${PROJECT_ID}@appspot.gserviceaccount.com"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$SERVICE_ACCOUNT" \
  --role="roles/secretmanager.secretAccessor"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$SERVICE_ACCOUNT" \
  --role="roles/secretmanager.secretVersionManager"
```

### Проблема: Cloud Scheduler не запускает функцию

**Решение:**
```bash
# Проверьте статус задачи
gcloud scheduler jobs describe b24-token-refresh-job \
  --location=$GCP_REGION

# Проверьте права Pub/Sub
gcloud pubsub topics add-iam-policy-binding b24-token-refresh-trigger \
  --member="serviceAccount:service-${PROJECT_NUMBER}@gcp-sa-cloudscheduler.iam.gserviceaccount.com" \
  --role="roles/pubsub.publisher"
```

### Проблема: Старые версии секретов не удаляются

**Причина:** Недостаточно прав для удаления версий

**Решение:**
```bash
SERVICE_ACCOUNT="${PROJECT_ID}@appspot.gserviceaccount.com"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$SERVICE_ACCOUNT" \
  --role="roles/secretmanager.admin"
```

---

## 📊 Мониторинг

### Метрики для отслеживания

1. **Успешность обновления токенов**
   ```
   resource.type="cloud_function"
   resource.labels.function_name="b24-token-refresh"
   jsonPayload.message=~"Token refresh completed"
   ```

2. **Ошибки обновления**
   ```
   resource.type="cloud_function"
   resource.labels.function_name="b24-token-refresh"
   severity="ERROR"
   ```

3. **Время выполнения**
   ```
   resource.type="cloud_function"
   resource.labels.function_name="b24-token-refresh"
   metric.type="cloudfunctions.googleapis.com/function/execution_times"
   ```

### Настройка алертов

Создайте алерт для ошибок обновления токенов:

```bash
# Через Cloud Console: Monitoring → Alerting → Create Policy
# Условие: Cloud Function execution errors > 1 in 5 minutes
# Уведомление: Email/Slack
```

---

## 💰 Стоимость

### Ежемесячные затраты (примерно)

| Сервис | Использование | Стоимость |
|--------|---------------|-----------|
| Cloud Functions | ~1,440 вызовов/месяц (каждые 30 мин) | ~$0.01 |
| Secret Manager | 4 секрета, ~2,880 операций чтения | ~$0.18 |
| Cloud Scheduler | 1 задача | $0.10 |
| Pub/Sub | <1MB данных | ~$0.01 |
| **Итого** | | **~$0.30/месяц** |

---

## 📚 Связанные документы

- [Bitrix24 OCR Architecture](./b24-ocr-architecture.md) - Архитектура OCR системы
- [Logging Guide](./logging-guide.md) - Руководство по логированию
- [Bitrix24 API Documentation](https://dev.1c-bitrix.ru/rest_help/) - Официальная документация API

---

## 📝 Changelog

### 2026-01-04 (v2.0)
- ✅ Переработана в глобальную инструкцию
- ✅ Добавлена полная настройка Google Cloud
- ✅ Добавлен раздел по Token Refresh сервису
- ✅ Добавлены примеры использования в других сервисах
- ✅ Добавлен Troubleshooting и мониторинг

### 2025-XX-XX (v1.0)
- ✅ Первая версия инструкции
- ✅ Базовая настройка OAuth

---

**Автор:** KeyFrame Lab
**Версия:** 2.0
**Дата создания:** 2026-01-04
