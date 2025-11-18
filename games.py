# ============================================
# games.py - جميع الألعاب
# ============================================
import random
from linebot.models import FlexSendMessage, TextSendMessage

C = {'bg':'#0A0E27', 'card':'#0F2440', 'text':'#E0F2FF', 'text2':'#7FB3D5', 'cyan':'#00D9FF'}

# بيانات الألعاب
GAMES_DATA = {
    'fast': {
        'name': 'أسرع ⏱️',
        'questions': [
            {'q': 'اكتب: سبحان الله', 'a': 'سبحان الله'},
            {'q': 'اكتب: الحمد لله', 'a': 'الحمد لله'},
            {'q': 'اكتب: الله أكبر', 'a': 'الله أكبر'},
            {'q': 'اكتب: لا إله إلا الله', 'a': 'لا إله إلا الله'},
            {'q': 'اكتب: استغفر الله', 'a': 'استغفر الله'}
        ]
    },
    'song': {
        'name': 'أغنية 🎵',
        'questions': [
            {'q': 'قولي أحبك كي تزيد وسامتي', 'a': 'كاظم الساهر'},
            {'q': 'يا طير يا طاير طير وهات أخبار', 'a': 'عبد المجيد عبد الله'},
            {'q': 'لو كان قلبي معي ما اخترت غيركم', 'a': 'محمد عبده'},
            {'q': 'قلبي معاك ولا بعيد عنك', 'a': 'راشد الماجد'},
            {'q': 'وش جاب لجيته على بالي', 'a': 'عبادي الجوهر'}
        ]
    },
    'opposite': {
        'name': 'ضد ↔️',
        'questions': [
            {'q': 'ما عكس: حار', 'a': 'بارد'},
            {'q': 'ما عكس: سريع', 'a': 'بطيء'},
            {'q': 'ما عكس: كبير', 'a': 'صغير'},
            {'q': 'ما عكس: قوي', 'a': 'ضعيف'},
            {'q': 'ما عكس: جميل', 'a': 'قبيح'}
        ]
    }
}

def create_game_card(game_name, question_text, current, total, show_buttons=True):
    buttons = []
    if show_buttons:
        buttons = [
            {"type":"button", "action":{"type":"message", "label":"لمح", "text":"لمح"}, 
             "style":"secondary", "color":"#FFFFFF", "height":"sm"},
            {"type":"button", "action":{"type":"message", "label":"جاوب", "text":"جاوب"}, 
             "style":"primary", "color":"#FFFFFF", "height":"sm"}
        ]
    
    return FlexSendMessage(alt_text=game_name, contents={
        "type":"bubble", "size":"mega", "direction":"rtl", "body":{
            "type":"box", "layout":"vertical", "spacing":"md", "backgroundColor":C['bg'], 
            "paddingAll":"20px", "contents":[
                {"type":"box", "layout":"vertical", "contents":[
                    {"type":"text", "text":game_name, "weight":"bold", "size":"xl", "color":C['cyan']},
                    {"type":"text", "text":f"السؤال {current}/{total}", "size":"sm", "color":C['text2']}
                ]},
                {"type":"box", "layout":"vertical", "backgroundColor":C['card'], "cornerRadius":"12px", 
                 "paddingAll":"16px", "contents":[
                    {"type":"text", "text":question_text, "wrap":True, "color":C['text'], "size":"md"}
                ]},
                {"type":"box", "layout":"vertical", "height":"3px", "cornerRadius":"2px", 
                 "backgroundColor":C['cyan']},
                {"type":"box", "layout":"horizontal", "spacing":"md", "margin":"lg", 
                 "contents":buttons} if buttons else {"type":"box", "layout":"vertical", "contents":[]}
            ]
        }
    })

def start_game(game_type):
    game_data = GAMES_DATA.get(game_type, GAMES_DATA['fast'])
    current_q = 0
    
    def get_card():
        q = game_data['questions'][current_q]
        return create_game_card(game_data['name'], q['q'], current_q+1, 5, 
                               show_buttons=game_type != 'fast')
    
    def hint():
        q = game_data['questions'][current_q]
        ans = q['a']
        return f" تلميح\nأول حرف: {ans[0]}\nعدد الحروف: {len(ans)}"
    
    def show_answer():
        nonlocal current_q
        q = game_data['questions'][current_q]
        ans = q['a']
        current_q += 1
        if current_q < 5:
            return get_card()
        return TextSendMessage(text=f"☑️ الإجابة: {ans}\n انتهت اللعبة!")
    
    def check(user_input):
        nonlocal current_q
        q = game_data['questions'][current_q]
        correct = user_input.strip().lower() == q['a'].lower()
        
        if correct:
            current_q += 1
            if current_q < 5:
                return {'correct': True, 'next': get_card(), 'msg': ''}
            return {'correct': True, 'next': TextSendMessage(text=" إجابة صحيحة!\n انتهت اللعبة!"), 'msg': ''}
        return {'correct': False, 'next': None, 'msg': '❌ إجابة خاطئة، حاول مرة أخرى'}
    
    return {'card': get_card(), 'hint': hint, 'show_answer': show_answer, 'check': check}
