import re
import random
import os

def normalize_text(text):
    if not text:
        return ""
    text = re.sub(r'[\u0617-\u061A\u064B-\u0652]', '', text)
    text = text.replace('أ', 'ا').replace('إ', 'ا').replace('آ', 'ا')
    text = text.replace('ة', 'ه').replace('ى', 'ي')
    return text.strip().lower()

def clean_input(text, max_length=500):
    if not text:
        return ""
    text = text.strip()
    if len(text) > max_length:
        text = text[:max_length]
    return text

def check_similarity(text1, text2, threshold=0.8):
    norm1 = normalize_text(text1)
    norm2 = normalize_text(text2)
    if norm1 == norm2:
        return True
    if len(norm1) != len(norm2):
        return False
    matches = sum(c1 == c2 for c1, c2 in zip(norm1, norm2))
    similarity = matches / len(norm1)
    return similarity >= threshold

def generate_hint(answer, reveal_percent=0.3):
    if not answer:
        return ""
    reveal_count = max(1, int(len(answer) * reveal_percent))
    hint = answer[:reveal_count] + '...'
    return hint

def shuffle_text(text):
    chars = list(text)
    random.shuffle(chars)
    return ''.join(chars)

def load_file_lines(filepath):
    if not os.path.exists(filepath):
        return []
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = [line.strip() for line in f if line.strip()]
    return lines

def save_file_lines(filepath, lines):
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as f:
        for line in lines:
            f.write(line + '\n')

def get_random_item(items):
    if not items:
        return None
    return random.choice(items)

def format_number(num):
    return f"{num:,}"

def truncate_text(text, max_length=100):
    if len(text) <= max_length:
        return text
    return text[:max_length-3] + '...'

def validate_arabic_text(text):
    if not text:
        return False
    arabic_pattern = re.compile(r'[\u0600-\u06FF]')
    return bool(arabic_pattern.search(text))

def remove_extra_spaces(text):
    return re.sub(r'\s+', ' ', text).strip()

def calculate_percentage(part, total):
    if total == 0:
        return 0
    return (part / total) * 100

def split_name_parts(full_name):
    parts = full_name.strip().split()
    if len(parts) >= 2:
        return parts[0], ' '.join(parts[1:])
    return full_name, ''

def is_valid_answer(answer, min_length=1):
    if not answer:
        return False
    answer = answer.strip()
    return len(answer) >= min_length
