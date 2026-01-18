import requests
import json
import os

# --- Configuration ---
# Вебхук URL для доступа к Bitrix24 REST API
WEBHOOK_URL = "https://b24-ivxa3z.bitrix24.pl/rest/8/1fd4f6kwp9aenqb0/"
ENTITY_TYPE_ID = 1042
ITEM_ID = 26

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

def get_item_from_smart_process(entity_type_id, item_id):
    """
    Получает один элемент из смарт-процесса.
    """
    params = {'entityTypeId': entity_type_id, 'id': item_id}
    result = execute_bx24_api_call('crm.item.get', params)

    if not result or 'result' not in result or 'item' not in result['result']:
        print(f"Не удалось получить элемент {item_id} для entityTypeId {entity_type_id}.")
        return {}

    return result['result']['item']


# --- Main Execution ---

if __name__ == "__main__":
    print(f"--- Запуск скрипта для получения структуры полей смарт-процесса с ID {ENTITY_TYPE_ID} через элемент {ITEM_ID} ---")

    item_data = get_item_from_smart_process(ENTITY_TYPE_ID, ITEM_ID)

    if item_data:
        # Мы получили элемент, его ключи - это и есть поля
        fields = list(item_data.keys())
        print(f"Найдено {len(fields)} полей. Список:")
        for field_name in fields:
            print(f"  {field_name}")

        # Сохраняем все найденные поля в JSON-файл
        output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")
        os.makedirs(output_dir, exist_ok=True)
        output_filename = os.path.join(output_dir, f"smart_process_{ENTITY_TYPE_ID}_fields_from_item.json")

        with open(output_filename, 'w', encoding='utf-8') as f:
            # Сохраним сам элемент, чтобы видеть и типы данных
            json.dump(item_data, f, indent=4, ensure_ascii=False)
        print(f"\n--- Скрипт завершен. Структура полей (на основе элемента) сохранена в файл: '{output_filename}' ---")
    else:
        print("Не удалось получить структуру полей.")
