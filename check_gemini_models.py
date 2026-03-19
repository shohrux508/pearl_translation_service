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

    print("\n" + "="*50)
    while True:
        model_name = input("Введите название модели для теста (например, models/gemini-2.5-flash) или 'q' для выхода: ").strip()
        if model_name.lower() in ['q', 'quit', 'exit', '']:
            break
            
        prompt = input("Введите ваш запрос: ").strip()
        if not prompt:
            print("Ошибка: Запрос не может быть пустым.")
            continue
            
        try:
            print(f"\nОтправка запроса к {model_name}...")
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(prompt)
            print("=== Ответ модели ===")
            print(response.text)
            print("====================\n")
        except Exception as e:
            print(f"Ошибка при обращении к модели: {e}\n")

if __name__ == "__main__":
    main()
