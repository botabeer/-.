"""
Utility Functions
=================
Helper functions for the bot
"""

import random
import os

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
    import re
    text = re.sub(r'[\u0617-\u061A\u064B-\u0652]', '', text)
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
