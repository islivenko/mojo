import requests
import json
import os

# --- Configuration ---
# Вебхук URL для доступа к Bitrix24 REST API
WEBHOOK_URL = "https://b24-ivxa3z.bitrix24.pl/rest/8/1fd4f6kwp9aenqb0/"
ENTITY_TYPE_ID = 1042

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

def get_fields_for_type(entity_type_id):
    """
    Получает все поля для указанного entityTypeId смарт-процесса.
    """
    params = {'entityTypeId': entity_type_id}
    result = execute_bx24_api_call('crm.type.fields', params)

    if not result or 'result' not in result or 'fields' not in result['result']:
        print(f"Не удалось получить поля для entityTypeId {entity_type_id}.")
        return {}

    return result['result']['fields']


# --- Main Execution ---

if __name__ == "__main__":
    print(f"--- Запуск скрипта для получения полей смарт-процесса с ID {ENTITY_TYPE_ID} ---")

    fields = get_fields_for_type(ENTITY_TYPE_ID)

    if fields:
        print(f"Найдено {len(fields)} полей. Список для алиасов:")
        # Выводим информацию в удобном для алиасов виде
        for field_name, field_data in fields.items():
            field_title = field_data.get('title', 'Без названия')
            field_type = field_data.get('type', 'unknown')
            # Для системных полей title может отсутствовать, используем field_name
            if not field_title:
                field_title = field_name
            print(f"  {field_name}: {field_title} ({field_type})")

        # Сохраняем все найденные поля в JSON-файл
        output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")
        os.makedirs(output_dir, exist_ok=True)
        output_filename = os.path.join(output_dir, f"smart_process_{ENTITY_TYPE_ID}_fields.json")

        with open(output_filename, 'w', encoding='utf-8') as f:
            json.dump(fields, f, indent=4, ensure_ascii=False)
        print(f"\n--- Скрипт завершен. Полная информация по полям сохранена в файл: '{output_filename}' ---")
    else:
        print("Поля не найдены для этого смарт-процесса.")
