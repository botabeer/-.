#!/bin/bash

echo "=========================================="
echo "بوت الحوت - سكريبت الاعداد"
echo "=========================================="
echo ""

if ! command -v python3 &> /dev/null; then
    echo "خطأ: Python 3 غير مثبت"
    echo "الرجاء تثبيت Python 3.8 او اعلى"
    exit 1
fi

echo "1. انشاء البيئة الافتراضية..."
python3 -m venv venv

echo "2. تفعيل البيئة الافتراضية..."
source venv/bin/activate

echo "3. تثبيت المكتبات..."
pip install --upgrade pip
pip install -r requirements.txt

echo "4. اعداد ملف .env..."
if [ ! -f .env ]; then
    cp .env.template .env
    echo "تم انشاء ملف .env - الرجاء تعديله بالبيانات الصحيحة"
else
    echo "ملف .env موجود بالفعل"
fi

echo "5. انشاء مجلد البيانات..."
mkdir -p data

echo "6. تهيئة قاعدة البيانات..."
python init_db.py

echo ""
echo "=========================================="
echo "تم الاعداد بنجاح!"
echo "=========================================="
echo ""
echo "الخطوات التالية:"
echo "1. عدل ملف .env بالبيانات الصحيحة"
echo "2. لتشغيل البوت في بيئة التطوير:"
echo "   python app.py"
echo "3. لتشغيل البوت في بيئة الانتاج:"
echo "   gunicorn app:app --workers 4 --bind 0.0.0.0:5000"
echo ""
