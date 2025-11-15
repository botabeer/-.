"""
Helper Functions
Utility functions used across the application
"""

import re
import os
import logging
from typing import List, Optional

logger = logging.getLogger(__name__)

def normalize_text(text: str) -> str:
    """
    Normalize Arabic text for comparison
    - Removes diacritics
    - Normalizes Hamza variations
    - Normalizes Taa Marbuta
    - Converts to lowercase
    - Removes extra whitespace
    """
    if not text:
        return ""
    
    text = text.strip().lower()
    
    # Normalize Hamza variations
    text = text.replace('أ', 'ا').replace('إ', 'ا').replace('آ', 'ا')
    text = text.replace('ؤ', 'و').replace('ئ', 'ي').replace('ء', '')
    
    # Normalize Taa Marbuta and Alif Maqsura
    text = text.replace('ة', 'ه').replace('ى', 'ي')
    
    # Remove diacritics (Tashkeel)
    text = re.sub(r'[\u064B-\u065F]', '', text)
    
    # Remove extra whitespace
    text = re.sub(r'\s+', '', text)
    
    return text

def load_file(filename: str) -> List[str]:
    """
    Load text file and return list of lines
    Handles different encodings and removes empty lines
    """
    try:
        # Get the base directory (parent of config folder)
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        file_path = os.path.join(base_dir, filename)
        
        if not os.path.exists(file_path):
            logger.warning(f"⚠️ File not found: {filename}")
            return []
        
        # Try UTF-8 first, then fallback to UTF-8 with BOM
        encodings = ['utf-8', 'utf-8-sig', 'cp1256']
        
        for encoding in encodings:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    lines = [line.strip() for line in f.readlines()]
                    lines = [line for line in lines if line]  # Remove empty lines
                    logger.info(f"✅ Loaded {len(lines)} lines from {filename}")
                    return lines
            except UnicodeDecodeError:
                continue
        
        logger.error(f"❌ Could not decode file: {filename}")
        return []
        
    except Exception as e:
        logger.error(f"❌ Error loading file {filename}: {e}")
        return []

def validate_arabic_text(text: str, min_length: int = 1, max_length: int = 100) -> bool:
    """
    Validate if text contains Arabic characters and meets length requirements
    """
    if not text:
        return False
    
    text = text.strip()
    
    # Check length
    if len(text) < min_length or len(text) > max_length:
        return False
    
    # Check if text contains Arabic characters
    arabic_pattern = re.compile(r'[\u0600-\u06FF]')
    return bool(arabic_pattern.search(text))

def format_time_ago(timestamp) -> str:
    """
    Format timestamp to human-readable 'time ago' format in Arabic
    """
    try:
        from datetime import datetime
        
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        
        now = datetime.now()
        diff = now - timestamp
        
        seconds = diff.total_seconds()
        
        if seconds < 60:
            return "الآن"
        elif seconds < 3600:
            minutes = int(seconds / 60)
            return f"منذ {minutes} دقيقة" if minutes == 1 else f"منذ {minutes} دقائق"
        elif seconds < 86400:
            hours = int(seconds / 3600)
            return f"منذ {hours} ساعة" if hours == 1 else f"منذ {hours} ساعات"
        else:
            days = int(seconds / 86400)
            return f"منذ {days} يوم" if days == 1 else f"منذ {days} أيام"
            
    except Exception as e:
        logger.error(f"❌ Error formatting time: {e}")
        return "غير معروف"

def sanitize_input(text: str, max_length: int = 500) -> str:
    """
    Sanitize user input to prevent injection and limit length
    """
    if not text:
        return ""
    
    # Limit length
    text = text[:max_length]
    
    # Remove potentially harmful characters
    text = re.sub(r'[<>\"\'`]', '', text)
    
    # Remove excessive whitespace
    text = ' '.join(text.split())
    
    return text.strip()

def generate_hint(word: str, hint_level: int = 1) -> str:
    """
    Generate hint for a word based on hint level
    Level 1: First letter and length
    Level 2: First and last letter
    Level 3: Pattern with blanks
    """
    if not word:
        return ""
    
    word = word.strip()
    
    if hint_level == 1:
        first_letter = word[0]
        word_length = len(word)
        return f"▫️ يبدأ بحرف: {first_letter}\n▫️ عدد الحروف: {word_length}"
    
    elif hint_level == 2:
        first_letter = word[0]
        last_letter = word[-1]
        word_length = len(word)
        return f"▫️ يبدأ بـ: {first_letter}\n▫️ ينتهي بـ: {last_letter}\n▫️ عدد الحروف: {word_length}"
    
    elif hint_level == 3:
        # Show first letter and blanks
        pattern = word[0] + ' _ ' * (len(word) - 1)
        return f"▫️ النمط: {pattern}"
    
    return ""

def calculate_similarity(str1: str, str2: str) -> float:
    """
    Calculate similarity between two strings (0.0 to 1.0)
    Uses Levenshtein distance algorithm
    """
    if not str1 or not str2:
        return 0.0
    
    str1 = normalize_text(str1)
    str2 = normalize_text(str2)
    
    if str1 == str2:
        return 1.0
    
    # Simple Levenshtein distance implementation
    len1, len2 = len(str1), len(str2)
    
    if len1 == 0:
        return 0.0
    if len2 == 0:
        return 0.0
    
    matrix = [[0] * (len2 + 1) for _ in range(len1 + 1)]
    
    for i in range(len1 + 1):
        matrix[i][0] = i
    for j in range(len2 + 1):
        matrix[0][j] = j
    
    for i in range(1, len1 + 1):
        for j in range(1, len2 + 1):
            cost = 0 if str1[i-1] == str2[j-1] else 1
            matrix[i][j] = min(
                matrix[i-1][j] + 1,      # deletion
                matrix[i][j-1] + 1,      # insertion
                matrix[i-1][j-1] + cost  # substitution
            )
    
    max_len = max(len1, len2)
    distance = matrix[len1][len2]
    similarity = 1.0 - (distance / max_len)
    
    return similarity

def is_close_match(answer: str, correct: str, threshold: float = 0.8) -> bool:
    """
    Check if answer is close enough to correct answer
    Useful for accepting minor spelling mistakes
    """
    similarity = calculate_similarity(answer, correct)
    return similarity >= threshold

def split_arabic_words(text: str) -> List[str]:
    """
    Split Arabic text into words while handling special cases
    """
    if not text:
        return []
    
    # Split by whitespace
    words = text.split()
    
    # Filter out empty strings and short words (< 2 chars)
    words = [w.strip() for w in words if len(w.strip()) >= 2]
    
    return words

def count_arabic_words(text: str) -> int:
    """
    Count number of Arabic words in text
    """
    words = split_arabic_words(text)
    return len(words)

def extract_first_letter(text: str) -> Optional[str]:
    """
    Extract first Arabic letter from text
    """
    if not text:
        return None
    
    # Find first Arabic character
    arabic_pattern = re.compile(r'[\u0600-\u06FF]')
    match = arabic_pattern.search(text)
    
    if match:
        return match.group()
    return None

def extract_last_letter(text: str) -> Optional[str]:
    """
    Extract last Arabic letter from text
    """
    if not text:
        return None
    
    # Find all Arabic characters
    arabic_pattern = re.compile(r'[\u0600-\u06FF]')
    matches = arabic_pattern.findall(text)
    
    if matches:
        return matches[-1]
    return None

def format_number_arabic(number: int) -> str:
    """
    Format number with Arabic formatting
    """
    if number < 0:
        return f"-{abs(number):,}".replace(',', '،')
    return f"{number:,}".replace(',', '،')

def truncate_text(text: str, max_length: int = 50, suffix: str = "...") -> str:
    """
    Truncate text to max length with suffix
    """
    if not text or len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix

def clean_whitespace(text: str) -> str:
    """
    Clean excessive whitespace from text
    """
    if not text:
        return ""
    
    # Replace multiple spaces with single space
    text = re.sub(r'\s+', ' ', text)
    
    # Remove leading/trailing whitespace
    return text.strip()
