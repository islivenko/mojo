# Bitrix24 Token Refresh Service

Автоматический сервис обновления OAuth токенов для Bitrix24.

## Описание

Этот сервис автоматически обновляет access токены Bitrix24 каждые 30 минут, используя refresh токен. Токены хранятся в Google Cloud Secret Manager с автоматической очисткой старых версий.

## Архитектура

```
Cloud Scheduler (каждые 30 мин)
    ↓
Pub/Sub Topic (b24-token-refresh-trigger)
    ↓
Cloud Function (b24-token-refresh)
    ↓
Secret Manager (b24-access-token, b24-refresh-token)
```

## Требования

- Google Cloud Project с включенными API:
  - Cloud Functions
  - Secret Manager
  - Cloud Scheduler
  - Pub/Sub
- Bitrix24 OAuth приложение (Client ID и Client Secret)
- Начальные токены (access_token и refresh_token)

## Установка

### 1. Создание секретов в Secret Manager

```bash
# Установите PROJECT_ID
export PROJECT_ID="your-project-id"

# 1. Client ID
echo -n "local.xxxxx" | \
  gcloud secrets create b24-client-id \
    --project=$PROJECT_ID \
    --replication-policy="automatic" \
    --data-file=-

# 2. Client Secret
echo -n "your-client-secret" | \
  gcloud secrets create b24-client-secret \
    --project=$PROJECT_ID \
    --replication-policy="automatic" \
    --data-file=-

# 3. Access Token (начальный)
echo -n "your-access-token" | \
  gcloud secrets create b24-access-token \
    --project=$PROJECT_ID \
    --replication-policy="automatic" \
    --data-file=-

# 4. Refresh Token
echo -n "your-refresh-token" | \
  gcloud secrets create b24-refresh-token \
    --project=$PROJECT_ID \
    --replication-policy="automatic" \
    --data-file=-
```

### 2. Создание Pub/Sub топика

```bash
gcloud pubsub topics create b24-token-refresh-trigger \
  --project=$PROJECT_ID
```

### 3. Деплой Cloud Function

```bash
cd google-cloud/b24-token-refresh
chmod +x deploy.sh
./deploy.sh
```

### 4. Настройка Cloud Scheduler

```bash
gcloud scheduler jobs create pubsub b24-token-refresh-job \
  --project=$PROJECT_ID \
  --schedule='*/30 * * * *' \
  --topic=b24-token-refresh-trigger \
  --message-body='{}' \
  --location=$GCP_REGION \
  --description="Refresh Bitrix24 OAuth tokens every 30 minutes"
```

## Тестирование

### Ручной запуск обновления токенов

```bash
gcloud scheduler jobs run b24-token-refresh-job \
  --project=$PROJECT_ID \
  --location=$GCP_REGION
```

### Просмотр логов

```bash
gcloud functions logs read b24-token-refresh \
  --project=$PROJECT_ID \
  --region=$GCP_REGION \
  --limit=50
```

### Проверка токенов

```bash
# Проверить версии access token
gcloud secrets versions list b24-access-token --project=$PROJECT_ID

# Получить текущий access token
gcloud secrets versions access latest --secret=b24-access-token --project=$PROJECT_ID
```

### Тестовый запрос к Bitrix24 API

```bash
# Получить access token
ACCESS_TOKEN=$(gcloud secrets versions access latest --secret=b24-access-token --project=$PROJECT_ID)

# Тестовый запрос
curl "https://[YOUR_DOMAIN].bitrix24.pl/rest/user.current.json?auth=$ACCESS_TOKEN"
```

## Использование в других сервисах

### Вариант 1: Через Secret Manager (рекомендуется)

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

## Мониторинг

### Метрики

- Успешность обновления токенов
- Ошибки обновления
- Время выполнения

### Алерты

Настройте алерты в Cloud Monitoring для:
- Ошибок обновления токенов
- Превышения времени выполнения
- Частых обращений к Secret Manager

## Troubleshooting

### Token refresh failed

**Причины:**
1. Истёк refresh_token (требуется повторная авторизация)
2. Неверный Client ID или Client Secret
3. Приложение удалено или деактивировано в Bitrix24

**Решение:**
1. Проверьте логи: `gcloud functions logs read b24-token-refresh`
2. Повторите процесс получения токенов из инструкции
3. Обновите секреты в Secret Manager

### Permission denied

**Решение:**

```bash
SERVICE_ACCOUNT="${PROJECT_ID}@appspot.gserviceaccount.com"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$SERVICE_ACCOUNT" \
  --role="roles/secretmanager.secretAccessor"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$SERVICE_ACCOUNT" \
  --role="roles/secretmanager.secretVersionManager"
```

## Стоимость

Примерные ежемесячные затраты:

| Сервис | Использование | Стоимость |
|--------|---------------|-----------|
| Cloud Functions | ~1,440 вызовов/месяц | ~$0.01 |
| Secret Manager | 4 секрета, ~2,880 операций | ~$0.18 |
| Cloud Scheduler | 1 задача | $0.10 |
| Pub/Sub | <1MB данных | ~$0.01 |
| **Итого** | | **~$0.30/месяц** |

## Связанные документы

- [Bitrix24 OAuth Setup Guide](../../docs/instructions/b24-oauth-setup.md)
- [Logging Guide](../../docs/instructions/logging-guide.md)

## Версия

- **Проект:** mojo_agency
- **Версия:** 1.0
- **Дата создания:** 2026-01-18
