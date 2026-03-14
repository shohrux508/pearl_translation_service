import os
import google.generativeai as genai
from dotenv import load_dotenv

def main():
    # Загружаем переменные окружения из .env файла
    load_dotenv()

    # Получаем API ключ
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("Ошибка: GEMINI_API_KEY не найден в переменных окружения.")
        return

    # Конфигурируем библиотеку
    genai.configure(api_key=api_key)

    print("=== Доступные модели Gemini ===")
    
    try:
        models = genai.list_models()
        count = 0
        for m in models:
            # Выводим только генеративные модели или все?
            # Если нужны только те, что могут генерировать контент:
            # if 'generateContent' in m.supported_generation_methods:
            print(f"Name: {m.name}")
            print(f"   Version: {m.version if hasattr(m, 'version') else 'N/A'}")
            print(f"   Description: {m.description}")
            print(f"   Supported Generation Methods: {', '.join(m.supported_generation_methods)}")
            print("-" * 50)
            count += 1
            
        print(f"Всего найдено моделей: {count}")
    except Exception as e:
        print(f"Произошла ошибка при получении списка моделей: {e}")

if __name__ == "__main__":
    main()
