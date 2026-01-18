import requests
import json
import os

# --- Configuration ---
# Вебхук URL для доступа к Bitrix24 REST API
WEBHOOK_URL = "https://b24-ivxa3z.bitrix24.pl/rest/8/1fd4f6kwp9aenqb0/"

# --- Functions ---

def execute_bx24_api_call(method, params=None):
    """Выполняет запрос к Bitrix24 REST API и возвращает результат."""
    if params is None:
        params = {}
    url = f"{WEBHOOK_URL}{method}"
    try:
        response = requests.post(url, json=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Ошибка при вызове API метода '{method}': {e}")
        return None

def get_contact_fields():
    """Получает все поля для сущности 'Контакт'."""
    print("Получение полей для сущности 'Контакт'...")
    result = execute_bx24_api_call('crm.contact.fields')

    if not result or 'result' not in result:
        print("Не удалось получить поля для контактов.")
        return {}

    return result['result']

# --- Main Execution ---

if __name__ == "__main__":
    print("--- Запуск скрипта для получения всех полей контактов Bitrix24 ---")

    fields = get_contact_fields()

    if fields:
        print(f"Найдено {len(fields)} полей. Список для алиасов:")
        # Выводим информацию в удобном для алиасов виде
        for field_name, field_data in fields.items():
            # Правильный приоритет для названия: сначала метка для списка, потом для формы, потом общее название
            field_title = field_data.get('listLabel') or field_data.get('formLabel') or field_data.get('title') or field_name
            field_type = field_data.get('type', 'unknown')
            print(f"  {field_name}: {field_title} ({field_type})")

        # Сохраняем все найденные поля в JSON-файл
        output_dir = os.path.dirname(os.path.abspath(__file__))
        output_filename = os.path.join(output_dir, "contact_fields.json")

        with open(output_filename, 'w', encoding='utf-8') as f:
            json.dump(fields, f, indent=4, ensure_ascii=False)
        print(f"\n--- Скрипт завершен. Полная информация по полям сохранена в файл: '{output_filename}' ---")
    else:
        print("\n--- Скрипт завершен. Поля не найдены. ---")
