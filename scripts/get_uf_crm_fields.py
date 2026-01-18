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
        response.raise_for_status()  # Генерирует исключение для HTTP-ошибок (4xx или 5xx)
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Ошибка при вызове API метода '{method}': {e}")
        return None

def get_all_smart_processes():
    """
    Получает список всех смарт-процессов с их title и entityTypeId.
    """
    print("Получение списка всех смарт-процессов...")
    result = execute_bx24_api_call('crm.type.list')

    if not result or 'result' not in result or 'types' not in result['result']:
        print("Не удалось получить список смарт-процессов. Ответ пуст или некорректен.")
        return []

    all_types = result['result']['types']
    print(f"Всего найдено {len(all_types)} смарт-процессов.")

    # Возвращаем список словарей с нужной информацией
    return [{'title': sp.get('title'), 'entityTypeId': sp.get('entityTypeId')} for sp in all_types]

def get_fields_for_entity(entity_type_id):
    """
    Получает все поля для указанного entityTypeId.
    """
    params = {'entityTypeId': entity_type_id}
    result = execute_bx24_api_call('crm.item.fields', params)

    if not result or 'result' not in result or 'fields' not in result['result']:
        print(f"Не удалось получить поля для entityTypeId {entity_type_id}.")
        return {}

    return result['result']['fields']


# --- Main Execution ---

if __name__ == "__main__":
    print("--- Запуск скрипта для получения всех полей смарт-процессов Bitrix24 ---")

    all_smart_processes = get_all_smart_processes()

    if not all_smart_processes:
        print("\nНе удалось найти ни одного смарт-процесса.")
    else:
        print("\n--- Получение полей для каждого процесса ---")
        all_processes_fields_data = {}
        for process in all_smart_processes:
            title = process['title']
            entity_id = process['entityTypeId']

            if not title or not entity_id:
                continue

            print(f"\n--- Смарт-процесс: '{title}' (entityTypeId: {entity_id}) ---")

            fields = get_fields_for_entity(entity_id)

            if fields:
                all_processes_fields_data[title] = {
                    "entityTypeId": entity_id,
                    "fields": fields
                }
                print(f"Найдено {len(fields)} полей. Список для алиасов:")
                # Выводим информацию в удобном для алиасов виде
                for field_name, field_data in fields.items():
                    field_title = field_data.get('title', 'Без названия')
                    field_type = field_data.get('type', 'unknown')
                    # Для системных полей title может отсутствовать, используем field_name
                    if not field_title:
                        field_title = field_name
                    print(f"  {field_name}: {field_title} ({field_type})")
            else:
                print("Поля не найдены для этого смарт-процесса.")

        # Сохраняем все найденные поля в один JSON-файл
        if all_processes_fields_data:
            output_dir = os.path.dirname(os.path.abspath(__file__))
            output_filename = os.path.join(output_dir, "all_smart_process_fields.json")

            with open(output_filename, 'w', encoding='utf-8') as f:
                json.dump(all_processes_fields_data, f, indent=4, ensure_ascii=False)
            print(f"\n--- Скрипт завершен. Полная информация по всем полям сохранена в файл: '{output_filename}' ---")
        else:
             print(f"\n--- Скрипт завершен. Не найдено ни одного поля. ---")
