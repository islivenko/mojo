# Sprawy cudzoziemców (SPA 1106)

> **Smart Process для управления делами иностранцев**
>
> Entity Type ID: **1106**

---

## 📋 Общая информация

| Параметр | Значение |
|----------|----------|
| **Entity Type ID** | 1106 |
| **Название** | Sprawy cudzoziemców |
| **Код** | - |
| **Категории** | Нет |
| **Стадии** | Да |
| **Связь с контактами** | Да |
| **Документы** | Да |
| **Бизнес-процессы** | Да |

---

## 🔗 Связанные объекты

### Основные связи

SPA 1106 имеет следующие связи с другими объектами:

#### 1. **Contact** (Контакт)
- **Поле**: `contactId`
- **Тип**: `crm_contact`
- **Описание**: Основной контакт (иностранец)

#### 2. **Podstawy pobytu** (SPA 1042)
- **Поле**: `ufCrm38_1768737959`
- **Название**: "Aktualne Podstawy pobytu"
- **Тип**: `crm` с `DYNAMIC_1042`
- **Описание**: Текущие основания пребывания
- **Дополнительное поле**: `ufCrm38_1768738011252` - Дата действия

#### 3. **Uprawnienia do pracy** (SPA 1046)
- **Поле**: `ufCrm38_1768738112`
- **Название**: "Aktualne uprawnienia do pracy"
- **Тип**: `crm` с `DYNAMIC_1046`
- **Описание**: Текущие разрешения на работу
- **Дополнительное поле**: `ufCrm38_1768738327769` - Дата действия

#### 4. **Procesy legalizacyjne** (SPA 1110)
- **Поле**: `ufCrm38_1768738413`
- **Название**: "Aktualne procesy legalizacyjne"
- **Тип**: `crm` с `DYNAMIC_1110`
- **Описание**: Текущие процессы легализации

#### 5. **Klient (Projekt)** (SPA 1098)
- **Поле**: `ufCrm38_1764509491`
- **Название**: "Klient użytkownik (Projekt)"
- **Тип**: `crm` с `DYNAMIC_1098`
- **Описание**: Связь с проектом клиента

---

## 📊 Структура полей

### Системные поля

| Поле | Тип | Описание |
|------|-----|----------|
| `id` | integer | ID элемента |
| `title` | string | Название дела |
| `createdBy` | user | Создатель |
| `updatedBy` | user | Изменивший |
| `movedBy` | user | Переместивший |
| `createdTime` | datetime | Дата создания |
| `updatedTime` | datetime | Дата изменения |
| `movedTime` | datetime | Дата перемещения |
| `categoryId` | crm_category | Lejek (воронка) |
| `stageId` | crm_status | Текущий этап |
| `previousStageId` | crm_status | Предыдущий этап |

### Поля связей

| Поле | Тип | Описание |
|------|-----|----------|
| `contactId` | crm_contact | Основной контакт |
| `contactIds` | crm_contact | Дополнительные контакты |
| `companyId` | crm_company | Компания |

### Пользовательские поля

| Поле | Название | Тип | Описание |
|------|----------|-----|----------|
| `ufCrm38_1764509760429` | nr paszportu | string | Номер паспорта |
| `ufCrm38_1764509780038` | Data ważności paszportu | date | Дата действия паспорта |
| `ufCrm38_1768737959` | Aktualne Podstawy pobytu | crm (1042) | Текущие основания пребывания |
| `ufCrm38_1768738011252` | Data ważności podstawy pobytu | date | Дата действия основания пребывания |
| `ufCrm38_1768738112` | Aktualne uprawnienia do pracy | crm (1046) | Текущие разрешения на работу |
| `ufCrm38_1768738327769` | Data ważności uprawnienia do pracy | date | Дата действия разрешения на работу |
| `ufCrm38_1768738413` | Aktualne procesy legalizacyjne | crm (1110) | Текущие процессы легализации |
| `ufCrm38_1764509491` | Klient użytkownik (Projekt) | crm (1098) | Связь с проектом клиента |

---

## 🔄 Логика синхронизации

### Направления синхронизации

```
┌──────────────────────────────────────────────────────────────┐
│                     Sprawy cudzoziemców                       │
│                        (SPA 1106)                             │
│                                                               │
│  ┌─────────────────────────────────────────────────────┐    │
│  │  ufCrm38_1768737959 - Podstawy pobytu (1042)       │    │
│  │  ufCrm38_1768738112 - Uprawnienia do pracy (1046)  │    │
│  │  ufCrm38_1768738413 - Procesy legalizacyjne (1110) │    │
│  │  ufCrm38_1764509491 - Klient (Projekt) (1098)      │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                               │
│  contactId ────────────► Contact                             │
└──────────────────────────────────────────────────────────────┘
         ▲                    ▲                    ▲
         │                    │                    │
    ┌────┴────┐         ┌────┴────┐         ┌────┴────┐
    │ Podstawy│         │ Praca   │         │ Procesy │
    │  (1042) │         │ (1046)  │         │ (1110)  │
    └─────────┘         └─────────┘         └─────────┘
```

### Правила синхронизации

#### 1. **Podstawy pobytu (SPA 1042) → Sprawy (SPA 1106)**
- При создании/обновлении Podstawy:
  - Если статус **активный** → добавить ID в `ufCrm38_1768737959`
  - Если статус **финальный** → удалить ID из `ufCrm38_1768737959`
- При удалении Podstawy → удалить из всех связанных Sprawy

#### 2. **Uprawnienia do pracy (SPA 1046) → Sprawy (SPA 1106)**
- Аналогично Podstawy pobytu
- Поле связи: `ufCrm38_1768738112`

#### 3. **Procesy legalizacyjne (SPA 1110) → Sprawy (SPA 1106)**
- Аналогично Podstawy pobytu
- Поле связи: `ufCrm38_1768738413`

#### 4. **Contact → Sprawy (SPA 1106)**
- При обновлении Contact:
  - Синхронизировать поля паспорта в связанные Sprawy
  - Обновить заголовок дела (title)

---

## 🎯 Отличия от SPA 1038

| Параметр | SPA 1038 | SPA 1106 |
|----------|----------|----------|
| **Entity Type ID** | 1038 | 1106 |
| **Podstawy pobytu** | `ufCrm8_1766853901` (SPA 1050) | `ufCrm38_1768737959` (SPA 1042) |
| **Uprawnienia do pracy** | `ufCrm8_1767129764` (SPA 1046) | `ufCrm38_1768738112` (SPA 1046) |
| **Wnioski** | `ufCrm8_1767556733` (SPA 1042) | Нет прямой связи |
| **Umowy** | `ufCrm8_1767126614` (SPA 1070) | Нет прямой связи |
| **Procesy legalizacyjne** | Нет | `ufCrm38_1768738413` (SPA 1110) |
| **Klient (Projekt)** | Нет | `ufCrm38_1764509491` (SPA 1098) |

### Важно!

**SPA 1106 использует другой SPA для Podstawy pobytu:**
- SPA 1038 → использует SPA **1050** (Podstawy pobytu)
- SPA 1106 → использует SPA **1042** (Podstawy pobytu)

**SPA 1106 имеет дополнительные связи:**
- **Procesy legalizacyjne** (SPA 1110) - отсутствует в SPA 1038
- **Klient (Projekt)** (SPA 1098) - отсутствует в SPA 1038

**SPA 1106 НЕ имеет связей:**
- **Wnioski** (SPA 1042) - есть в SPA 1038
- **Umowy** (SPA 1070) - есть в SPA 1038

---

## 📝 Примечания

1. **Основания пребывания**: SPA 1106 использует SPA 1042 (не 1050 как в SPA 1038)
2. **Разрешения на работу**: Оба SPA используют одинаковый SPA 1046
3. **Новые связи**: SPA 1106 имеет связи с процессами легализации (1110) и проектами (1098)
4. **Отсутствующие связи**: В SPA 1106 нет связей с Wnioski и Umowy

---

## 🔧 Конфигурация для синхронизации

```bash
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

---

**Дата создания**: 2026-01-18
**Последнее обновление**: 2026-01-18
**Автор**: KeyFrame Lab
