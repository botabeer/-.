# ============================================
# tests/test_bot.py - اختبارات آلية
# ============================================

import pytest
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database import db
from rules import POINTS, GAMES_INFO, MAIN_GAMES
from style import create_welcome_flex, create_help_flex
from utils import normalize_text, sanitize_input

class TestDatabase:
    """اختبارات قاعدة البيانات"""
    
    def test_create_player(self):
        player = db.create_player('U123', 'Test User')
        assert player is not None
        assert player['name'] == 'Test User'
        assert player['points'] == 0
    
    def test_update_points(self):
        db.create_player('U456', 'Test User 2')
        db.update_points('U456', POINTS['correct'])
        player = db.get_player('U456')
        assert player['points'] == POINTS['correct']
    
    def test_leaderboard(self):
        leaderboard = db.get_leaderboard(10)
        assert isinstance(leaderboard, list)

class TestUtils:
    """اختبارات الدوال المساعدة"""
    
    def test_normalize_text(self):
        assert normalize_text('  مرحبا  ') == 'مرحبا'
        assert normalize_text('مَرْحَباً') == 'مرحبا'
    
    def test_sanitize_input(self):
        assert len(sanitize_input('a' * 1000)) <= 500
        assert '<script>' not in sanitize_input('<script>alert(1)</script>')

class TestRules:
    """اختبارات القوانين"""
    
    def test_points_system(self):
        assert POINTS['correct'] == 2
        assert POINTS['hint'] == -1
        assert POINTS['answer'] == 0
    
    def test_games_info(self):
        for game in MAIN_GAMES:
            assert game in GAMES_INFO
            assert 'name' in GAMES_INFO[game]
            assert 'rounds' in GAMES_INFO[game]

class TestStyle:
    """اختبارات التصاميم"""
    
    def test_welcome_flex(self):
        flex = create_welcome_flex()
        assert flex['type'] == 'carousel'
        assert len(flex['contents']) == 2
    
    def test_help_flex(self):
        flex = create_help_flex()
        assert flex['type'] == 'bubble'
        assert 'body' in flex

class TestGemini:
    """اختبارات Gemini AI"""
    
    @pytest.mark.skipif(not os.getenv('GEMINI_API_KEY_1'), reason="No API key")
    def test_gemini_response(self):
        from gemini_service import gemini
        response = gemini.generate_response("مرحبا")
        assert isinstance(response, str)
        assert len(response) > 0

class TestMonitoring:
    """اختبارات المراقبة"""
    
    def test_health_check(self):
        from monitoring import monitoring
        health = monitoring.get_health()
        assert 'status' in health
        assert health['status'] in ['healthy', 'unhealthy']

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
