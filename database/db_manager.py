from .db import Database

# إنشاء كائن قاعدة بيانات واحد يمكن استدعاؤه في كل المشروع
db_manager = Database("game_bot.db")
