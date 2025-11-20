from database import Database
import os

def init_database():
    print("جاري تهيئة قاعدة البيانات...")
    
    db_path = 'whale_bot.db'
    
    if os.path.exists(db_path):
        print(f"قاعدة البيانات موجودة: {db_path}")
        response = input("هل تريد اعادة انشائها؟ (y/n): ")
        if response.lower() == 'y':
            os.remove(db_path)
            print("تم حذف قاعدة البيانات القديمة")
    
    db = Database(db_path)
    print("تم انشاء قاعدة البيانات بنجاح")
    
    print("\nالجداول المنشأة:")
    print("- players (اللاعبين)")
    print("- game_history (سجل الالعاب)")
    
    print("\nالفهارس المنشأة:")
    print("- idx_points (ترتيب النقاط)")
    print("- idx_active (آخر نشاط)")
    print("- idx_history_user (سجل المستخدم)")
    
    print("\nتمت التهيئة بنجاح!")

if __name__ == "__main__":
    init_database()
