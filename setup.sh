#!/bin/bash
# ============================================
# setup.sh - سكريبت التثبيت والإعداد
# ============================================

echo "=================================="
echo "إعداد بوت الحوت"
echo "=================================="
echo ""

# التحقق من Python
echo "1. التحقق من Python..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 غير مثبت. يرجى تثبيته أولاً."
    exit 1
fi
echo "✓ Python 3 مثبت"
python3 --version
echo ""

# إنشاء البيئة الافتراضية
echo "2. إنشاء البيئة الافتراضية..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✓ تم إنشاء البيئة الافتراضية"
else
    echo "✓ البيئة الافتراضية موجودة بالفعل"
fi
echo ""

# تفعيل البيئة الافتراضية
echo "3. تفعيل البيئة الافتراضية..."
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
    echo "✓ تم تفعيل البيئة الافتراضية"
elif [ -f "venv/Scripts/activate" ]; then
    source venv/Scripts/activate
    echo "✓ تم تفعيل البيئة الافتراضية"
else
    echo "❌ فشل تفعيل البيئة الافتراضية"
    exit 1
fi
echo ""

# تحديث pip
echo "4. تحديث pip..."
pip install --upgrade pip
echo "✓ تم تحديث pip"
echo ""

# تثبيت المكتبات
echo "5. تثبيت المكتبات من requirements.txt..."
pip install -r requirements.txt
if [ $? -eq 0 ]; then
    echo "✓ تم تثبيت جميع المكتبات بنجاح"
else
    echo "❌ فشل تثبيت المكتبات"
    exit 1
fi
echo ""

# إنشاء ملف .env
echo "6. إعداد ملف البيئة..."
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo "✓ تم إنشاء ملف .env من .env.example"
        echo "⚠️  يرجى تحديث ملف .env بتوكناتك الحقيقية"
    else
        echo "❌ ملف .env.example غير موجود"
    fi
else
    echo "✓ ملف .env موجود بالفعل"
fi
echo ""

# إنشاء قاعدة البيانات
echo "7. إنشاء قاعدة البيانات..."
python init_db.py
if [ $? -eq 0 ]; then
    echo "✓ تم إنشاء قاعدة البيانات بنجاح"
else
    echo "❌ فشل إنشاء قاعدة البيانات"
    exit 1
fi
echo ""

# إنشاء مجلد data إذا لم يكن موجوداً
echo "8. التحقق من مجلد البيانات..."
if [ ! -d "data" ]; then
    mkdir data
    echo "✓ تم إنشاء مجلد data"
    
    # إنشاء ملفات بيانات فارغة
    touch data/challenges.txt
    touch data/confessions.txt
    touch data/mentions.txt
    touch data/questions.txt
    echo "✓ تم إنشاء ملفات البيانات"
else
    echo "✓ مجلد data موجود"
fi
echo ""

# التحقق من الهيكل
echo "9. التحقق من هيكل المشروع..."
REQUIRED_DIRS=("games" "data")
REQUIRED_FILES=("app.py" "rules.py" "style.py" "config.py" "utils.py" "init_db.py")

all_good=true

for dir in "${REQUIRED_DIRS[@]}"; do
    if [ -d "$dir" ]; then
        echo "✓ $dir/"
    else
        echo "❌ $dir/ مفقود"
        all_good=false
    fi
done

for file in "${REQUIRED_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "✓ $file"
    else
        echo "❌ $file مفقود"
        all_good=false
    fi
done
echo ""

if [ "$all_good" = true ]; then
    echo "=================================="
    echo "✓ اكتمل الإعداد بنجاح!"
    echo "=================================="
    echo ""
    echo "الخطوات التالية:"
    echo "1. حدث ملف .env بتوكنات LINE الخاصة بك"
    echo "2. أضف محتوى إلى ملفات data/"
    echo "3. شغل البوت: python app.py"
    echo ""
    echo "لتشغيل البوت محلياً:"
    echo "  python app.py"
    echo ""
    echo "لتشغيل البوت في بيئة الإنتاج:"
    echo "  gunicorn app:app"
    echo ""
else
    echo "=================================="
    echo "❌ الإعداد غير مكتمل"
    echo "=================================="
    echo "يرجى التحقق من الملفات المفقودة"
    exit 1
fi
