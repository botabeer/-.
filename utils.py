# ============================================
# utils.py - الدوال المساعدة
# ============================================

"""
دوال مساعدة لبوت الحوت
=======================
دوال عامة للتحقق، القراءة، التحويل، والمعالجة
"""

import random
import re
import sqlite3
from datetime import datetime
from typing import List, Optional, Any
import os


def random_choice_from_file(file_path: str) -> Optional[str]:
    """
    اختيار عشوائي من ملف نصي
    
    Args:
        file_path: مسار الملف
        
    Returns:
        سطر عشوائي من الملف أو None
    """
    try:
        if not os.path.exists(file_path):
            return None
            
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = [line.strip() for line in f if line.strip()]
            
        return random.choice(lines) if lines else None
    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
        return None


def validate_answer(user_answer: str, correct_answers: List[str], strict: bool = False) -> bool:
    """
    التحقق من صحة الإجابة
    
    Args:
        user_answer: إجابة المستخدم
        correct_answers: قائمة الإجابات الصحيحة
        strict: هل التطابق صارم (case-sensitive)
        
    Returns:
        True إذا كانت الإجابة صحيحة
    """
    if not user_answer or not correct_answers:
        return False
        
    user_answer = user_answer.strip()
    
    if strict:
        return user_answer in correct_answers
    else:
        user_answer = user_answer.lower()
        return any(user_answer == ans.lower() for ans in correct_answers)


def normalize_text(text: str) -> str:
    """
    تطبيع النص (إزالة المسافات الزائدة والتشكيل)
    
    Args:
        text: النص المراد تطبيعه
        
    Returns:
        النص المطبّع
    """
    if not text:
        return ""
    
    # إزالة التشكيل
    text = re.sub(r'[\u0617-\u061A\u064B-\u0652]', '', text)
    
    # إزالة المسافات الزائدة
    text = ' '.join(text.split())
    
    return text.strip()


def calculate_similarity(text1: str, text2: str) -> float:
    """
    حساب نسبة التشابه بين نصين
    
    Args:
        text1: النص الأول
        text2: النص الثاني
        
    Returns:
        نسبة التشابه (0-100)
    """
    text1 = normalize_text(text1).lower()
    text2 = normalize_text(text2).lower()
    
    if not text1 or not text2:
        return 0.0
    
    if text1 == text2:
        return 100.0
    
    # حساب بسيط باستخدام الأحرف المشتركة
    set1 = set(text1)
    set2 = set(text2)
    
    intersection = len(set1 & set2)
    union = len(set1 | set2)
    
    if union == 0:
        return 0.0
        
    return (intersection / union) * 100


def format_timestamp(timestamp: Optional[datetime] = None) -> str:
    """
    تنسيق الوقت
    
    Args:
        timestamp: الوقت (None = الآن)
        
    Returns:
        النص المنسق
    """
    if timestamp is None:
        timestamp = datetime.now()
    
    return timestamp.strftime('%Y-%m-%d %H:%M:%S')


def sanitize_input(text: str, max_length: int = 500) -> str:
    """
    تنظيف وتأمين المدخلات
    
    Args:
        text: النص المدخل
        max_length: الطول الأقصى
        
    Returns:
        النص المنظف
    """
    if not text:
        return ""
    
    # إزالة المسافات الزائدة
    text = text.strip()
    
    # تحديد الطول
    if len(text) > max_length:
        text = text[:max_length]
    
    # إزالة الرموز الخطرة
    text = re.sub(r'[<>{}]', '', text)
    
    return text


def is_valid_user_id(user_id: str) -> bool:
    """
    التحقق من صحة معرف المستخدم
    
    Args:
        user_id: معرف المستخدم
        
    Returns:
        True إذا كان صحيحاً
    """
    if not user_id:
        return False
    
    # معرف LINE عادة يبدأ بـ U ويحتوي على أحرف وأرقام
    return bool(re.match(r'^U[a-f0-9]{32}$', user_id))


def parse_command(message: str) -> tuple:
    """
    تحليل الرسالة لاستخراج الأمر والمعاملات
    
    Args:
        message: الرسالة
        
    Returns:
        (command, args) - الأمر والمعاملات
    """
    if not message:
        return None, []
    
    parts = message.strip().split(maxsplit=1)
    command = parts[0]
    args = parts[1] if len(parts) > 1 else ""
    
    return command, args


def get_random_element(items: List[Any]) -> Optional[Any]:
    """
    اختيار عنصر عشوائي من قائمة
    
    Args:
        items: القائمة
        
    Returns:
        عنصر عشوائي أو None
    """
    return random.choice(items) if items else None


def split_into_chunks(text: str, chunk_size: int = 2000) -> List[str]:
    """
    تقسيم النص إلى أجزاء
    
    Args:
        text: النص
        chunk_size: حجم كل جزء
        
    Returns:
        قائمة الأجزاء
    """
    if not text:
        return []
    
    chunks = []
    for i in range(0, len(text), chunk_size):
        chunks.append(text[i:i + chunk_size])
    
    return chunks


def calculate_points_change(action: str, rules: dict) -> int:
    """
    حساب التغيير في النقاط بناءً على الإجراء
    
    Args:
        action: نوع الإجراء (correct, hint, answer, skip)
        rules: قواعد النقاط
        
    Returns:
        التغيير في النقاط
    """
    return rules.get(action, 0)


def format_leaderboard(players: List[tuple]) -> str:
    """
    تنسيق قائمة المتصدرين
    
    Args:
        players: قائمة اللاعبين [(name, points, rank), ...]
        
    Returns:
        نص منسق
    """
    if not players:
        return "لا يوجد لاعبون بعد"
    
    lines = ["المتصدرون:", "=" * 30]
    
    for name, points, rank in players[:10]:
        rank_symbol = {1: "🥇", 2: "🥈", 3: "🥉"}.get(rank, f"{rank}.")
        lines.append(f"{rank_symbol} {name} - {points} نقطة")
    
    return "\n".join(lines)


def create_hint(answer: str, reveal_ratio: float = 0.3) -> str:
    """
    إنشاء تلميح من الإجابة
    
    Args:
        answer: الإجابة الكاملة
        reveal_ratio: نسبة الأحرف المكشوفة
        
    Returns:
        التلميح
    """
    if not answer:
        return ""
    
    answer = answer.strip()
    length = len(answer)
    reveal_count = max(1, int(length * reveal_ratio))
    
    # اختيار مواضع عشوائية للكشف
    positions = random.sample(range(length), min(reveal_count, length))
    
    hint = list('_' * length)
    for pos in positions:
        if answer[pos] != ' ':
            hint[pos] = answer[pos]
        else:
            hint[pos] = ' '
    
    return ''.join(hint)


def get_time_remaining(start_time: datetime, duration: int) -> int:
    """
    حساب الوقت المتبقي
    
    Args:
        start_time: وقت البداية
        duration: المدة بالثواني
        
    Returns:
        الوقت المتبقي بالثواني
    """
    elapsed = (datetime.now() - start_time).total_seconds()
    remaining = max(0, duration - elapsed)
    return int(remaining)


def is_arabic(text: str) -> bool:
    """
    التحقق من وجود أحرف عربية في النص
    
    Args:
        text: النص
        
    Returns:
        True إذا كان يحتوي على عربي
    """
    if not text:
        return False
    
    arabic_pattern = re.compile(r'[\u0600-\u06FF]')
    return bool(arabic_pattern.search(text))


def validate_file_exists(file_path: str) -> bool:
    """
    التحقق من وجود الملف
    
    Args:
        file_path: مسار الملف
        
    Returns:
        True إذا كان موجوداً
    """
    return os.path.exists(file_path) and os.path.isfile(file_path)
