### Руководство по работе с Mermaid диаграммами в Cursor

Это руководство описывает настройку, синтаксис и лучшие практики создания диаграмм Mermaid в среде Cursor. Mermaid — язык описания диаграмм на основе текста, интегрированный с Markdown.

---

#### 1. Установка и настройка

**Расширение для Cursor/VSCode:**

```
bierner.markdown-mermaid
```

**Установка:**
1. Откройте Cursor → Extensions (Ctrl/Cmd + Shift + X)
2. Найдите `Markdown Preview Mermaid Support`
3. Нажмите Install

**Проверка установки:**
1. Создайте файл `test.md`
2. Добавьте простую диаграмму (см. пример ниже)
3. Откройте Preview (Ctrl/Cmd + Shift + V)

```mermaid
graph LR
    A[Установка] --> B[Тест] --> C[Успех!]
```

---

#### 2. Типы диаграмм

Mermaid поддерживает множество типов диаграмм. Ниже — наиболее полезные для документации проектов.

##### 2.1. Flowchart (graph) — Блок-схемы

**Направления:**
- `TB` / `TD` — сверху вниз (Top to Bottom)
- `BT` — снизу вверх (Bottom to Top)
- `LR` — слева направо (Left to Right)
- `RL` — справа налево (Right to Left)

**Базовый синтаксис:**

```mermaid
graph TD
    A[Прямоугольник] --> B(Скруглённый)
    B --> C{Ромб/Условие}
    C -->|Да| D[Результат 1]
    C -->|Нет| E[Результат 2]
    D --> F((Круг))
    E --> F
```

**Формы узлов:**

| Синтаксис | Форма |
|-----------|-------|
| `A[text]` | Прямоугольник |
| `A(text)` | Скруглённый прямоугольник |
| `A((text))` | Круг |
| `A{text}` | Ромб |
| `A[[text]]` | Подпрограмма |
| `A[(text)]` | Цилиндр (БД) |
| `A>text]` | Флаг |
| `A{{text}}` | Шестиугольник |

**Типы связей:**

| Синтаксис | Описание |
|-----------|----------|
| `A --> B` | Стрелка |
| `A --- B` | Линия без стрелки |
| `A -.-> B` | Пунктирная стрелка |
| `A ==> B` | Жирная стрелка |
| `A --text--> B` | Стрелка с текстом |
| `A -->|text| B` | Альтернативный текст |

---

##### 2.2. Sequence Diagram — Диаграммы последовательности

Идеальны для документирования API-взаимодействий и процессов.

```mermaid
sequenceDiagram
    participant C as Client
    participant S as Server
    participant DB as Database

    C->>S: HTTP Request
    activate S
    S->>DB: Query
    activate DB
    DB-->>S: Result
    deactivate DB
    S-->>C: Response
    deactivate S

    Note over C,S: Синхронный вызов
    Note right of DB: Данные кэшируются
```

**Типы стрелок:**

| Синтаксис | Описание |
|-----------|----------|
| `A->>B` | Сплошная линия со стрелкой |
| `A-->>B` | Пунктирная линия со стрелкой |
| `A-xB` | Сплошная линия с крестом |
| `A--xB` | Пунктирная линия с крестом |
| `A-)B` | Сплошная линия с открытой стрелкой (async) |
| `A--)B` | Пунктирная с открытой стрелкой |

**Дополнительные элементы:**

```mermaid
sequenceDiagram
    participant A
    participant B

    rect rgb(200, 220, 255)
        Note over A,B: Группа операций
        A->>B: Запрос 1
        B-->>A: Ответ 1
    end

    alt Условие истинно
        A->>B: Путь А
    else Условие ложно
        A->>B: Путь Б
    end

    loop Каждые 5 минут
        A->>B: Heartbeat
    end

    opt Опционально
        A->>B: Необязательный шаг
    end
```

---

##### 2.3. Class Diagram — Диаграммы классов

Полезны для документирования структур данных и API-моделей.

```mermaid
classDiagram
    class User {
        +int id
        +string email
        +string name
        +login()
        +logout()
    }

    class Order {
        +int id
        +datetime created
        +float total
        +calculate_total()
    }

    class Product {
        +int id
        +string name
        +float price
    }

    User "1" --> "*" Order : places
    Order "*" --> "*" Product : contains
```

**Отношения:**

| Синтаксис | Тип связи |
|-----------|-----------|
| `A <\|-- B` | Наследование |
| `A *-- B` | Композиция |
| `A o-- B` | Агрегация |
| `A --> B` | Ассоциация |
| `A -- B` | Связь |
| `A ..> B` | Зависимость |
| `A ..\|> B` | Реализация |

---

##### 2.4. Entity Relationship Diagram — ER-диаграммы

Для документирования структуры баз данных.

```mermaid
erDiagram
    USER ||--o{ ORDER : places
    ORDER ||--|{ ORDER_LINE : contains
    PRODUCT ||--o{ ORDER_LINE : "ordered in"

    USER {
        int id PK
        string email UK
        string name
        datetime created_at
    }

    ORDER {
        int id PK
        int user_id FK
        datetime created_at
        string status
    }

    PRODUCT {
        int id PK
        string name
        decimal price
    }

    ORDER_LINE {
        int order_id FK
        int product_id FK
        int quantity
    }
```

**Кардинальность:**

| Синтаксис | Значение |
|-----------|----------|
| `\|\|` | Ровно один |
| `o\|` | Ноль или один |
| `}\|` | Один или много |
| `}o` | Ноль или много |

---

##### 2.5. State Diagram — Диаграммы состояний

Для документирования жизненного цикла объектов.

```mermaid
stateDiagram-v2
    [*] --> Draft

    Draft --> Pending : submit()
    Pending --> Approved : approve()
    Pending --> Rejected : reject()
    Rejected --> Draft : revise()
    Approved --> [*]

    state Pending {
        [*] --> UnderReview
        UnderReview --> AwaitingApproval
        AwaitingApproval --> [*]
    }
```

---

##### 2.6. Pie Chart — Круговые диаграммы

```mermaid
pie showData
    title Распределение задач
    "Завершено" : 45
    "В работе" : 30
    "Ожидание" : 15
    "Отменено" : 10
```

---

##### 2.7. Gantt Chart — Диаграммы Ганта

```mermaid
gantt
    title План проекта
    dateFormat  YYYY-MM-DD
    excludes    weekends

    section Анализ
    Сбор требований     :a1, 2025-01-06, 5d
    Архитектура         :a2, after a1, 3d

    section Разработка
    Backend API         :b1, after a2, 10d
    Frontend            :b2, after a2, 12d

    section Тестирование
    Интеграция          :c1, after b1, 5d
    UAT                 :c2, after c1, 3d
```

---

##### 2.8. Git Graph — Git-ветвление

```mermaid
gitGraph
    commit id: "init"
    branch develop
    checkout develop
    commit id: "feature-1"
    commit id: "feature-2"
    checkout main
    merge develop id: "release-1.0"
    commit id: "hotfix"
    checkout develop
    commit id: "feature-3"
    checkout main
    merge develop id: "release-1.1"
```

---

#### 3. Подгруппы и стилизация

##### 3.1. Subgraph — Группировка элементов

```mermaid
graph TB
    subgraph Frontend
        A[React App]
        B[Mobile App]
    end

    subgraph Backend
        C[API Gateway]
        D[Auth Service]
        E[Data Service]
    end

    subgraph Database
        F[(PostgreSQL)]
        G[(Redis)]
    end

    A --> C
    B --> C
    C --> D
    C --> E
    D --> F
    E --> F
    D --> G
```

##### 3.2. Стилизация узлов

```mermaid
graph LR
    A[Default]
    B[Styled]
    C[Critical]

    style A fill:#f9f,stroke:#333,stroke-width:2px
    style B fill:#bbf,stroke:#00f,stroke-width:2px
    style C fill:#f00,stroke:#900,stroke-width:4px,color:#fff

    A --> B --> C
```

##### 3.3. Классы стилей

```mermaid
graph LR
    A[Service A]:::serviceClass
    B[Service B]:::serviceClass
    C[Database]:::dbClass
    D[Error]:::errorClass

    A --> C
    B --> C
    C --> D

    classDef serviceClass fill:#9cf,stroke:#36f
    classDef dbClass fill:#fc9,stroke:#f60
    classDef errorClass fill:#f99,stroke:#f00
```

---

#### 4. Интеграция с Cursor AI

##### 4.1. Промпты для генерации диаграмм

**Для архитектурных диаграмм:**
```
Создай Mermaid диаграмму архитектуры системы, включающей:
- Frontend (React)
- Backend API (FastAPI)
- База данных (PostgreSQL)
- Кэш (Redis)
- Message Queue (RabbitMQ)
```

**Для sequence диаграмм:**
```
Создай Mermaid sequence диаграмму для процесса:
1. Пользователь отправляет запрос на авторизацию
2. API проверяет токен в Redis
3. Если токен не найден — запрос к БД
4. Возврат результата пользователю
```

**Для ER диаграмм:**
```
Создай Mermaid ER диаграмму для модели:
- User (id, email, name)
- Order (id, user_id, total, status)
- Product (id, name, price)
- OrderItem (order_id, product_id, quantity)
```

##### 4.2. Рекомендации при работе с AI

1. **Указывайте тип диаграммы** — `graph`, `sequenceDiagram`, `erDiagram` и т.д.
2. **Описывайте направление** — для flowchart указывайте `TD`, `LR` и т.д.
3. **Уточняйте детали** — количество элементов, связи, группировки
4. **Просите итеративные улучшения** — "добавь подгруппу", "измени стрелки на пунктирные"

---

#### 5. Best Practices

##### 5.1. Структура файлов

```
docs/
├── architecture/
│   ├── overview.md          # Общая архитектура
│   ├── data-flow.md         # Потоки данных
│   └── deployment.md        # Инфраструктура
├── api/
│   ├── auth-flow.md         # Sequence: авторизация
│   └── order-flow.md        # Sequence: заказы
├── database/
│   ├── schema.md            # ER-диаграмма
│   └── migrations.md        # История изменений
└── diagrams.md              # Сводный файл диаграмм
```

##### 5.2. Именование

* Файлы с диаграммами — в **kebab-case**: `user-flow.md`, `api-architecture.md`
* Идентификаторы узлов — краткие и понятные: `API`, `DB`, `Cache`
* Подгруппы — с заглавной буквы: `Backend`, `Frontend`, `Database`

##### 5.3. Читаемость

* **Максимум 15-20 узлов** на одной диаграмме
* **Используйте подгруппы** для логической группировки
* **Разбивайте сложные диаграммы** на несколько уровней детализации:
  - High-level: общая архитектура
  - Mid-level: компоненты модуля
  - Low-level: детали реализации

##### 5.4. Документирование

Каждая диаграмма должна сопровождаться:
1. **Заголовком** — что изображено
2. **Контекстом** — когда/где используется
3. **Легендой** — если используются специальные обозначения

---

#### 6. Экспорт и публикация

##### 6.1. Mermaid Live Editor

Онлайн-редактор для быстрого создания и экспорта:
```
https://mermaid.live/
```

Возможности:
- Редактирование в реальном времени
- Экспорт в PNG, SVG, PDF
- Шаринг по ссылке

##### 6.2. CLI-инструмент

```bash
# Установка
npm install -g @mermaid-js/mermaid-cli

# Генерация PNG
mmdc -i diagram.mmd -o diagram.png

# Генерация SVG
mmdc -i diagram.mmd -o diagram.svg

# Генерация PDF
mmdc -i diagram.mmd -o diagram.pdf
```

##### 6.3. GitHub/GitLab интеграция

GitHub и GitLab нативно рендерят Mermaid в `.md` файлах.
Диаграммы отображаются автоматически в Preview и README.

---

#### 7. Troubleshooting

##### 7.1. Диаграмма не рендерится

**Проверьте:**
1. Установлено расширение `bierner.markdown-mermaid`
2. Код начинается с ` ```mermaid ` и заканчивается ` ``` `
3. Нет синтаксических ошибок (проверьте в Mermaid Live)

##### 7.2. Ошибки синтаксиса

**Частые проблемы:**

| Ошибка | Причина | Решение |
|--------|---------|---------|
| `Parse error` | Неверный синтаксис | Проверьте скобки и стрелки |
| `Lexical error` | Спецсимволы в тексте | Оберните текст в кавычки |
| `Unknown diagram type` | Опечатка в типе | `sequenceDiagram`, не `sequence` |

**Экранирование спецсимволов:**

```mermaid
graph LR
    A["Текст с (скобками)"]
    B["Текст с 'кавычками'"]
    A --> B
```

##### 7.3. Производительность

При большом количестве элементов (50+):
- Разбейте на несколько диаграмм
- Используйте подгруппы
- Упростите связи

---

#### 8. Шаблоны для проекта

##### 8.1. Шаблон архитектуры микросервиса

```mermaid
graph TB
    subgraph External
        Client[Client App]
        ExtAPI[External API]
    end

    subgraph "Service Name"
        GW[API Gateway]
        Auth[Auth Service]
        Core[Core Service]
        Worker[Background Worker]
    end

    subgraph Data
        DB[(PostgreSQL)]
        Cache[(Redis)]
        Queue[Message Queue]
    end

    Client --> GW
    ExtAPI --> GW
    GW --> Auth
    GW --> Core
    Core --> DB
    Core --> Cache
    Core --> Queue
    Queue --> Worker
    Worker --> DB
```

##### 8.2. Шаблон API-flow

```mermaid
sequenceDiagram
    participant C as Client
    participant GW as Gateway
    participant A as Auth
    participant S as Service
    participant DB as Database

    C->>GW: Request + Token
    GW->>A: Validate Token
    A-->>GW: OK / Error
    alt Token Valid
        GW->>S: Forward Request
        S->>DB: Query
        DB-->>S: Data
        S-->>GW: Response
        GW-->>C: 200 OK
    else Token Invalid
        GW-->>C: 401 Unauthorized
    end
```

##### 8.3. Шаблон CI/CD Pipeline

```mermaid
graph LR
    subgraph Development
        Code[Code Push]
        PR[Pull Request]
    end

    subgraph CI
        Lint[Lint]
        Test[Unit Tests]
        Build[Build]
    end

    subgraph CD
        Stage[Staging]
        Approve{Manual Approve}
        Prod[Production]
    end

    Code --> PR
    PR --> Lint
    Lint --> Test
    Test --> Build
    Build --> Stage
    Stage --> Approve
    Approve -->|Yes| Prod
    Approve -->|No| Code
```

---

**Автор:** KeyFrame Lab Team
**Версия:** 1.0
**Дата создания:** 2025-01-04
**Источники:**
- [Mermaid Official Docs](https://mermaid.js.org/intro/)
- [Cursor Mermaid Guide](https://cursor.com/docs/cookbook/mermaid-diagrams)

