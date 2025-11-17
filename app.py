"""
بوت الحوت - نظام ألعاب تفاعلي احترافي
الإصدار: 3.0.0
التصميم: 3D Experience - رمادي داكن مع توهجات أزرق/سماوي
"""

from flask import Flask, request, abort, jsonify
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError, LineBotApiError
from linebot.models import (
    MessageEvent, TextMessage, FlexSendMessage,
    QuickReply, QuickReplyButton, MessageAction
)
import os
import sys
import logging
import json
from datetime import datetime, timedelta
from functools import wraps
from collections import defaultdict
from threading import Lock, Thread
import time
import random

# ═══════════════════════════════════════════════════════════════
# إعداد Logging المتقدم
# ═══════════════════════════════════════════════════════════════
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('whale_bot.log', encoding='utf-8')
    ]
)
logger = logging.getLogger("whale-bot")

# ═══════════════════════════════════════════════════════════════
# تحميل الإعدادات
# ═══════════════════════════════════════════════════════════════
LINE_TOKEN = os.getenv('LINE_CHANNEL_ACCESS_TOKEN', '')
LINE_SECRET = os.getenv('LINE_CHANNEL_SECRET', '')
ADMIN_TOKEN = os.getenv('ADMIN_TOKEN', 'admin_whale_2025')

# مفاتيح Gemini للذكاء الاصطناعي
GEMINI_KEYS = [
    os.getenv('GEMINI_API_KEY_1', ''),
    os.getenv('GEMINI_API_KEY_2', ''),
    os.getenv('GEMINI_API_KEY_3', '')
]
GEMINI_KEYS = [k for k in GEMINI_KEYS if k]

if not LINE_TOKEN or not LINE_SECRET:
    logger.critical("❌ فشل في تحميل إعدادات LINE")
    sys.exit(1)

# ═══════════════════════════════════════════════════════════════
# الثوابت والإعدادات
# ═══════════════════════════════════════════════════════════════
VERSION = "3.0.0"
BOT_NAME = "بوت الحوت"
CLEANUP_DAYS = 45  # حذف المستخدمين غير النشطين بعد 45 يوم
MAX_MESSAGES_PER_MINUTE = 10  # حماية من السبام

# ألوان 3D Experience - رمادي داكن مع توهجات أزرق/سماوي
COLORS = {
    'bg': '#0F172A',           # خلفية داكنة جداً
    'card': '#1E293B',         # بطاقات رمادية داكنة
    'card2': '#334155',        # بطاقات أفتح قليلاً
    'card3': '#475569',        # بطاقات أفتح للتباين
    'text': '#F1F5F9',         # نص أبيض مائل للرمادي
    'text2': '#94A3B8',        # نص رمادي فاتح
    'text3': '#64748B',        # نص رمادي أغمق
    'sep': '#475569',          # خطوط فاصلة
    'btn': '#3B82F6',          # أزرار زرقاء
    'btn_hover': '#2563EB',    # أزرار عند التحويم
    'gradient1': '#06B6D4',    # سماوي (Cyan)
    'gradient2': '#0EA5E9',    # أزرق فاتح
    'gradient3': '#3B82F6',    # أزرق
    'success': '#10B981',      # أخضر للنجاح
    'warning': '#F59E0B',      # برتقالي للتحذير
    'error': '#EF4444',        # أحمر للخطأ
    'glow': '#0EA5E980',       # توهج أزرق شفاف
    'shadow': '#00000080',     # ظل أسود شفاف
}

# الأوامر المقبولة فقط
VALID_COMMANDS = {
    'البداية', 'مساعدة', 'انضم', 'انسحب', 'نقاطي', 'الصدارة',
    'أغنية', 'لعبة', 'سلسلة', 'أسرع', 'ضد', 'تكوين', 'اختلاف', 'توافق',
    'سؤال', 'سوال', 'تحدي', 'اعتراف', 'منشن',
    'لمح', 'جاوب', 'ايقاف', 'اعادة', 'الحل'
}

# ═══════════════════════════════════════════════════════════════
# تهيئة Flask و LINE Bot
# ═══════════════════════════════════════════════════════════════
app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False
app.config['JSON_SORT_KEYS'] = False

line_bot_api = LineBotApi(LINE_TOKEN)
handler = WebhookHandler(LINE_SECRET)

# ═══════════════════════════════════════════════════════════════
# قاعدة البيانات البسيطة (في الذاكرة + ملف JSON)
# ═══════════════════════════════════════════════════════════════
DB_FILE = 'whale_bot_db.json'
db_lock = Lock()

def load_db():
    """تحميل قاعدة البيانات"""
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass
    return {
        'users': {},      # {user_id: {name, points, last_active, games_played}}
        'games': {},      # {room_id: {game_type, data, players, started_at}}
        'questions_used': [], # أسئلة مستخدمة لتجنب التكرار
        'stats': {'total_games': 0, 'total_players': 0}
    }

def save_db(data):
    """حفظ قاعدة البيانات"""
    with db_lock:
        try:
            with open(DB_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            logger.error(f"❌ خطأ في حفظ DB: {e}")
            return False

db = load_db()
logger.info(f"✅ تم تحميل DB: {len(db['users'])} مستخدم، {len(db['games'])} لعبة نشطة")

# ═══════════════════════════════════════════════════════════════
# Cache للأداء
# ═══════════════════════════════════════════════════════════════
names_cache = {}  # {user_id: name}
rate_limit_cache = defaultdict(lambda: {'count': 0, 'reset_at': datetime.now()})

# ═══════════════════════════════════════════════════════════════
# تحميل المحتوى
# ═══════════════════════════════════════════════════════════════
def load_content(filename):
    """تحميل محتوى من ملف"""
    try:
        path = os.path.join('content', filename)
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                lines = [line.strip() for line in f if line.strip()]
                return lines
        logger.warning(f"⚠️ ملف {filename} غير موجود")
        return []
    except Exception as e:
        logger.error(f"❌ خطأ في تحميل {filename}: {e}")
        return []

QUESTIONS = load_content('questions.txt')
CHALLENGES = load_content('challenges.txt')
CONFESSIONS = load_content('confessions.txt')
MENTIONS = load_content('mentions.txt')

if not QUESTIONS:
    QUESTIONS = ["ما هو أكثر شيء تحبه في الحياة؟"] * 50
if not CHALLENGES:
    CHALLENGES = ["تحدى نفسك وأرسل رسالة لأقرب شخص لك"] * 50
if not CONFESSIONS:
    CONFESSIONS = ["اعترف بشيء لم تخبر به أحداً من قبل"] * 50
if not MENTIONS:
    MENTIONS = ["منشن شخص تحب التحدث معه دائماً"] * 50

logger.info(f"📚 المحتوى: {len(QUESTIONS)} سؤال، {len(CHALLENGES)} تحدي، {len(CONFESSIONS)} اعتراف، {len(MENTIONS)} منشن")

# ═══════════════════════════════════════════════════════════════
# دوال مساعدة
# ═══════════════════════════════════════════════════════════════
def is_valid_command(text):
    """التحقق من أن الرسالة أمر صالح"""
    if not text:
        return False
    text = text.strip()
    # تحقق من الأوامر الأساسية
    for cmd in VALID_COMMANDS:
        if text.startswith(cmd) or text == cmd:
            return True
    return False

def get_user_name(user_id):
    """الحصول على اسم المستخدم من Cache أو LINE"""
    if user_id in names_cache:
        return names_cache[user_id]
    
    try:
        profile = line_bot_api.get_profile(user_id)
        name = profile.display_name
        names_cache[user_id] = name
        return name
    except LineBotApiError as e:
        if e.status_code == 404:
            # المستخدم لم يضف البوت بعد
            pass
        else:
            logger.warning(f"⚠️ فشل في جلب اسم {user_id}: {e}")
    except Exception as e:
        logger.error(f"❌ خطأ في get_user_name: {e}")
    
    return "لاعب"

def check_rate_limit(user_id):
    """التحقق من معدل الرسائل (حماية من السبام)"""
    now = datetime.now()
    user_data = rate_limit_cache[user_id]
    
    # إعادة تعيين إذا مر دقيقة
    if now > user_data['reset_at']:
        user_data['count'] = 0
        user_data['reset_at'] = now + timedelta(minutes=1)
    
    user_data['count'] += 1
    return user_data['count'] <= MAX_MESSAGES_PER_MINUTE

def get_or_create_user(user_id):
    """الحصول على المستخدم أو إنشاؤه"""
    if user_id not in db['users']:
        name = get_user_name(user_id)
        db['users'][user_id] = {
            'name': name,
            'points': 0,
            'last_active': datetime.now().isoformat(),
            'games_played': 0,
            'registered': False
        }
        save_db(db)
        logger.info(f"➕ مستخدم جديد: {name} ({user_id})")
    else:
        # تحديث آخر نشاط
        db['users'][user_id]['last_active'] = datetime.now().isoformat()
        # تحديث الاسم إذا تغير
        new_name = get_user_name(user_id)
        if new_name != db['users'][user_id]['name']:
            db['users'][user_id]['name'] = new_name
            save_db(db)
    
    return db['users'][user_id]

def update_user_points(user_id, points_change):
    """تحديث نقاط المستخدم"""
    user = get_or_create_user(user_id)
    user['points'] = max(0, user['points'] + points_change)
    save_db(db)
    return user['points']

def get_random_unused(items_list, used_key):
    """اختيار عنصر عشوائي لم يُستخدم مؤخراً"""
    if not items_list:
        return None
    
    used = set(db.get(used_key, []))
    available = [item for item in items_list if item not in used]
    
    # إذا استُخدمت كل العناصر، نعيد تعيين القائمة
    if not available:
        db[used_key] = []
        available = items_list
    
    selected = random.choice(available)
    
    # حفظ العنصر المستخدم
    if used_key not in db:
        db[used_key] = []
    db[used_key].append(selected)
    
    # إبقاء آخر 50% فقط من العناصر المستخدمة
    if len(db[used_key]) > len(items_list) // 2:
        db[used_key] = db[used_key][-(len(items_list) // 2):]
    
    save_db(db)
    return selected

# ═══════════════════════════════════════════════════════════════
# بطاقات Flex - تصميم 3D Experience
# ═══════════════════════════════════════════════════════════════
def create_flex_bubble(title, content_items, footer_buttons=None, color=COLORS['gradient1']):
    """إنشاء بطاقة Flex بتصميم 3D"""
    
    contents = {
        "type": "box",
        "layout": "vertical",
        "contents": [
            {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "text",
                        "text": title,
                        "weight": "bold",
                        "size": "xl",
                        "color": COLORS['text'],
                        "wrap": True
                    }
                ],
                "paddingAll": "20px",
                "backgroundColor": COLORS['card']
            },
            {
                "type": "separator",
                "color": COLORS['sep']
            },
            {
                "type": "box",
                "layout": "vertical",
                "contents": content_items,
                "paddingAll": "20px",
                "spacing": "md",
                "backgroundColor": COLORS['card2']
            }
        ],
        "paddingAll": "0px"
    }
    
    if footer_buttons:
        contents["contents"].extend([
            {
                "type": "separator",
                "color": COLORS['sep']
            },
            {
                "type": "box",
                "layout": "vertical",
                "contents": footer_buttons,
                "spacing": "sm",
                "paddingAll": "16px",
                "backgroundColor": COLORS['card']
            }
        ])
    
    return {
        "type": "bubble",
        "size": "kilo",
        "body": contents
    }

def get_welcome_flex():
    """بطاقة الترحيب"""
    content = [
        {
            "type": "text",
            "text": "مرحباً بك في بوت الحوت",
            "size": "lg",
            "weight": "bold",
            "color": COLORS['text']
        },
        {
            "type": "text",
            "text": "بوت ألعاب تفاعلي ذكي للمجموعات",
            "size": "sm",
            "color": COLORS['text2'],
            "margin": "sm"
        },
        {
            "type": "separator",
            "margin": "xl",
            "color": COLORS['sep']
        },
        {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {"type": "text", "text": "▫️ 8 ألعاب ممتعة", "size": "sm", "color": COLORS['text']},
                {"type": "text", "text": "▫️ نظام نقاط ذكي", "size": "sm", "color": COLORS['text'], "margin": "sm"},
                {"type": "text", "text": "▫️ لوحة صدارة تفاعلية", "size": "sm", "color": COLORS['text'], "margin": "sm"},
                {"type": "text", "text": "▫️ تصميم 3D أنيق", "size": "sm", "color": COLORS['text'], "margin": "sm"}
            ],
            "margin": "xl"
        },
        {
            "type": "text",
            "text": "© 2025 بوت الحوت",
            "size": "xxs",
            "color": COLORS['text2'],
            "align": "center",
            "margin": "xl"
        }
    ]
    
    buttons = [
        {
            "type": "button",
            "action": {"type": "message", "label": "▫️ مساعدة", "text": "مساعدة"},
            "style": "primary",
            "color": COLORS['btn'],
            "height": "sm"
        },
        {
            "type": "button",
            "action": {"type": "message", "label": "▫️ انضم", "text": "انضم"},
            "style": "secondary",
            "height": "sm"
        }
    ]
    
    return create_flex_bubble("البداية", content, buttons, COLORS['gradient1'])

def get_help_flex():
    """بطاقة المساعدة"""
    content = [
        {
            "type": "text",
            "text": "الأوامر الأساسية",
            "weight": "bold",
            "size": "md",
            "color": COLORS['text']
        },
        {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {"type": "text", "text": "▫️ انضم - التسجيل في النظام", "size": "sm", "color": COLORS['text2'], "wrap": True},
                {"type": "text", "text": "▫️ انسحب - إلغاء التسجيل", "size": "sm", "color": COLORS['text2'], "wrap": True, "margin": "sm"},
                {"type": "text", "text": "▫️ نقاطي - عرض نقاطك", "size": "sm", "color": COLORS['text2'], "wrap": True, "margin": "sm"},
                {"type": "text", "text": "▫️ الصدارة - أفضل اللاعبين", "size": "sm", "color": COLORS['text2'], "wrap": True, "margin": "sm"},
                {"type": "text", "text": "▫️ ايقاف - إيقاف اللعبة", "size": "sm", "color": COLORS['text2'], "wrap": True, "margin": "sm"}
            ],
            "margin": "md"
        },
        {
            "type": "separator",
            "margin": "xl",
            "color": COLORS['sep']
        },
        {
            "type": "text",
            "text": "الألعاب المتاحة",
            "weight": "bold",
            "size": "md",
            "color": COLORS['text'],
            "margin": "xl"
        },
        {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {"type": "text", "text": "▫️ أغنية - خمن المغني", "size": "sm", "color": COLORS['text2']},
                {"type": "text", "text": "▫️ لعبة - إنسان حيوان نبات", "size": "sm", "color": COLORS['text2'], "margin": "sm"},
                {"type": "text", "text": "▫️ سلسلة - سلسلة الحروف", "size": "sm", "color": COLORS['text2'], "margin": "sm"},
                {"type": "text", "text": "▫️ أسرع - أسرع إجابة", "size": "sm", "color": COLORS['text2'], "margin": "sm"},
                {"type": "text", "text": "▫️ ضد - ضد الكلمة", "size": "sm", "color": COLORS['text2'], "margin": "sm"},
                {"type": "text", "text": "▫️ تكوين - تكوين كلمات", "size": "sm", "color": COLORS['text2'], "margin": "sm"}
            ],
            "margin": "md"
        },
        {
            "type": "separator",
            "margin": "xl",
            "color": COLORS['sep']
        },
        {
            "type": "text",
            "text": "ترفيه بدون نقاط",
            "weight": "bold",
            "size": "md",
            "color": COLORS['text'],
            "margin": "xl"
        },
        {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {"type": "text", "text": "▫️ اختلاف - ابحث عن الاختلافات", "size": "sm", "color": COLORS['text2']},
                {"type": "text", "text": "▫️ توافق - قياس التوافق", "size": "sm", "color": COLORS['text2'], "margin": "sm"},
                {"type": "text", "text": "▫️ سؤال - أسئلة عامة", "size": "sm", "color": COLORS['text2'], "margin": "sm"},
                {"type": "text", "text": "▫️ تحدي - تحديات ممتعة", "size": "sm", "color": COLORS['text2'], "margin": "sm"},
                {"type": "text", "text": "▫️ اعتراف - اعترافات", "size": "sm", "color": COLORS['text2'], "margin": "sm"},
                {"type": "text", "text": "▫️ منشن - منشن عشوائي", "size": "sm", "color": COLORS['text2'], "margin": "sm"}
            ],
            "margin": "md"
        }
    ]
    
    buttons = [
        {
            "type": "button",
            "action": {"type": "message", "label": "▫️ نقاطي", "text": "نقاطي"},
            "style": "primary",
            "color": COLORS['success'],
            "height": "sm"
        },
        {
            "type": "button",
            "action": {"type": "message", "label": "▫️ الصدارة", "text": "الصدارة"},
            "style": "secondary",
            "height": "sm"
        }
    ]
    
    return create_flex_bubble("مساعدة", content, buttons, COLORS['gradient1'])

def get_stats_flex(user_id):
    """بطاقة الإحصائيات الشخصية"""
    user = get_or_create_user(user_id)
    
    status = "🥇 مسجل" if user.get('registered', False) else "غير مسجل"
    status_color = COLORS['success'] if user.get('registered', False) else COLORS['text2']
    
    content = [
        {
            "type": "box",
            "layout": "horizontal",
            "contents": [
                {"type": "text", "text": "الاسم", "size": "sm", "color": COLORS['text2'], "flex": 0},
                {"type": "text", "text": user['name'], "size": "sm", "color": COLORS['text'], "align": "end", "weight": "bold"}
            ]
        },
        {
            "type": "box",
            "layout": "horizontal",
            "contents": [
                {"type": "text", "text": "الحالة", "size": "sm", "color": COLORS['text2'], "flex": 0},
                {"type": "text", "text": status, "size": "sm", "color": status_color, "align": "end", "weight": "bold"}
            ],
            "margin": "md"
        },
        {
            "type": "separator",
            "margin": "xl",
            "color": COLORS['sep']
        },
        {
            "type": "box",
            "layout": "horizontal",
            "contents": [
                {"type": "text", "text": "النقاط", "size": "md", "color": COLORS['text2'], "flex": 0},
                {"type": "text", "text": str(user['points']), "size": "xl", "color": COLORS['gradient1'], "align": "end", "weight": "bold"}
            ],
            "margin": "xl"
        },
        {
            "type": "box",
            "layout": "horizontal",
            "contents": [
                {"type": "text", "text": "الألعاب", "size": "sm", "color": COLORS['text2'], "flex": 0},
                {"type": "text", "text": str(user.get('games_played', 0)), "size": "sm", "color": COLORS['text'], "align": "end"}
            ],
            "margin": "md"
        }
    ]
    
    buttons = []
    if not user.get('registered', False):
        buttons.append({
            "type": "button",
            "action": {"type": "message", "label": "▫️ انضم الآن", "text": "انضم"},
            "style": "primary",
            "color": COLORS['success'],
            "height": "sm"
        })
    else:
        buttons.append({
            "type": "button",
            "action": {"type": "message", "label": "▫️ الصدارة", "text": "الصدارة"},
            "style": "primary",
            "color": COLORS['btn'],
            "height": "sm"
        })
    
    return create_flex_bubble("نقاطي", content, buttons, COLORS['gradient1'])

def get_leaderboard_flex():
    """بطاقة لوحة الصدارة"""
    # ترتيب المستخدمين المسجلين حسب النقاط
    registered_users = [(uid, u) for uid, u in db['users'].items() if u.get('registered', False)]
    top_users = sorted(registered_users, key=lambda x: x[1]['points'], reverse=True)[:10]
    
    if not top_users:
        content = [
            {
                "type": "text",
                "text": "لا يوجد لاعبين مسجلين بعد",
                "size": "md",
                "color": COLORS['text2'],
                "align": "center",
                "wrap": True
            }
        ]
    else:
        content = []
        for i, (uid, user) in enumerate(top_users, 1):
            medal = "🏆" if i == 1 else "🥇" if i == 2 else "▫️"
            content.append({
                "type": "box",
                "layout": "horizontal",
                "contents": [
                    {"type": "text", "text": f"{medal} {i}", "size": "sm", "color": COLORS['text2'], "flex": 0},
                    {"type": "text", "text": user['name'], "size": "sm", "color": COLORS['text'], "flex": 2},
                    {"type": "text", "text": str(user['points']), "size": "sm", "color": COLORS['gradient1'], "align": "end", "weight": "bold", "flex": 1}
                ],
                "margin": "md" if i > 1 else "none"
            })
    
    buttons = [
        {
            "type": "button",
            "action": {"type": "message", "label": "▫️ نقاطي", "text": "نقاطي"},
            "style": "primary",
            "color": COLORS['success'],
            "height": "sm"
        }
    ]
    
    return create_flex_bubble("الصدارة", content, buttons, COLORS['gradient1'])

def get_quick_reply_buttons():
    """أزرار الرد السريع الثابتة"""
    return QuickReply(items=[
        QuickReplyButton(action=MessageAction(label="▫️ مساعدة", text="مساعدة")),
        QuickReplyButton(action=MessageAction(label="▫️ نقاطي", text="نقاطي")),
        QuickReplyButton(action=MessageAction(label="▫️ الصدارة", text="الصدارة")),
        QuickReplyButton(action=MessageAction(label="▫️ سؤال", text="سؤال")),
        QuickReplyButton(action=MessageAction(label="▫️ تحدي", text="تحدي")),
        QuickReplyButton(action=MessageAction(label="▫️ اعتراف", text="اعتراف")),
        QuickReplyButton(action=MessageAction(label="▫️ منشن", text="منشن")),
        QuickReplyButton(action=MessageAction(label="▫️ أغنية", text="أغنية")),
        QuickReplyButton(action=MessageAction(label="▫️ لعبة", text="لعبة")),
        QuickReplyButton(action=MessageAction(label="▫️ اختلاف", text="اختلاف")),
        QuickReplyButton(action=MessageAction(label="▫️ توافق", text="توافق"))
    ])

# ═══════════════════════════════════════════════════════════════
# معالجة الرسائل الرئيسية
# ═══════════════════════════════════════════════════════════════
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    """معالجة الرسائل - يستجيب فقط للأوامر"""
    try:
        text = event.message.text.strip()
        user_id = event.source.user_id
        room_id = getattr(event.source, 'group_id', None) or getattr(event.source, 'room_id', None)
        
        # تجاهل الرسائل التي ليست أوامر
        if not is_valid_command(text):
            return
        
        # التحقق من Rate Limit
        if not check_rate_limit(user_id):
            logger.warning(f"⚠️ تجاوز معدل الرسائل: {user_id}")
            return
        
        # تحديث بيانات المستخدم
        user = get_or_create_user(user_id)
        
        # ═══════════════ الأوامر الأساسية ═══════════════
        if text in ['البداية', 'بداية']:
            flex = FlexSendMessage(alt_text="البداية", contents=get_welcome_flex())
            line_bot_api.reply_message(event.reply_token, flex)
            return
        
        elif text in ['مساعدة', 'المساعدة']:
            flex = FlexSendMessage(alt_text="مساعدة", contents=get_help_flex())
            line_bot_api.reply_message(event.reply_token, flex)
            return
        
        elif text in ['انضم', 'تسجيل']:
            if user.get('registered', False):
                msg = TextMessage(text="✓ أنت مسجل بالفعل!")
            else:
                user['registered'] = True
                db['stats']['total_players'] = db['stats'].get('total_players', 0) + 1
                save_db(db)
                flex = FlexSendMessage(
                    alt_text="تم التسجيل",
                    contents=create_flex_bubble(
                        "تم التسجيل بنجاح",
                        [
                            {"type": "text", "text": f"مرحباً {user['name']}", "size": "md", "color": COLORS['text'], "weight": "bold"},
                            {"type": "text", "text": "✓ تم تسجيلك في النظام", "size": "sm", "color": COLORS['success'], "margin": "md"},
                            {"type": "text", "text": "الآن يمكنك جمع النقاط والمنافسة!", "size": "sm", "color": COLORS['text2'], "margin": "sm", "wrap": True}
                        ],
                        [
                            {"type": "button", "action": {"type": "message", "label": "▫️ ابدأ اللعب", "text": "أغنية"}, "style": "primary", "color": COLORS['success'], "height": "sm"}
                        ]
                    )
                )
                line_bot_api.reply_message(event.reply_token, flex)
                return
            line_bot_api.reply_message(event.reply_token, msg)
            return
        
        elif text in ['انسحب', 'الغاء']:
            if not user.get('registered', False):
                msg = TextMessage(text="✗ أنت غير مسجل أصلاً")
            else:
                user['registered'] = False
                save_db(db)
                flex = FlexSendMessage(
                    alt_text="تم الانسحاب",
                    contents=create_flex_bubble(
                        "تم إلغاء التسجيل",
                        [
                            {"type": "text", "text": "✓ تم إلغاء تسجيلك", "size": "md", "color": COLORS['text2']},
                            {"type": "text", "text": "يمكنك التسجيل مرة أخرى في أي وقت", "size": "sm", "color": COLORS['text2'], "margin": "md", "wrap": True}
                        ],
                        [
                            {"type": "button", "action": {"type": "message", "label": "▫️ انضم مجدداً", "text": "انضم"}, "style": "secondary", "height": "sm"}
                        ]
                    )
                )
                line_bot_api.reply_message(event.reply_token, flex)
                return
            line_bot_api.reply_message(event.reply_token, msg)
            return
        
        elif text in ['نقاطي', 'نقاط']:
            flex = FlexSendMessage(alt_text="نقاطي", contents=get_stats_flex(user_id))
            line_bot_api.reply_message(event.reply_token, flex)
            return
        
        elif text in ['الصدارة', 'صدارة']:
            flex = FlexSendMessage(alt_text="الصدارة", contents=get_leaderboard_flex())
            line_bot_api.reply_message(event.reply_token, flex)
            return
        
        # ═══════════════ ألعاب الترفيه (بدون نقاط) ═══════════════
        elif text in ['سؤال', 'سوال']:
            question = get_random_unused(QUESTIONS, 'questions_used')
            msg = TextMessage(text=f"▫️ {question}", quick_reply=get_quick_reply_buttons())
            line_bot_api.reply_message(event.reply_token, msg)
            return
        
        elif text == 'تحدي':
            challenge = get_random_unused(CHALLENGES, 'challenges_used')
            msg = TextMessage(text=f"▫️ {challenge}", quick_reply=get_quick_reply_buttons())
            line_bot_api.reply_message(event.reply_token, msg)
            return
        
        elif text == 'اعتراف':
            confession = get_random_unused(CONFESSIONS, 'confessions_used')
            msg = TextMessage(text=f"▫️ {confession}", quick_reply=get_quick_reply_buttons())
            line_bot_api.reply_message(event.reply_token, msg)
            return
        
        elif text == 'منشن':
            mention = get_random_unused(MENTIONS, 'mentions_used')
            msg = TextMessage(text=f"▫️ {mention}", quick_reply=get_quick_reply_buttons())
            line_bot_api.reply_message(event.reply_token, msg)
            return
        
        # ═══════════════ الألعاب التفاعلية ═══════════════
        # سيتم التعامل معها في ملفات الألعاب المنفصلة
        elif text in ['أغنية', 'لعبة', 'سلسلة', 'أسرع', 'ضد', 'تكوين', 'اختلاف', 'توافق']:
            # رسالة مؤقتة حتى يتم تطوير الألعاب
            msg = TextMessage(
                text=f"▫️ لعبة {text} قيد التطوير\n\nاستخدم الأوامر الأخرى للتجربة!",
                quick_reply=get_quick_reply_buttons()
            )
            line_bot_api.reply_message(event.reply_token, msg)
            return
        
        elif text == 'ايقاف':
            if room_id and room_id in db['games']:
                del db['games'][room_id]
                save_db(db)
                msg = TextMessage(text="✓ تم إيقاف اللعبة")
                line_bot_api.reply_message(event.reply_token, msg)
            return
        
    except Exception as e:
        logger.error(f"❌ خطأ في معالجة الرسالة: {e}", exc_info=True)

# ═══════════════════════════════════════════════════════════════
# نظام التنظيف التلقائي
# ═══════════════════════════════════════════════════════════════
def cleanup_inactive_users():
    """حذف المستخدمين غير النشطين"""
    while True:
        try:
            time.sleep(86400)  # كل 24 ساعة
            
            cutoff_date = datetime.now() - timedelta(days=CLEANUP_DAYS)
            removed = 0
            
            for user_id in list(db['users'].keys()):
                user = db['users'][user_id]
                last_active = datetime.fromisoformat(user['last_active'])
                
                if last_active < cutoff_date:
                    del db['users'][user_id]
                    if user_id in names_cache:
                        del names_cache[user_id]
                    removed += 1
            
            if removed > 0:
                save_db(db)
                logger.info(f"🧹 تم حذف {removed} مستخدم غير نشط")
        
        except Exception as e:
            logger.error(f"❌ خطأ في التنظيف: {e}")

# ═══════════════════════════════════════════════════════════════
# Routes
# ═══════════════════════════════════════════════════════════════
@app.route("/", methods=['GET'])
def home():
    """الصفحة الرئيسية"""
    ai_status = "مفعّل" if GEMINI_KEYS else "معطّل"
    ai_class = "success" if GEMINI_KEYS else "warning"
    
    return f"""<!DOCTYPE html>
<html dir="rtl" lang="ar">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width,initial-scale=1">
    <title>{BOT_NAME} - 3D Experience</title>
    <style>
        * {{margin:0;padding:0;box-sizing:border-box}}
        body {{
            font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;
            background:{COLORS['bg']};
            min-height:100vh;
            display:flex;
            align-items:center;
            justify-content:center;
            padding:20px;
            position:relative;
            overflow:hidden
        }}
        .glow {{
            position:fixed;
            width:400px;
            height:400px;
            border-radius:50%;
            filter:blur(100px);
            opacity:0.3;
            animation:pulse 8s ease-in-out infinite
        }}
        .glow1 {{background:{COLORS['gradient1']};top:-100px;right:-100px}}
        .glow2 {{background:{COLORS['gradient3']};bottom:-100px;left:-100px;animation-delay:4s}}
        @keyframes pulse {{
            0%,100% {{opacity:0.3;transform:scale(1)}}
            50% {{opacity:0.5;transform:scale(1.1)}}
        }}
        .container {{
            background:{COLORS['card']};
            border:2px solid {COLORS['card2']};
            border-radius:32px;
            box-shadow:0 25px 50px rgba(0,0,0,0.5),0 0 80px {COLORS['glow']},inset 0 1px 0 rgba(255,255,255,0.1);
            padding:48px;
            max-width:600px;
            width:100%;
            position:relative;
            z-index:1
        }}
        .logo {{
            width:120px;
            height:120px;
            margin:0 auto 24px;
            background:{COLORS['card']};
            border:4px solid {COLORS['gradient1']};
            border-radius:50%;
            display:flex;
            align-items:center;
            justify-content:center;
            font-size:48px;
            font-weight:bold;
            color:{COLORS['gradient1']};
            box-shadow:0 0 40px {COLORS['glow']},inset 0 2px 8px rgba(0,0,0,0.3);
            position:relative
        }}
        .logo::before {{
            content:'';
            position:absolute;
            inset:-8px;
            background:{COLORS['glow']};
            border-radius:50%;
            filter:blur(20px);
            z-index:-1
        }}
        h1 {{
            color:{COLORS['text']};
            font-size:2.8em;
            margin-bottom:12px;
            text-align:center;
            font-weight:700;
            text-shadow:0 0 20px {COLORS['glow']},0 2px 4px rgba(0,0,0,0.5)
        }}
        .subtitle {{
            color:{COLORS['text2']};
            font-size:0.9em;
            text-align:center;
            margin-bottom:40px;
            letter-spacing:3px;
            text-transform:uppercase
        }}
        .status {{
            background:{COLORS['card2']};
            border-radius:24px;
            padding:28px;
            margin:24px 0;
            border:1px solid {COLORS['sep']};
            box-shadow:inset 0 2px 4px rgba(0,0,0,0.2),0 4px 8px rgba(0,0,0,0.3)
        }}
        .status-item {{
            display:flex;
            justify-content:space-between;
            align-items:center;
            padding:18px 0;
            border-bottom:1px solid {COLORS['sep']}
        }}
        .status-item:last-child {{border-bottom:none}}
        .label {{color:{COLORS['text2']};font-size:0.95em;font-weight:500}}
        .value {{color:{COLORS['text']};font-weight:700;font-size:1.2em}}
        .badge {{
            display:inline-flex;
            align-items:center;
            gap:6px;
            padding:8px 16px;
            border-radius:20px;
            font-size:0.85em;
            font-weight:600
        }}
        .badge::before {{
            content:'';
            width:8px;
            height:8px;
            border-radius:50%;
            animation:blink 2s ease-in-out infinite
        }}
        .badge.success {{background:rgba(16,185,129,0.2);color:{COLORS['success']};border:1px solid {COLORS['success']}}}
        .badge.success::before {{background:{COLORS['success']};box-shadow:0 0 8px {COLORS['success']}}}
        .badge.warning {{background:rgba(245,158,11,0.2);color:{COLORS['warning']};border:1px solid {COLORS['warning']}}}
        .badge.warning::before {{background:{COLORS['warning']};box-shadow:0 0 8px {COLORS['warning']}}}
        @keyframes blink {{
            0%,100% {{opacity:1}}
            50% {{opacity:0.5}}
        }}
        .copyright {{text-align:center;margin-top:40px}}
        .copyright-circle {{
            width:90px;
            height:90px;
            margin:0 auto 16px;
            background:{COLORS['card2']};
            border:3px solid {COLORS['sep']};
            border-radius:50%;
            display:flex;
            flex-direction:column;
            align-items:center;
            justify-content:center;
            box-shadow:0 4px 12px rgba(0,0,0,0.3),inset 0 2px 4px rgba(0,0,0,0.2)
        }}
        .copyright-circle .symbol {{color:{COLORS['gradient1']};font-size:36px;font-weight:bold;text-shadow:0 0 10px {COLORS['glow']}}}
        .copyright-circle .year {{color:{COLORS['text2']};font-size:11px;margin-top:6px;font-weight:600}}
        .copyright-text {{color:{COLORS['text2']};font-size:0.85em}}
        .container {{animation:slideUp 0.6s ease-out}}
        @keyframes slideUp {{
            from {{opacity:0;transform:translateY(30px)}}
            to {{opacity:1;transform:translateY(0)}}
        }}
        .logo {{animation:fadeIn 1s ease-out 0.2s both}}
        @keyframes fadeIn {{
            from {{opacity:0;transform:scale(0.8)}}
            to {{opacity:1;transform:scale(1)}}
        }}
        @media (max-width:768px) {{
            .container {{padding:32px 24px}}
            h1 {{font-size:2em}}
            .logo {{width:100px;height:100px;font-size:40px}}
        }}
    </style>
</head>
<body>
    <div class="glow glow1"></div>
    <div class="glow glow2"></div>
    <div class="container">
        <div class="logo">W</div>
        <h1>{BOT_NAME}</h1>
        <div class="subtitle">3D Gaming Experience</div>
        <div class="status">
            <div class="status-item">
                <span class="label">حالة الخادم</span>
                <span class="badge success">يعمل</span>
            </div>
            <div class="status-item">
                <span class="label">الذكاء الاصطناعي</span>
                <span class="badge {ai_class}">{ai_status}</span>
            </div>
            <div class="status-item">
                <span class="label">إجمالي المستخدمين</span>
                <span class="value">{len(db['users'])}</span>
            </div>
            <div class="status-item">
                <span class="label">المسجلين</span>
                <span class="value">{sum(1 for u in db['users'].values() if u.get('registered'))}</span>
            </div>
            <div class="status-item">
                <span class="label">الألعاب النشطة</span>
                <span class="value">{len(db['games'])}</span>
            </div>
            <div class="status-item">
                <span class="label">إجمالي الألعاب</span>
                <span class="value">{db['stats'].get('total_games', 0)}</span>
            </div>
        </div>
        <div class="copyright">
            <div class="copyright-circle">
                <span class="symbol">©</span>
                <span class="year">2025</span>
            </div>
            <div class="copyright-text">{BOT_NAME} - جميع الحقوق محفوظة</div>
        </div>
    </div>
</body>
</html>"""

@app.route("/health", methods=['GET'])
def health():
    """فحص صحة السيرفر"""
    return jsonify({
        "status": "healthy",
        "version": VERSION,
        "timestamp": datetime.now().isoformat(),
        "users": len(db['users']),
        "registered": sum(1 for u in db['users'].values() if u.get('registered')),
        "active_games": len(db['games'])
    }), 200

@app.route("/callback", methods=['POST'])
def callback():
    """Webhook LINE"""
    signature = request.headers.get('X-Line-Signature', '')
    body = request.get_data(as_text=True)
    
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        logger.error("❌ توقيع LINE غير صالح")
        abort(400)
    except Exception as e:
        logger.error(f"❌ خطأ في Callback: {e}")
    
    return 'OK'

@app.route("/admin/reload", methods=['POST'])
def admin_reload():
    """إعادة تحميل المحتوى (Admin فقط)"""
    token = request.headers.get('X-Admin-Token', '')
    if token != ADMIN_TOKEN:
        abort(403)
    
    global QUESTIONS, CHALLENGES, CONFESSIONS, MENTIONS
    try:
        QUESTIONS = load_content('questions.txt')
        CHALLENGES = load_content('challenges.txt')
        CONFESSIONS = load_content('confessions.txt')
        MENTIONS = load_content('mentions.txt')
        logger.info("✅ تم إعادة تحميل المحتوى")
        return jsonify({"status": "reloaded"}), 200
    except Exception as e:
        logger.error(f"❌ خطأ في إعادة التحميل: {e}")
        return jsonify({"error": str(e)}), 500

# ═══════════════════════════════════════════════════════════════
# تشغيل البوت
# ═══════════════════════════════════════════════════════════════
if __name__ == "__main__":
    print("\n" + "═"*70)
    print(f"  {BOT_NAME} - {VERSION}")
    print("  3D Gaming Experience")
    print("═"*70 + "\n")
    
    # تشغيل نظام التنظيف
    cleanup_thread = Thread(target=cleanup_inactive_users, daemon=True)
    cleanup_thread.start()
    logger.info("✅ تم تشغيل نظام التنظيف التلقائي")
    
    # تشغيل السيرفر
    port = int(os.environ.get('PORT', 5000))
    logger.info(f"🚀 تشغيل السيرفر على المنفذ {port}")
    
    try:
        app.run(host='0.0.0.0', port=port, debug=False, threaded=True)
    except KeyboardInterrupt:
        logger.info("⏹️ إيقاف البوت...")
        save_db(db)
        logger.info("✅ تم حفظ البيانات")
