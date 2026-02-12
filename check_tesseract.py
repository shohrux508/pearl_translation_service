import os
import shutil
import sys
import subprocess
import urllib.request
from pathlib import Path

TESSERACT_CMD = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
# Define local TESSDATA directory since system one is read-only
LOCAL_TESSDATA = Path(os.getcwd()) / "tessdata"
SYSTEM_TESSDATA = Path(r"C:\Program Files\Tesseract-OCR\tessdata")

DOWNLOAD_URL_TEMPLATE = "https://github.com/tesseract-ocr/tessdata/raw/main/{lang}.traineddata"

def find_tesseract():
    if shutil.which("tesseract"):
        return "tesseract"
    if os.path.exists(TESSERACT_CMD):
        return TESSERACT_CMD
    return None

def check_langs(tesseract_path, tessdata_prefix=None):
    env = os.environ.copy()
    if tessdata_prefix:
        env["TESSDATA_PREFIX"] = str(tessdata_prefix)
        
    try:
        result = subprocess.run([tesseract_path, "--list-langs"], capture_output=True, text=True, check=True, env=env)
        langs = result.stdout.strip().split('\n')[1:] # Skip first line "List of available languages..."
        return [l.strip() for l in langs]
    except subprocess.CalledProcessError as e:
        print(f"Error checking langs: {e}")
        return []

def download_lang(lang, tessdata_dir):
    url = DOWNLOAD_URL_TEMPLATE.format(lang=lang)
    dest = tessdata_dir / f"{lang}.traineddata"
    
    if dest.exists():
        print(f"{lang} already exists at {dest}")
        return True
    
    print(f"Downloading {lang} from {url} to {dest}...")
    try:
        urllib.request.urlretrieve(url, dest)
        print(f"Downloaded {lang}")
        return True
    except Exception as e:
        print(f"Failed to download {lang}: {e}")
        return False

def setup_local_tessdata():
    if not LOCAL_TESSDATA.exists():
        LOCAL_TESSDATA.mkdir(parents=True, exist_ok=True)
    
    # Copy essential English/OSD data if missing locally but present in system
    for lang in ["eng", "osd"]:
        local_path = LOCAL_TESSDATA / f"{lang}.traineddata"
        system_path = SYSTEM_TESSDATA / f"{lang}.traineddata"
        
        if not local_path.exists() and system_path.exists():
            print(f"Copying {lang} from system tessdata...")
            try:
                shutil.copy2(system_path, local_path)
            except Exception as e:
                print(f"Failed to copy {lang}: {e}")
                # Try download instead if copy fails
                download_lang(lang, LOCAL_TESSDATA)
        elif not local_path.exists():
             download_lang(lang, LOCAL_TESSDATA)

def main():
    tesseract_path = find_tesseract()
    if not tesseract_path:
        print("Tesseract not found. Please install it.")
        sys.exit(1)
    
    print(f"Found Tesseract at: {tesseract_path}")
    
    # Setup local tessdata
    setup_local_tessdata()
    
    # Download missing languages to local tessdata
    required_langs = ["rus", "uzb"]
    for lang in required_langs:
        download_lang(lang, LOCAL_TESSDATA)

    # Check languages with local TESSDATA_PREFIX
    print(f"Checking languages using TESSDATA_PREFIX={LOCAL_TESSDATA}")
    installed_langs = check_langs(tesseract_path, tessdata_prefix=LOCAL_TESSDATA)
    print(f"Installed languages: {installed_langs}")
    
    output_msg = ""
    if "rus" in installed_langs and "uzb" in installed_langs:
         output_msg = "SUCCESS: rus and uzb are installed."
    else:
         output_msg = "FAILURE: Missing required languages."
    
    print(output_msg)
    
    # Also verify without prefix just in case user managed to install them globally
    # system_langs = check_langs(tesseract_path)
    # print(f"System-wide installed languages: {system_langs}")

if __name__ == "__main__":
    main()
