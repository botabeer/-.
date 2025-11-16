#!/bin/bash

# ═══════════════════════════════════════════════════════════════
#  بوت الحوت - سكريبت التثبيت السريع
# ═══════════════════════════════════════════════════════════════

echo "═══════════════════════════════════════════════════════════════"
echo " بوت الحوت - نظام ألعاب تفاعلية"
echo "═══════════════════════════════════════════════════════════════"
echo ""

# التحقق من Python
echo "📋 التحقق من المتطلبات..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 غير مثبت. يرجى تثبيته أولاً."
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d ' ' -f 2)
echo "✅ Python $PYTHON_VERSION"

# إنشاء المجلدات
echo ""
echo "📁 إنشاء البنية..."
mkdir -p config database cache utils ai ui managers handlers games

# إنشاء ملفات __init__.py
echo "📝 إنشاء ملفات __init__.py..."

# config/__init__.py
cat > config/__init__.py << 'EOF'
"""استيراد الإعدادات"""
from .config import config, BotConfig, THEME, NO_POINTS_GAMES

__all__ = ['config', 'BotConfig', 'THEME', 'NO_POINTS_GAMES']
EOF

# database/__init__.py
cat > database/__init__.py << 'EOF'
"""استيراد قاعدة البيانات"""
from .database import db_manager, DatabaseException, DatabaseManager

__all__ = ['db_manager', 'DatabaseException', 'DatabaseManager']
EOF

# cache/__init__.py
cat > cache/__init__.py << 'EOF'
"""استيراد الذاكرة المؤقتة"""
from .cache import names_cache, stats_cache, leaderboard_cache, CacheManager

__all__ = ['names_cache', 'stats_cache', 'leaderboard_cache', 'CacheManager']
EOF

# utils/__init__.py
cat > utils/__init__.py << 'EOF'
"""استيراد الدوال المساعدة"""
from .utils import safe_text, normalize_text, load_file, get_profile_safe, check_rate

__all__ = ['safe_text', 'normalize_text', 'load_file', 'get_profile_safe', 'check_rate']
EOF

# ai/__init__.py
cat > ai/__init__.py << 'EOF'
"""استيراد الذكاء الاصطناعي"""
from .gemini_ai import USE_AI, ask_gemini

__all__ = ['USE_AI', 'ask_gemini']
EOF

# ui/__init__.py
cat > ui/__init__.py << 'EOF'
"""استيراد واجهة المستخدم"""
from .cards import (
    get_quick_reply, create_card, create_button,
    get_welcome_card, get_help_card, get_registration_card,
    get_withdrawal_card, get_stats_card, get_leaderboard_card
)

__all__ = [
    'get_quick_reply', 'create_card', 'create_button',
    'get_welcome_card', 'get_help_card', 'get_registration_card',
    'get_withdrawal_card', 'get_stats_card', 'get_leaderboard_card'
]
EOF

# managers/__init__.py
cat > managers/__init__.py << 'EOF'
"""استيراد المديرين"""
from .user_manager import UserManager
from .game_manager import GameManager
from .cleanup_manager import cleanup_manager, CleanupManager

__all__ = ['UserManager', 'GameManager', 'cleanup_manager', 'CleanupManager']
EOF

# handlers/__init__.py
cat > handlers/__init__.py << 'EOF'
"""استيراد معالجات الأحداث"""
from .message_handler import handle_text_message

__all__ = ['handle_text_message']
EOF

echo "✅ تم إنشاء جميع ملفات __init__.py"

# إنشاء requirements.txt
echo ""
echo "📦 إنشاء requirements.txt..."
cat > requirements.txt << 'EOF'
Flask==3.0.0
line-bot-sdk==3.7.0
google-generativeai==0.3.2
EOF

echo "✅ تم إنشاء requirements.txt"

# إنشاء .env.example
echo ""
echo "🔐 إنشاء .env.example..."
cat > .env.example << 'EOF'
# LINE Bot Configuration
LINE_CHANNEL_ACCESS_TOKEN=your_line_channel_access_token_here
LINE_CHANNEL_SECRET=your_line_channel_secret_here

# Gemini AI Configuration (اختياري)
GEMINI_API_KEY_1=your_gemini_api_key_1_here
GEMINI_API_KEY_2=your_gemini_api_key_2_here

# Admin Token (اختياري)
ADMIN_TOKEN=your_secure_admin_token_here

# Server Configuration
PORT=5000
EOF

echo "✅ تم إنشاء .env.example"

# إنشاء .gitignore
echo ""
echo "🚫 إنشاء .gitignore..."
cat > .gitignore << 'EOF'
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
env/
ENV/

# Database
*.db
*.db-shm
*.db-wal

# Logs
*.log
bot.log

# Environment
.env
.env.local

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Distribution
build/
dist/
*.egg-info/
EOF

echo "✅ تم إنشاء .gitignore"

# إنشاء ملفات الألعاب الفارغة
echo ""
echo "🎮 إنشاء ملفات الألعاب..."
touch games/questions.txt
touch games/challenges.txt
touch games/confessions.txt
touch games/more_questions.txt

echo "✅ تم إنشاء ملفات الألعاب"

# إنشاء البيئة الافتراضية
echo ""
echo "🐍 إنشاء البيئة الافتراضية..."
if python3 -m venv venv; then
    echo "✅ تم إنشاء البيئة الافتراضية"
else
    echo "⚠️ فشل إنشاء البيئة الافتراضية"
fi

# تفعيل البيئة وتثبيت المكتبات
echo ""
echo "📦 تثبيت المكتبات..."
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
    echo "✅ تم تثبيت المكتبات"
else
    echo "⚠️ يرجى تفعيل البيئة الافتراضية يدوياً"
fi

# إنشاء README.md
echo ""
echo "📄 إنشاء README.md..."
cat > README.md << 'EOF'
# 🐋 بوت الحوت - نظام ألعاب تفاعلية

## 🚀 التثبيت السريع

### 1. نسخ .env
```bash
cp .env.example .env
nano .env  # أضف مفاتيح LINE و Gemini
```

### 2. تفعيل البيئة
```bash
# Linux/Mac
source venv/bin/activate

# Windows
venv\Scripts\activate
```

### 3. التشغيل
```bash
python app.py
```

## 📋 البنية

```
whale-bot/
├── app.py
├── config/
├── database/
├── cache/
├── utils/
├── ai/
├── ui/
├── managers/
├── handlers/
└── games/
```

## 🎮 الألعاب

- أغنية، لعبة، سلسلة، أسرع
- ضد، تكوين، اختلاف، توافق

## 📝 الأوامر

- `انضم` - التسجيل
- `نقاطي` - الإحصائيات
- `الصدارة` - المتصدرين
- `إيقاف` - إنهاء اللعبة

## 📞 الدعم

للمساعدة، راجع التوثيق الكامل.
EOF

echo "✅ تم إنشاء README.md"

# عرض الملخص
echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "✅ اكتمل التثبيت بنجاح!"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "📁 البنية المُنشأة:"
echo "   ✅ config/"
echo "   ✅ database/"
echo "   ✅ cache/"
echo "   ✅ utils/"
echo "   ✅ ai/"
echo "   ✅ ui/"
echo "   ✅ managers/"
echo "   ✅ handlers/"
echo "   ✅ games/"
echo ""
echo "📋 الخطوات التالية:"
echo ""
echo "1️⃣  انسخ ملفات الكود من الأرتيفاكت إلى المجلدات المناسبة"
echo ""
echo "2️⃣  قم بإعداد ملف .env:"
echo "   cp .env.example .env"
echo "   nano .env"
echo ""
echo "3️⃣  فعّل البيئة الافتراضية:"
echo "   source venv/bin/activate  # Linux/Mac"
echo "   venv\\Scripts\\activate    # Windows"
echo ""
echo "4️⃣  شغّل البوت:"
echo "   python app.py"
echo ""
echo "═══════════════════════════════════════════════════════════════"
echo " بوت الحوت © 2025"
echo "═══════════════════════════════════════════════════════════════"
