#!/bin/bash

# 🐋 بوت الحوت - سكريبت التثبيت السريع

echo "================================"
echo "🐋 بوت الحوت - Setup Script"
echo "================================"
echo ""

# التحقق من Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 غير مثبت!"
    exit 1
fi

echo "✅ Python version: $(python3 --version)"
echo ""

# إنشاء بيئة افتراضية
echo "📦 إنشاء بيئة افتراضية..."
python3 -m venv venv
source venv/bin/activate

# تثبيت المكتبات
echo "📥 تثبيت المكتبات..."
pip install --upgrade pip
pip install Flask==3.0.0 line-bot-sdk==3.5.0 requests==2.31.0 python-dotenv==1.0.0 gunicorn==21.2.0

# إنشاء ملف .env إذا لم يكن موجوداً
if [ ! -f .env ]; then
    echo "📝 إنشاء ملف .env..."
    cat > .env << 'EOF'
LINE_CHANNEL_ACCESS_TOKEN=your_token_here
LINE_CHANNEL_SECRET=your_secret_here
PORT=5000
EOF
    echo "⚠️  تحذير: عدّل ملف .env وأضف التوكنات الصحيحة!"
fi

# التحقق من الملفات المطلوبة
echo ""
echo "🔍 التحقق من الملفات..."

files=("app.py" "games.py" "config.py" "requirements.txt")
missing=0

for file in "${files[@]}"; do
    if [ -f "$file" ]; then
        echo "  ✅ $file"
    else
        echo "  ❌ $file (مفقود!)"
        missing=$((missing + 1))
    fi
done

echo ""

if [ $missing -gt 0 ]; then
    echo "❌ هناك $missing ملف مفقود!"
    echo "⚠️  انسخ الملفات من artifacts أولاً"
    exit 1
fi

# إنشاء .gitignore
if [ ! -f .gitignore ]; then
    echo "📝 إنشاء .gitignore..."
    cat > .gitignore << 'EOF'
.env
*.db
__pycache__/
*.pyc
.DS_Store
venv/
*.log
EOF
fi

# اختبار الاستيراد
echo "🧪 اختبار الملفات..."
python3 -c "import app; import games; import config" 2>/dev/null

if [ $? -eq 0 ]; then
    echo "  ✅ جميع الملفات تعمل بشكل صحيح"
else
    echo "  ❌ هناك خطأ في الملفات"
    echo "  🔍 تحقق من syntax errors"
fi

echo ""
echo "================================"
echo "✅ التثبيت اكتمل بنجاح!"
echo "================================"
echo ""
echo "📌 الخطوات التالية:"
echo ""
echo "1. عدّل ملف .env وأضف توكنات LINE"
echo "2. شغّل البوت: python3 app.py"
echo "3. افتح المتصفح: http://localhost:5000"
echo ""
echo "🚀 للنشر على Render:"
echo "   git init"
echo "   git add ."
echo "   git commit -m 'Initial commit'"
echo "   git remote add origin YOUR_REPO_URL"
echo "   git push -u origin main"
echo ""
echo "🐋 حظ موفق!"
echo ""
