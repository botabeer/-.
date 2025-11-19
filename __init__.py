# games/__init__.py

# استيراد الدالة start_game من ملف games.py الرئيسي
try:
    from .games import start_game
except ImportError:
    start_game = None
    print("✗ تحذير: لم يتم تحميل start_game من games.py")
