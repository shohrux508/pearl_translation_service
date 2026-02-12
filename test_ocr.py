from PIL import Image, ImageDraw, ImageFont, ImageColor
import pytesseract
import os
import sys

# Настройка путей
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
TESSDATA_DIR = os.path.join(PROJECT_DIR, "tessdata")
TESSERACT_CMD = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# Указываем путь к исполняемому файлу
if os.path.exists(TESSERACT_CMD):
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD
else:
    print(f"WARNING: Tesseract executable not found at {TESSERACT_CMD}")

# Указываем путь к данным (языковым моделям) через переменную окружения
os.environ["TESSDATA_PREFIX"] = TESSDATA_DIR

def create_test_image(text, filename, font_path=None):
    width = 800
    height = 200
    img = Image.new('RGB', (width, height), color=(255, 255, 255))
    d = ImageDraw.Draw(img)
    
    # Пытаемся найти шрифт с подержкой кириллицы
    try:
        font = ImageFont.truetype("arial.ttf", 32)
    except IOError:
        font = ImageFont.load_default()
        print("Warning: Arial font not found, using default.")

    d.text((20, 20), text, fill=(0, 0, 0), font=font)
    img.save(filename)
    return filename

def test_language(lang, text, filename):
    print(f"--- Testing language: {lang} ---")
    create_test_image(text, filename)
    
    try:
        # Указываем язык явно
        result = pytesseract.image_to_string(Image.open(filename), lang=lang)
        print(f"Image text: '{text}'")
        print(f"OCR Result: '{result.strip()}'")
        
        if text.lower() in result.lower() or result.strip():
             if not result.strip():
                 print(f"[WARN] Empty result. Font issue?")
             else:
                 print(f"[SUCCESS] {lang} works.")
        else:
             print(f"[FAIL] Text mismatch.")
             
    except pytesseract.TesseractError as e:
        print(f"[ERROR] TesseractError: {e}")
    except Exception as e:
        print(f"[ERROR] Exception: {e}")
    finally:
        if os.path.exists(filename):
            try:
                os.remove(filename)
            except:
                pass
    print("\n")

def run_tests():
    print(f"Using TESSDATA_PREFIX: {os.environ['TESSDATA_PREFIX']}")
    
    if not os.path.exists(os.path.join(TESSDATA_DIR, "eng.traineddata")):
         print("WARNING: eng.traineddata not found in local tessdata!")
    
    test_language("eng", "Hello World 123", "test_eng.png")
    test_language("rus", "Privet Mir", "test_rus_lat.png") # Test rus with latin first just in case
    test_language("rus", "Привет мир", "test_rus.png")
    test_language("uzb", "Salom Dunyo", "test_uzb.png")

if __name__ == "__main__":
    # Force stdout to utf-8 just in case, though we removed emojis
    # sys.stdout.reconfigure(encoding='utf-8')
    run_tests()
