#!/bin/bash

# 🐋 بوت الحوت - سكريبت تنظيم المشروع التلقائي
# يقوم بنقل الملفات إلى الهيكل الجديد

echo "================================"
echo "🐋 بوت الحوت - Project Organizer"
echo "================================"
echo ""

# ألوان للطباعة
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# وظيفة طباعة ملونة
print_success() { echo -e "${GREEN}✅ $1${NC}"; }
print_error() { echo -e "${RED}❌ $1${NC}"; }
print_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
print_info() { echo -e "${BLUE}ℹ️  $1${NC}"; }

# التحقق من وجود الملفات الأساسية
echo "🔍 التحقق من الملفات..."
required_files=("app.py" "config.py" "utils.py")
missing=0

for file in "${required_files[@]}"; do
    if [ -f "$file" ]; then
        print_success "$file موجود"
    else
        print_error "$file مفقود!"
        missing=$((missing + 1))
    fi
done

if [ $missing -gt 0 ]; then
    print_error "بعض الملفات الأساسية مفقودة!"
    exit 1
fi

echo ""
print_info "بدء تنظيم المشروع..."
echo ""

# ========== إنشاء المجلدات ==========
echo "📁 إنشاء المجلدات..."

if [ ! -d "games" ]; then
    mkdir games
    print_success "تم إنشاء مجلد games/"
else
    print_warning "مجلد games/ موجود مسبقاً"
fi

if [ ! -d "data" ]; then
    mkdir data
    print_success "تم إنشاء مجلد data/"
else
    print_warning "مجلد data/ موجود مسبقاً"
fi

echo ""

# ========== نقل ملفات الألعاب ==========
echo "🎮 نقل ملفات الألعاب..."

game_files=(
    "game_opposite.py"
    "game_song.py"
    "game_chain.py"
    "game_order.py"
    "game_build.py"
    "game_lbgame.py"
    "game_fast.py"
    "game_compatibility.py"
)

moved_games=0
for file in "${game_files[@]}"; do
    if [ -f "$file" ]; then
        if [ ! -f "games/$file" ]; then
            mv "$file" "games/"
            print_success "تم نقل $file"
            moved_games=$((moved_games + 1))
        else
            print_warning "$file موجود بالفعل في games/"
        fi
    else
        print_warning "$file غير موجود في المجلد الحالي"
    fi
done

echo ""

# ========== نقل ملفات البيانات ==========
echo "📄 نقل ملفات البيانات..."

data_files=(
    "mentions.txt"
    "questions.txt"
    "challenges.txt"
    "confessions.txt"
)

moved_data=0
for file in "${data_files[@]}"; do
    if [ -f "$file" ]; then
        if [ ! -f "data/$file" ]; then
            mv "$file" "data/"
            print_success "تم نقل $file"
            moved_data=$((moved_data + 1))
        else
            print_warning "$file موجود بالفعل في data/"
        fi
    else
        print_warning "$file غير موجود (سيتم إنشاؤه لاحقاً)"
    fi
done

echo ""

# ========== إنشاء games/__init__.py ==========
if [ ! -f "games/__init__.py" ]; then
    echo "📝 إنشاء games/__init__.py..."
    cat > games/__init__.py << 'EOF'
"""
مجلد الألعاب - Whale Bot Games Package
"""

from .game_opposite import OppositeGame
from .game_song import SongGame
from .game_chain import ChainWordsGame
from .game_order import OrderGame
from .game_build import BuildGame
from .game_lbgame import LBGame
from .game_fast import FastGame
from .game_compatibility import CompatibilityGame

__all__ = [
    'OppositeGame',
    'SongGame',
    'ChainWordsGame',
    'OrderGame',
    'BuildGame',
    'LBGame',
    'FastGame',
    'CompatibilityGame'
]

GAME_CLASSES = {
    'ضد': OppositeGame,
    'اغنية': SongGame,
    'سلسلة': ChainWordsGame,
    'ترتيب': OrderGame,
    'تكوين': BuildGame,
    'لعبة': LBGame,
    'اسرع': FastGame,
    'توافق': CompatibilityGame
}
EOF
    print_success "تم إنشاء games/__init__.py"
else
    print_warning "games/__init__.py موجود بالفعل"
fi

echo ""

# ========== إنشاء .gitignore ==========
if [ ! -f ".gitignore" ]; then
    echo "📝 إنشاء .gitignore..."
    cat > .gitignore << 'EOF'
# Python
__pycache__/
*.py[cod]
*.so
.Python
venv/
env/

# Environment
.env
.env.local

# Database
*.db
*.sqlite3

# Logs
*.log

# IDE
.vscode/
.idea/
.DS_Store

# Keep data files
!data/*.txt
EOF
    print_success "تم إنشاء .gitignore"
else
    print_warning ".gitignore موجود بالفعل"
fi

echo ""

# ========== ملخص ==========
echo "================================"
echo "📊 ملخص العملية"
echo "================================"
echo ""
print_info "تم نقل $moved_games من ملفات الألعاب"
print_info "تم نقل $moved_data من ملفات البيانات"
echo ""

# ========== التحقق النهائي ==========
echo "🔍 التحقق من الهيكل الجديد..."
echo ""

if [ -d "games" ] && [ -f "games/__init__.py" ]; then
    print_success "مجلد games/ جاهز"
else
    print_error "مشكلة في مجلد games/"
fi

if [ -d "data" ]; then
    print_success "مجلد data/ جاهز"
else
    print_error "مشكلة في مجلد data/"
fi

echo ""

# ========== الخطوات التالية ==========
echo "================================"
echo "📌 الخطوات التالية"
echo "================================"
echo ""
echo "1. تأكد من وجود ملفات الألعاب في games/"
echo "   ls games/"
echo ""
echo "2. تأكد من وجود ملفات البيانات في data/"
echo "   ls data/"
echo ""
echo "3. حدّث المسارات في config.py:"
echo "   MENTIONS_FILE = 'data/mentions.txt'"
echo "   QUESTIONS_FILE = 'data/questions.txt'"
echo ""
echo "4. اختبر الاستيراد:"
echo "   python3 -c 'from games import GAME_CLASSES; print(GAME_CLASSES.keys())'"
echo ""
echo "5. شغّل البوت:"
echo "   python3 app.py"
echo ""

print_success "تم تنظيم المشروع بنجاح! 🎉"
echo ""
