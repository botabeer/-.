#!/bin/bash

echo "🎮 إعداد LINE Bot للألعاب"
echo "=============================="
echo ""

# فحص Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 غير مثبت. قم بتثبيته أولاً."
    exit 1
fi

echo "✅ Python موجود"
echo ""

# إنشاء البيئة الافتراضية
echo "📦 إنشاء البيئة الافتراضية..."
python3 -m venv venv

# تفعيل البيئة
echo "🔧 تفعيل البيئة..."
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    source venv/Scripts/activate
else
    source venv/bin/activate
fi

# تثبيت المكتبات
echo "📥 تثبيت المكتبات..."
pip install --upgrade pip
pip install -r requirements.txt

# إنشاء مجلد الألعاب
echo "📁 إنشاء مجلد الألعاب..."
mkdir -p games
touch games/__init__.py

# نسخ ملف البيئة
if [ ! -f .env ]; then
    echo "📝 إنشاء ملف .env..."
    cp .env.example .env
    echo "⚠️  تذكر: عدّل ملف .env وأضف مفاتيحك!"
else
    echo "✅ ملف .env موجود بالفعل"
fi

# إنشاء .gitignore
echo "🔒 إنشاء .gitignore..."
cat > .gitignore << 'EOF'
__pycache__/
*.py[cod]
venv/
.env
*.db
*.sqlite
.DS_Store
EOF

echo ""
echo "✅ تم الإعداد بنجاح!"
echo ""
echo "الخطوات التالية:"
echo "1. عدّل ملف .env وأضف مفاتيح LINE"
echo "2. أضف ملفات الألعاب في مجلد games/"
echo "3. شغل البوت: python app.py"
echo ""
