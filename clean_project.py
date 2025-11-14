import os

# الرموز أو الأحرف الغريبة اللي ممكن تسبب أخطاء
BAD_CHARS = ["│", "﻿", "—", "‒", "–", "—", "―"]

def clean_file(filepath):
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        original_content = content
        for char in BAD_CHARS:
            content = content.replace(char, "")

        # لو الملف تغير فعلاً
        if content != original_content:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"✅ تم تنظيف الملف: {filepath}")
    except Exception as e:
        print(f"⚠️ تخطيت الملف {filepath}: {e}")

def clean_project(root_folder="."):
    for root, _, files in os.walk(root_folder):
        for file in files:
            if file.endswith(".py") or file.endswith(".txt"):
                clean_file(os.path.join(root, file))

if __name__ == "__main__":
    print("🚿 بدء تنظيف المشروع من الرموز الغريبة...")
    clean_project(".")
    print("✨ تم الانتهاء من التنظيف بنجاح!")
