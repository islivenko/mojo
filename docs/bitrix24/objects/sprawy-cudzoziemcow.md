# Sprawy cudzoziemców (SPA 1038)

> **Объект: Дела иностранцев**
>
> Версия: 1.0 | Последнее обновление: 2026-01-04

---

## 🎯 Назначение объекта

**Sprawy cudzoziemców** - главная сущность модуля Legalizacja, которая консолидирует всю информацию по иностранцу и его делу легализации.

**Основные функции:**
- Центральная точка хранения данных о кандидате
- Агрегация связей со всеми связанными объектами
- Отслеживание статуса дела
- Управление процессом легализации

---

## 📊 Структура данных

### Основные поля

| Поле | Тип | Обязательное | Описание |
|------|-----|--------------|----------|
| `ID` | Integer | Да | Уникальный идентификатор дела |
| `TITLE` | String | Да | Название дела (автогенерация) |
| `STAGE_ID` | String | Да | Стадия дела |
| `CREATED_TIME` | DateTime | Да | Дата создания |
| `UPDATED_TIME` | DateTime | Да | Дата последнего обновления |

### Пользовательские поля (UF_CRM_*)

#### Секция: Dane podstawowe (Основные данные)

| Поле | Код поля | Тип | Описание |
|------|----------|-----|----------|
| Umowy abonamentowe | `ufCrm_...` | Связь | Связь с абонементными договорами |
| Osoba odpowiedzialna | `ASSIGNED_BY_ID` | User | Ответственное лицо |

#### Секция: Dane osobowe (Персональные данные)

| Поле | Код поля | Тип | Описание |
|------|----------|-----|----------|
| Cudzoziemiec (Kontakt) | `CONTACT_ID` | Contact | Связь с контактом кандидата |
| Nazwisko imię kandydata | `ufCrm_...` | String | Фамилия и имя (синхронизируется с Contact) |
| Paszport | `ufCrm_...` | String | Номер паспорта (синхронизируется с Contact) |
| Data urodzin | `ufCrm_...` | Date | Дата рождения (синхронизируется с Contact) |

#### Секция: Informacja o wnioskach (Информация о заявлениях)

| Поле | Код поля | Тип | Описание |
|------|----------|-----|----------|
| Wnioski | `ufCrm_...` | CRM (Wnioski) | Связь с заявлениями |

#### Секция: Informacja o podstawach pobytu (Информация об основаниях пребывания)

| Поле | Код поля | Тип | Описание |
|------|----------|-----|----------|
| Aktualne Podstawy pobytu | `ufCrm_...` | CRM (SPA 1050) | Активные основания пребывания |
| Data ważności podstawy pobytu | `ufCrm_...` | Date | Дата действия основания |

#### Секция: Informacja o uprawnieniach do pracy (Информация о разрешениях на работу)

| Поле | Код поля | Тип | Описание |
|------|----------|-----|----------|
| Aktualne uprawnienia do pracy | `ufCrm_...` | CRM (SPA 1046) | Активные разрешения на работу |

#### Секция: Informacja o zatrudnieniu (Информация о трудоустройстве)

| Поле | Код поля | Тип | Описание |
|------|----------|-----|----------|
| Umowy | `ufCrm_...` | CRM (SPA 1070) | Договоры с кандидатом |
| Stanowisko | `ufCrm_...` | CRM (Stanowiska) | Должность кандидата |

> ⚠️ **TODO:** Получить актуальные коды полей (`ufCrm_*`) через Bitrix24 REST API:
> ```bash
> curl "https://[DOMAIN].bitrix24.pl/rest/crm.type.fields?entityTypeId=1038"
> ```

---

## 📝 Структура формы

Карточка дела организована в **6 секций**:

```mermaid
graph TB
    subgraph Form["📋 Форма Sprawy cudzoziemców"]
        S1["📋 Dane podstawowe<br/>(Основные данные)"]
        S2["👤 Dane osobowe<br/>(Персональные данные)"]
        S3["📝 Informacja o wnioskach<br/>(Заявления)"]
        S4["🛂 Informacja o podstawach pobytu<br/>(Основания пребывания)"]
        S5["💼 Informacja o uprawnieniach do pracy<br/>(Разрешения на работу)"]
        S6["🤝 Informacja o zatrudnieniu<br/>(Трудоустройство)"]
    end

    S1 -.-> F1["• Umowy abonamentowe<br/>• Osoba odpowiedzialna"]
    S2 -.-> F2["• Cudzoziemiec (Kontakt)<br/>• Nazwisko imię<br/>• Paszport<br/>• Data urodzin"]
    S3 -.-> F3["• Wnioski (список)"]
    S4 -.-> F4["• Aktualne Podstawy pobytu<br/>• Data ważności"]
    S5 -.-> F5["• Aktualne uprawnienia"]
    S6 -.-> F6["• Umowy<br/>• Stanowisko"]

    style Form fill:#f9f9f9,stroke:#333,stroke-width:2px
    style S1 fill:#e3f2fd,stroke:#1976d2
    style S2 fill:#fff3e0,stroke:#f57c00
    style S3 fill:#f3e5f5,stroke:#7b1fa2
    style S4 fill:#e8f5e9,stroke:#388e3c
    style S5 fill:#fce4ec,stroke:#c2185b
    style S6 fill:#e0f2f1,stroke:#00796b

    style F1 fill:#fff,stroke:#1976d2,stroke-dasharray: 5 5
    style F2 fill:#fff,stroke:#f57c00,stroke-dasharray: 5 5
    style F3 fill:#fff,stroke:#7b1fa2,stroke-dasharray: 5 5
    style F4 fill:#fff,stroke:#388e3c,stroke-dasharray: 5 5
    style F5 fill:#fff,stroke:#c2185b,stroke-dasharray: 5 5
    style F6 fill:#fff,stroke:#00796b,stroke-dasharray: 5 5
```

### 📋 Dane podstawowe (Основные данные)
```
┌─────────────────────────────────────────┐
│ Umowy abonamentowe:    [Выбор договора] │
│ Osoba odpowiedzialna:  [Выбор юзера]    │
└─────────────────────────────────────────┘
```

### 👤 Dane osobowe (Персональные данные)
```
┌─────────────────────────────────────────┐
│ Cudzoziemiec (Kontakt): [Выбор контакта]│
│ Nazwisko imię kandydata: [Текст]        │
│ Paszport:                [Текст]        │
│ Data urodzin:            [Дата]         │
└─────────────────────────────────────────┘
```
> 🔄 Поля синхронизируются автоматически с Contact

### 📝 Informacja o wnioskach (Информация о заявлениях)
```
┌─────────────────────────────────────────┐
│ Wnioski:  [Список связанных заявлений]  │
│           • Wniosek #1 (Status)         │
│           • Wniosek #2 (Status)         │
└─────────────────────────────────────────┘
```

### 🛂 Informacja o podstawach pobytu (Информация об основаниях пребывания)
```
┌─────────────────────────────────────────┐
│ Aktualne Podstawy pobytu:               │
│   • Wiza (01.01.2024 - 01.06.2024)      │
│   • Karta pobytu (01.07.2024 - ...)     │
│                                         │
│ Data ważności podstawy pobytu:          │
│   [01.07.2026]                          │
└─────────────────────────────────────────┘
```
> 🔄 Только активные элементы (исключая SUCCESS/FAIL)

### 💼 Informacja o uprawnieniach do pracy (Информация о разрешениях на работу)
```
┌─────────────────────────────────────────┐
│ Aktualne uprawnienia do pracy:          │
│   • Zezwolenie typu A (до 01.12.2025)   │
└─────────────────────────────────────────┘
```
> 🔄 Только активные элементы

### 🤝 Informacja o zatrudnieniu (Информация о трудоустройстве)
```
┌─────────────────────────────────────────┐
│ Umowy:      [Список договоров]          │
│             • Umowa #123 (Active)       │
│                                         │
│ Stanowisko: [Wybrane stanowisko]        │
│             Magazynier - Warszawa       │
└─────────────────────────────────────────┘
```

---

## ⚙️ Свойства объекта

### Связи (Relations)

```mermaid
graph TB
    Contact["Contact<br/>(Контакт кандидата)"]
    Sprawy["Sprawy cudzoziemców<br/>(SPA 1038)<br/>🎯 Главная сущность"]
    Podstawy["Podstawy pobytu<br/>(SPA 1050)<br/>🛂 Основания пребывания"]
    Uprawnienia["Uprawnienia do pracy<br/>(SPA 1046)<br/>💼 Разрешения на работу"]
    Wnioski["Wnioski<br/>📝 Заявления"]
    Umowy["Umowy<br/>(SPA 1070)<br/>📄 Договоры"]
    Stanowiska["Stanowiska<br/>🤝 Должности"]
    Zalaczniki["Załączniki<br/>(SPA 1054)<br/>📎 Документы"]

    Contact -->|"1:N"| Sprawy
    Sprawy -->|"1:N"| Podstawy
    Sprawy -->|"1:N"| Uprawnienia
    Sprawy -->|"1:N"| Wnioski
    Sprawy -->|"1:N"| Umowy
    Sprawy -->|"1:N"| Stanowiska
    Sprawy -->|"1:N"| Zalaczniki

    style Sprawy fill:#9cf,stroke:#36f,stroke-width:3px
    style Contact fill:#fc9,stroke:#f60,stroke-width:2px
    style Podstawy fill:#cfc,stroke:#6a6,stroke-width:2px
    style Uprawnienia fill:#cfc,stroke:#6a6,stroke-width:2px
    style Wnioski fill:#cfc,stroke:#6a6,stroke-width:2px
    style Umowy fill:#cfc,stroke:#6a6,stroke-width:2px
    style Stanowiska fill:#cfc,stroke:#6a6,stroke-width:2px
    style Zalaczniki fill:#cfc,stroke:#6a6,stroke-width:2px
```

### Автоматизация полей

| Поле | Источник | Триггер | Описание |
|------|----------|---------|----------|
| `TITLE` | Auto | Создание/Обновление | `{LAST_NAME} {NAME} • Sprawa nr. {ID}` |
| `Nazwisko imię kandydata` | Contact | Обновление Contact | Синхронизация ФИО |
| `Paszport` | Contact | Обновление Contact | Синхронизация номера паспорта |
| `Data urodzin` | Contact | Обновление Contact | Синхронизация даты рождения |
| `Aktualne Podstawy pobytu` | SPA 1050 | Создание/Обновление Podstawy | Фильтр активных |
| `Aktualne uprawnienia do pracy` | SPA 1046 | Создание/Обновление Uprawnienia | Фильтр активных |
| `Umowy` | SPA 1070 | Создание/Обновление Umowy | Фильтр активных |

### Стадии (Stages)

> ⚠️ **TODO:** Документировать стадии дела (получить через API или из Bitrix24)

```mermaid
stateDiagram-v2
    [*] --> NEW

    NEW --> IN_PROGRESS : Взять в работу
    IN_PROGRESS --> DOCUMENTS_COLLECTION : Начать сбор документов

    DOCUMENTS_COLLECTION --> APPLICATION_SUBMITTED : Подать заявление
    DOCUMENTS_COLLECTION --> IN_PROGRESS : Вернуть в работу

    APPLICATION_SUBMITTED --> WAITING_DECISION : Ожидание решения

    WAITING_DECISION --> COMPLETED : Одобрено
    WAITING_DECISION --> IN_PROGRESS : Доработка

    IN_PROGRESS --> CANCELLED : Отменить
    DOCUMENTS_COLLECTION --> CANCELLED : Отменить
    APPLICATION_SUBMITTED --> CANCELLED : Отменить
    WAITING_DECISION --> CANCELLED : Отказ

    COMPLETED --> [*]
    CANCELLED --> [*]

    note right of NEW
        Новое дело
        Создано автоматически
    end note

    note right of DOCUMENTS_COLLECTION
        Сбор документов
        OCR паспортов
    end note

    note right of COMPLETED
        Успешное завершение
        Легализация завершена
    end note
```

**Стадии:**
- `NEW` - Новое дело
- `IN_PROGRESS` - В работе
- `DOCUMENTS_COLLECTION` - Сбор документов
- `APPLICATION_SUBMITTED` - Заявление подано
- `WAITING_DECISION` - Ожидание решения
- `COMPLETED` - Завершено
- `CANCELLED` - Отменено

---

## 🔄 Процессы

### 1. Создание дела

**Триггер:** Создание нового Contact кандидата

**Шаги:**
1. Создаётся новый элемент Sprawy cudzoziemców
2. Устанавливается связь с Contact (`CONTACT_ID`)
3. Автоматически заполняется `TITLE`
4. Синхронизируются базовые данные из Contact
5. Устанавливается стадия `NEW`

**Ответственные сервисы:**
- Bitrix24 Automation Rules

### 2. Синхронизация данных с Contact

**Триггер:** Обновление Contact

```mermaid
sequenceDiagram
    participant B24 as Bitrix24
    participant HTTP as b24-spa-1038-sync<br/>(HTTP)
    participant PS as Pub/Sub
    participant W as b24-spa-1038-sync<br/>(Worker)
    participant SM as Secret Manager
    participant Sprawy as Sprawy cudzoziemców<br/>(SPA 1038)

    B24->>HTTP: Webhook: Contact updated
    activate HTTP
    HTTP->>PS: Publish message
    HTTP-->>B24: 200 OK
    deactivate HTTP

    PS->>W: Trigger Worker
    activate W
    W->>SM: Get access_token
    SM-->>W: Token

    W->>B24: Get Contact data
    B24-->>W: Contact fields

    W->>B24: Find related Sprawy
    B24-->>W: List of Sprawy IDs

    loop Для каждого дела
        W->>Sprawy: Update fields<br/>• Nazwisko imię<br/>• Paszport<br/>• Data urodzin<br/>• TITLE
        Sprawy-->>W: Updated
    end

    W->>B24: Post to Timeline
    deactivate W

    Note over W,Sprawy: Ежедневная синхронизация: 03:00
```

**Ответственные сервисы:**
- `b24-spa-1038-sync` (HTTP + Worker)

**Расписание:**
- По триггеру: при обновлении Contact
- Ежедневно: 03:00 (полная синхронизация)

### 3. Синхронизация связей с SPA объектами

**Триггер:** Создание/обновление связанных объектов

```mermaid
sequenceDiagram
    participant SPA as SPA Object<br/>(Podstawy/Uprawnienia/Umowy)
    participant B24 as Bitrix24
    participant HTTP as b24-spa-1038-sync<br/>(HTTP)
    participant PS as Pub/Sub
    participant W as Worker
    participant Sprawy as Sprawy cudzoziemców

    SPA->>B24: Create/Update item
    B24->>HTTP: Webhook: Item changed
    activate HTTP
    HTTP->>PS: Publish message
    HTTP-->>B24: 200 OK
    deactivate HTTP

    PS->>W: Trigger Worker
    activate W

    W->>B24: Get parent Sprawy ID
    B24-->>W: Parent ID

    W->>B24: Get all related items
    B24-->>W: List of items

    W->>W: Filter active items<br/>(exclude SUCCESS/FAIL)

    W->>Sprawy: Update "Aktualne ..." fields
    Sprawy-->>W: Updated

    W->>Sprawy: Update dates
    Sprawy-->>W: Updated

    W->>B24: Post to Timeline
    deactivate W

    Note over W: Фильтрация:<br/>✅ ACTIVE, IN_PROGRESS<br/>❌ SUCCESS, FAIL
```

**Ответственные сервисы:**
- `b24-spa-1038-sync` (HTTP + Worker)

**Расписание:**
- По триггеру: при создании/обновлении связанных объектов
- Ежедневно: 03:00 (полная синхронизация)

### 4. Обработка документов

**Триггер:** Загрузка файла в связанный Załączniki (SPA 1054)

```mermaid
sequenceDiagram
    participant User as Пользователь
    participant Zal as Załączniki<br/>(SPA 1054)
    participant B24 as Bitrix24
    participant OCR_HTTP as b24-ocr-http
    participant PS1 as Pub/Sub<br/>(OCR)
    participant OCR_W as b24-ocr-worker
    participant DocAI as Document AI
    participant Gemini as Gemini AI
    participant Contact as Contact
    participant Sync as b24-spa-1038-sync
    participant Sprawy as Sprawy cudzoziemców

    User->>Zal: Upload passport file
    Zal->>B24: File uploaded
    B24->>OCR_HTTP: Webhook: File added
    activate OCR_HTTP
    OCR_HTTP->>PS1: Publish OCR task
    OCR_HTTP-->>B24: 200 OK
    deactivate OCR_HTTP

    PS1->>OCR_W: Trigger OCR Worker
    activate OCR_W

    OCR_W->>B24: Download file
    B24-->>OCR_W: File (PDF/Image)

    OCR_W->>DocAI: OCR request
    activate DocAI
    DocAI-->>OCR_W: Raw text + MRZ
    deactivate DocAI

    OCR_W->>Gemini: Parse passport data
    activate Gemini
    Gemini-->>OCR_W: Structured data<br/>(passport_number, name, etc.)
    deactivate Gemini

    OCR_W->>Contact: Update fields
    Contact-->>OCR_W: Updated

    OCR_W->>B24: Post to Timeline
    deactivate OCR_W

    Note over Contact,Sync: Автоматическая синхронизация

    Contact->>Sync: Trigger sync
    activate Sync
    Sync->>Sprawy: Update from Contact
    Sprawy-->>Sync: Updated
    deactivate Sync

    Note over OCR_W,Gemini: Извлекаются:<br/>• Номер паспорта<br/>• ФИО<br/>• Дата рождения<br/>• Гражданство<br/>• Даты выдачи/окончания
```

**Ответственные сервисы:**
- `b24-ocr` (HTTP + Worker)
- `b24-spa-1038-sync` (для синхронизации)

---

## 🔧 Функциональность

### Автоматизации

#### 1. Автогенерация Title

**Что делает:**
- Автоматически формирует название дела

**Формат:**
```
{LAST_NAME} {NAME} • Sprawa nr. {ID}
```

**Пример:**
```
KOWALSKI Jan • Sprawa nr. 1234
```

**Триггер:**
- Создание дела
- Обновление Contact (изменение имени)

#### 2. Синхронизация с Contact

**Что делает:**
- Автоматически синхронизирует персональные данные

**Синхронизируемые поля:**
- Contact.NAME + Contact.LAST_NAME → Nazwisko imię kandydata
- Contact.UF_CRM_1765737216852 → Paszport
- Contact.BIRTHDATE → Data urodzin

**Триггер:**
- Обновление Contact
- Ежедневная синхронизация (03:00)

#### 3. Фильтрация активных связей

**Что делает:**
- Автоматически обновляет списки активных элементов
- Исключает элементы со статусами SUCCESS/FAIL

**Применяется к:**
- Aktualne Podstawy pobytu
- Aktualne uprawnienia do pracy
- Umowy (активные договоры)

**Триггер:**
- Создание/обновление связанных объектов
- Изменение статуса связанного объекта
- Ежедневная синхронизация (03:00)

### REST API методы

#### Получение дела

```bash
curl -X POST "https://[DOMAIN].bitrix24.pl/rest/crm.item.get" \
  -d "entityTypeId=1038" \
  -d "id=1234" \
  -d "auth=[ACCESS_TOKEN]"
```

#### Создание дела

```bash
curl -X POST "https://[DOMAIN].bitrix24.pl/rest/crm.item.add" \
  -d "entityTypeId=1038" \
  -d "fields[contactId]=5678" \
  -d "fields[assignedById]=1" \
  -d "auth=[ACCESS_TOKEN]"
```

#### Обновление дела

```bash
curl -X POST "https://[DOMAIN].bitrix24.pl/rest/crm.item.update" \
  -d "entityTypeId=1038" \
  -d "id=1234" \
  -d "fields[ufCrm_...]=value" \
  -d "auth=[ACCESS_TOKEN]"
```

#### Получение списка дел

```bash
curl -X POST "https://[DOMAIN].bitrix24.pl/rest/crm.item.list" \
  -d "entityTypeId=1038" \
  -d "filter[stageId]=IN_PROGRESS" \
  -d "order[id]=DESC" \
  -d "auth=[ACCESS_TOKEN]"
```

---

## 📊 Метрики и KPI

### Основные метрики

| Метрика | Описание | Источник |
|---------|----------|----------|
| Количество активных дел | Дела в работе (не завершены) | `filter[stageId]!=COMPLETED` |
| Среднее время обработки | От создания до завершения | `CREATED_TIME` → `CLOSED_TIME` |
| Процент успешных дел | Завершённые vs отменённые | `COMPLETED` / `CANCELLED` |
| Полнота заполнения | % заполненных обязательных полей | Анализ полей |

### Дашборды

#### 1. Воронка дел по стадиям

```mermaid
graph LR
    subgraph Воронка["📊 Воронка дел по стадиям"]
        NEW["NEW<br/>15 дел<br/>18%"]
        PROGRESS["IN_PROGRESS<br/>25 дел<br/>30%"]
        DOCS["DOCUMENTS<br/>18 дел<br/>22%"]
        APP["APPLICATION<br/>12 дел<br/>14%"]
        WAIT["WAITING<br/>8 дел<br/>10%"]
        DONE["COMPLETED<br/>5 дел<br/>6%"]
    end

    NEW ==>|83%| PROGRESS
    PROGRESS ==>|72%| DOCS
    DOCS ==>|67%| APP
    APP ==>|67%| WAIT
    WAIT ==>|63%| DONE

    style NEW fill:#e3f2fd,stroke:#1976d2,stroke-width:3px
    style PROGRESS fill:#fff3e0,stroke:#f57c00,stroke-width:3px
    style DOCS fill:#f3e5f5,stroke:#7b1fa2,stroke-width:3px
    style APP fill:#e8f5e9,stroke:#388e3c,stroke-width:3px
    style WAIT fill:#fce4ec,stroke:#c2185b,stroke-width:3px
    style DONE fill:#c8e6c9,stroke:#2e7d32,stroke-width:3px
```

#### 2. Статистика по ответственным

| Ответственный | Активных дел | Завершено | Средн. время |
|---------------|--------------|-----------|--------------|
| Иванов И.     | 12           | 45        | 28 дней      |
| Петров П.     | 8            | 32        | 31 день      |

---

## 🔗 Связанные документы

- [Legalizacja Module Overview](../legalizacja-module.md) - Обзор модуля
- [Podstawy pobytu (SPA 1050)](./podstawy-pobytu.md) - Основания пребывания
- [Uprawnienia do pracy (SPA 1046)](./uprawnienia-do-pracy.md) - Разрешения на работу
- [Załączniki (SPA 1054)](./zalaczniki.md) - Документы и вложения
- [b24-spa-1038-sync Service](../../google-cloud/b24-spa-1038-sync/README.md) - Сервис синхронизации

---

## 📅 История изменений

### 2026-01-04
- ✅ Создан документ объекта Sprawy cudzoziemców
- ✅ Документирована структура данных
- ✅ Документирована структура формы (6 секций)
- ✅ Описаны свойства и связи
- ✅ Описаны процессы синхронизации
- ✅ Документирована функциональность

### 2026-01-03
- ✅ Реализована синхронизация всех связей
- ✅ Реализована интеграция с OCR

---

**Автор:** KeyFrame Lab
**Версия:** 1.0
**Дата создания:** 2026-01-04

