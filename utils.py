"""
Utility Functions
=================
Helper functions for the bot
"""

import random
import os
import re

def read_random_line(filepath):
    """Read random line from file"""
    try:
        if not os.path.exists(filepath):
            return None
        
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = [line.strip() for line in f if line.strip()]
        
        return random.choice(lines) if lines else None
    except Exception:
        return None

def read_all_lines(filepath):
    """Read all lines from file"""
    try:
        if not os.path.exists(filepath):
            return []
        
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = [line.strip() for line in f if line.strip()]
        
        return lines
    except Exception:
        return []

def sanitize_input(text, max_length=500):
    """Clean and limit input text"""
    if not text:
        return ""
    
    text = text.strip()
    if len(text) > max_length:
        text = text[:max_length]
    
    return text

def normalize_text(text):
    """Normalize Arabic text"""
    if not text:
        return ""
    
    # Remove diacritics
    text = re.sub(r'[\u0617-\u061A\u064B-\u0652]', '', text)
    
    # Normalize Arabic letters
    text = text.replace('أ', 'ا')
    text = text.replace('إ', 'ا')
    text = text.replace('آ', 'ا')
    text = text.replace('ة', 'ه')
    text = text.replace('ى', 'ي')
    
    # Remove extra spaces
    text = ' '.join(text.split())
    
    return text.strip()

def check_similarity(text1, text2):
    """Check text similarity"""
    text1 = normalize_text(text1).lower()
    text2 = normalize_text(text2).lower()
    
    if not text1 or not text2:
        return False
    
    return text1 == text2

def create_hint(answer, ratio=0.3):
    """Create hint from answer"""
    if not answer:
        return ""
    
    length = len(answer)
    reveal_count = max(1, int(length * ratio))
    positions = random.sample(range(length), min(reveal_count, length))
    
    hint = ['_' if answer[i] != ' ' else ' ' for i in range(length)]
    for pos in positions:
        hint[pos] = answer[pos]
    
    return ''.join(hint)

def shuffle_letters(word):
    """Shuffle letters in word"""
    if not word:
        return ""
    
    letters = list(word)
    random.shuffle(letters)
    return ''.join(letters)

def format_time(seconds):
    """Format seconds to readable time"""
    if seconds < 60:
        return f"{seconds} ثانية"
    elif seconds < 3600:
        minutes = seconds // 60
        return f"{minutes} دقيقة"
    else:
        hours = seconds // 3600
        return f"{hours} ساعة"

def parse_game_line(line):
    """Parse game file line (format: question|answer)"""
    if not line or '|' not in line:
        return None, None
    
    parts = line.split('|', 1)
    if len(parts) != 2:
        return None, None
    
    question = parts[0].strip()
    answer = parts[1].strip()
    
    return question, answer

def calculate_score(base_points, used_hint=False, time_taken=0, max_time=30):
    """Calculate score based on performance"""
    score = base_points
    
    if used_hint:
        score -= 2
    
    if time_taken > 0 and max_time > 0:
        time_ratio = time_taken / max_time
        if time_ratio < 0.3:
            score += 3
        elif time_ratio < 0.5:
            score += 2
        elif time_ratio < 0.7:
            score += 1
    
    return max(0, score)

def validate_answer(user_answer, correct_answer, fuzzy=True):
    """Validate answer with optional fuzzy matching"""
    if not user_answer or not correct_answer:
        return False
    
    user_answer = normalize_text(user_answer)
    correct_answer = normalize_text(correct_answer)
    
    if fuzzy:
        if user_answer in correct_answer or correct_answer in user_answer:
            return True
        
        if len(user_answer) > 3 and len(correct_answer) > 3:
            user_words = set(user_answer.split())
            correct_words = set(correct_answer.split())
            common = user_words & correct_words
            if len(common) >= len(correct_words) * 0.7:
                return True
    
    return user_answer == correct_answer

def get_ordinal(number):
    """Get ordinal number in Arabic"""
    ordinals = {
        1: "الأول", 2: "الثاني", 3: "الثالث", 4: "الرابع", 5: "الخامس",
        6: "السادس", 7: "السابع", 8: "الثامن", 9: "التاسع", 10: "العاشر"
    }
    return ordinals.get(number, f"الـ {number}")

def ensure_directory(directory):
    """Ensure directory exists"""
    if not os.path.exists(directory):
        os.makedirs(directory)

def ensure_file(filepath, default_content=""):
    """Ensure file exists"""
    if not os.path.exists(filepath):
        directory = os.path.dirname(filepath)
        if directory:
            ensure_directory(directory)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(default_content)
