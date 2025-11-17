{
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                        {"type": "text", "text": "⚙️ أثناء اللعب", "size": "md", "weight": "bold", "color": COSMIC['primary']},
                        {"type": "text", "text": "▫️ لمح - الحصول على تلميح\n▫️ جاوب - عرض الإجابة", "size": "sm", "color": COSMIC['text_secondary'], "wrap": True, "margin": "md"}
                    ],
                    "backgroundColor": COSMIC['bg_card'],
                    "cornerRadius": "16px",
                    "paddingAll": "lg",
                    "margin": "md",
                    "borderWidth": "2px",
                    "borderColor": COSMIC['border']
                },
                {"type": "text", "text": "© Bot Al-Hout 2025", "size": "xs", "color": COSMIC['text_muted'], "align": "center", "margin": "lg"}
            ],
            "backgroundColor": COSMIC['bg_main'],
            "paddingAll": "xl"
        },
        "footer": {
            "type": "box",
            "layout": "horizontal",
            "contents": [
                {"type": "button", "action": {"type": "message", "label": "⚡ انضم", "text": "انضم"}, "style": "primary", "color": COSMIC['primary'], "height": "sm"},
                {"type": "button", "action": {"type": "message", "label": "📊 نقاطي", "text": "نقاطي"}, "style": "secondary", "height": "sm"},
                {"type": "button", "action": {"type": "message", "label": "🏆 الصدارة", "text": "الصدارة"}, "style": "secondary", "height": "sm"}
            ],
            "spacing": "sm",
            "backgroundColor": COSMIC['bg_main'],
            "paddingAll": "lg"
        }
    }

def get_stats_card(user_id, display_name):
    """بطاقة الإحصائيات - Cosmic Style"""
    stats = get_user_stats(user_id)
    
    if not stats:
        return {
            "type": "bubble",
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {"type": "text", "text": "⚠️", "size": "xxl", "align": "center"},
                    {"type": "text", "text": "إحصائياتك", "size": "xl", "weight": "bold", "color": COSMIC['text_main'], "align": "center", "margin": "md"},
                    {"type": "separator", "margin": "lg", "color": COSMIC['border']},
                    {"type": "text", "text": "لم تبدأ بعد", "size": "md", "color": COSMIC['text_secondary'], "align": "center", "margin": "xl"}
                ],
                "backgroundColor": COSMIC['bg_main'],
                "paddingAll": "xl"
            },
            "footer": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {"type": "button", "action": {"type": "message", "label": "⚡ ابدأ الآن", "text": "انضم"}, "style": "primary", "color": COSMIC['primary']}
                ],
                "backgroundColor": COSMIC['bg_main'],
                "paddingAll": "lg"
            }
        }
    
    win_rate = (stats['wins'] / stats['games_played'] * 100) if stats['games_played'] > 0 else 0
    
    return {
        "type": "bubble",
        "size": "mega",
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "box",
                    "layout": "horizontal",
                    "contents": [
                        {
                            "type": "box",
                            "layout": "vertical",
                            "contents": [
                                {"type": "text", "text": "إحصائياتك", "size": "sm", "color": COSMIC['text_secondary']},
                                {"type": "text", "text": display_name[:15], "size": "xxl", "weight": "bold", "color": COSMIC['text_main'], "margin": "xs", "wrap": True}
                            ],
                            "flex": 1
                        },
                        {
                            "type": "box",
                            "layout": "vertical",
                            "contents": [{"type": "text", "text": "🏆", "size": "xxl", "align": "center"}],
                            "width": "60px",
                            "height": "60px",
                            "backgroundColor": COSMIC['bg_card'],
                            "cornerRadius": "16px",
                            "justifyContent": "center",
                            "borderWidth": "3px",
                            "borderColor": COSMIC['primary']
                        }
                    ]
                },
                {
                    "type": "box",
                    "layout": "horizontal",
                    "contents": [
                        {
                            "type": "box",
                            "layout": "vertical",
                            "contents": [
                                {"type": "text", "text": "النقاط", "size": "xs", "color": COSMIC['text_secondary'], "align": "center"},
                                {"type": "text", "text": str(stats['total_points']), "size": "xxl", "weight": "bold", "color": COSMIC['primary'], "align": "center", "margin": "md"},
                                {"type": "text", "text": "⭐", "size": "lg", "align": "center", "margin": "sm"}
                            ],
                            "backgroundColor": COSMIC['bg_card'],
                            "cornerRadius": "16px",
                            "paddingAll": "lg",
                            "flex": 1,
                            "borderWidth": "2px",
                            "borderColor": COSMIC['border']
                        },
                        {
                            "type": "box",
                            "layout": "vertical",
                            "contents": [
                                {"type": "text", "text": "الألعاب", "size": "xs", "color": COSMIC['text_secondary'], "align": "center"},
                                {"type": "text", "text": str(stats['games_played']), "size": "xxl", "weight": "bold", "color": COSMIC['primary'], "align": "center", "margin": "md"},
                                {"type": "text", "text": "🎮", "size": "lg", "align": "center", "margin": "sm"}
                            ],
                            "backgroundColor": COSMIC['bg_card'],
                            "cornerRadius": "16px",
                            "paddingAll": "lg",
                            "flex": 1,
                            "margin": "md",
                            "borderWidth": "2px",
                            "borderColor": COSMIC['border']
                        }
                    ],
                    "margin": "xl"
                },
                {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                        {
                            "type": "box",
                            "layout": "horizontal",
                            "contents": [
                                {"type": "text", "text": "معدل الفوز", "size": "sm", "color": COSMIC['text_secondary'], "flex": 1},
                                {"type": "text", "text": f"{win_rate:.0f}%", "size": "sm", "weight": "bold", "color": COSMIC['primary'], "align": "end"}
                            ]
                        },
                        {
                            "type": "box",
                            "layout": "horizontal",
                            "contents": [
                                {"type": "box", "layout": "vertical", "contents": [], "backgroundColor": COSMIC['primary'], "height": "8px", "cornerRadius": "4px", "width": f"{min(win_rate, 100):.0f}%"}
                            ],
                            "backgroundColor": COSMIC['border'],
                            "height": "8px",
                            "cornerRadius": "4px",
                            "margin": "sm"
                        }
                    ],
                    "backgroundColor": COSMIC['bg_card'],
                    "cornerRadius": "12px",
                    "paddingAll": "md",
                    "margin": "xl",
                    "borderWidth": "1px",
                    "borderColor": COSMIC['border']
                }
            ],
            "paddingAll": "xl",
            "backgroundColor": COSMIC['bg_main']
        },
        "footer": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {"type": "button", "action": {"type": "message", "label": "🏆 الصدارة", "text": "الصدارة"}, "style": "secondary", "height": "sm"}
            ],
            "backgroundColor": COSMIC['bg_main'],
            "paddingAll": "lg"
        }
    }

def get_leaderboard_card():
    """لوحة الصدارة - Cosmic Style"""
    leaders = get_leaderboard()
    
    if not leaders:
        return {
            "type": "bubble",
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {"type": "text", "text": "🏆 لوحة الصدارة", "size": "xxl", "weight": "bold", "color": COSMIC['text_main'], "align": "center"},
                    {"type": "separator", "margin": "lg", "color": COSMIC['border']},
                    {"type": "text", "text": "لا توجد بيانات", "size": "md", "color": COSMIC['text_secondary'], "align": "center", "margin": "xl"}
                ],
                "backgroundColor": COSMIC['bg_main'],
                "paddingAll": "xl"
            }
        }
    
    player_items = []
    for i, leader in enumerate(leaders, 1):
        emoji = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else str(i)
        
        player_items.append({
            "type": "box",
            "layout": "horizontal",
            "contents": [
                {"type": "text", "text": emoji, "size": "md", "weight": "bold", "flex": 0, "color": COSMIC['primary']},
                {"type": "text", "text": leader['display_name'][:20], "size": "sm", "flex": 3, "margin": "md", "wrap": True, "color": COSMIC['text_main']},
                {"type": "text", "text": str(leader['total_points']), "size": "sm", "weight": "bold", "flex": 1, "align": "end", "color": COSMIC['primary']}
            ],
            "backgroundColor": COSMIC['bg_card'] if i > 3 else COSMIC['bg_elevated'],
            "cornerRadius": "12px",
            "paddingAll": "md",
            "margin": "sm" if i > 1 else "md",
            "borderWidth": "2px" if i <= 3 else "1px",
            "borderColor": COSMIC['primary'] if i <= 3 else COSMIC['border']
        })
    
    return {
        "type": "bubble",
        "size": "mega",
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {"type": "text", "text": "🏆 لوحة الصدارة", "size": "xxl", "weight": "bold", "color": COSMIC['text_main'], "align": "center"},
                {"type": "separator", "margin": "lg", "color": COSMIC['border']},
                {"type": "text", "text": "أفضل اللاعبين", "size": "sm", "color": COSMIC['text_secondary'], "align": "center", "margin": "md"},
                {"type": "box", "layout": "vertical", "contents": player_items, "margin": "lg"}
            ],
            "backgroundColor": COSMIC['bg_main'],
            "paddingAll": "xl"
        }
    }

def get_winner_card(winner_name, winner_score, all_scores):
    """بطاقة الفائز - Cosmic Style"""
    score_items = []
    for i, (name, score) in enumerate(all_scores, 1):
        if i == 1:
            rank_text = "🥇 المركز الأول"
            text_color = COSMIC['primary']
            bg_color = COSMIC['bg_elevated']
        elif i == 2:
            rank_text = "🥈 المركز الثاني"
            text_color = COSMIC['text_main']
            bg_color = COSMIC['bg_card']
        elif i == 3:
            rank_text = "🥉 المركز الثالث"
            text_color = COSMIC['text_main']
            bg_color = COSMIC['bg_card']
        else:
            rank_text = f"▫️ المركز {i}"
            text_color = COSMIC['text_secondary']
            bg_color = COSMIC['bg_card']
        
        score_items.append({
            "type": "box",
            "layout": "horizontal",
            "contents": [
                {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                        {"type": "text", "text": rank_text, "size": "xs", "color": COSMIC['text_tertiary']},
                        {"type": "text", "text": name, "size": "sm", "color": text_color, "weight": "bold", "wrap": True}
                    ],
                    "flex": 3
                },
                {"type": "text", "text": str(score), "size": "lg", "color": text_color, "weight": "bold", "align": "end", "flex": 1}
            ],
            "backgroundColor": bg_color,
            "cornerRadius": "12px",
            "paddingAll": "md",
            "margin": "sm" if i > 1 else "none",
            "borderWidth": "2px" if i == 1 else "1px",
            "borderColor": COSMIC['primary'] if i == 1 else COSMIC['border']
        })
    
    return {
        "type": "bubble",
        "size": "mega",
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                        {"type": "text", "text": "🎉", "size": "xxl", "align": "center"},
                        {"type": "text", "text": "انتهت اللعبة", "size": "xl", "weight": "bold", "color": COSMIC['text_main'], "align": "center", "margin": "md"}
                    ],
                    "backgroundColor": COSMIC['bg_elevated'],
                    "cornerRadius": "16px",
                    "paddingAll": "xl",
                    "borderWidth": "2px",
                    "borderColor": COSMIC['primary']
                },
                {"type": "separator", "margin": "xl", "color": COSMIC['border']},
                {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                        {"type": "text", "text": "الفائز", "size": "sm", "color": COSMIC['text_secondary'], "align": "center"},
                        {"type": "text", "text": winner_name, "size": "xxl", "weight": "bold", "color": COSMIC['primary'], "align": "center", "margin": "sm", "wrap": True},
                        {
                            "type": "box",
                            "layout": "horizontal",
                            "contents": [
                                {"type": "text", "text": f"{winner_score} نقطة", "size": "md", "weight": "bold", "color": COSMIC['text_secondary'], "align": "center"}
                            ],
                            "margin": "md"
                        }
                    ],
                    "margin": "xl"
                },
                {"type": "separator", "margin": "xl", "color": COSMIC['border']},
                {"type": "text", "text": "النتائج النهائية", "size": "md", "weight": "bold", "color": COSMIC['text_main'], "margin": "xl"},
                {"type": "box", "layout": "vertical", "contents": score_items, "margin": "md"}
            ],
            "backgroundColor": COSMIC['bg_main'],
            "paddingAll": "xl"
        },
        "footer": {
            "type": "box",
            "layout": "horizontal",
            "contents": [
                {"type": "button", "action": {"type": "message", "label": "⚡ لعب مرة أخرى", "text": "أغنية"}, "style": "primary", "color": COSMIC['primary'], "height": "sm"},
                {"type": "button", "action": {"type": "message", "label": "🏆 الصدارة", "text": "الصدارة"}, "style": "secondary", "height": "sm"}
            ],
            "spacing": "sm",
            "backgroundColor": COSMIC['bg_main'],
            "paddingAll": "lg"
        }
    }

# ═══════════════════════════════════════════════════════════════
# دالة بدء اللعبة
# ═══════════════════════════════════════════════════════════════

def start_game(game_id, game_class, game_type, user_id, event):
    """بدء لعبة جديدة"""
    if game_class is None:
        try:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=f"▫️ لعبة {game_type} غير متوفرة حالياً", quick_reply=get_quick_reply())
            )
        except:
            pass
        return False
    
    try:
        with games_lock:
            if game_class in [SongGame, HumanAnimalPlantGame, LettersWordsGame]:
                game = game_class(line_bot_api, use_ai=USE_AI, ask_ai=ask_gemini)
            else:
                game = game_class(line_bot_api)
            
            with players_lock:
                participants = registered_players.copy()
                participants.add(user_id)
            
            active_games[game_id] = {
                'game': game,
                'type': game_type,
                'created_at': datetime.now(),
                'participants': participants,
                'answered_users': set()
            }
        
        response = game.start_game()
        if isinstance(response, TextSendMessage):
            response.quick_reply = get_quick_reply()
        elif isinstance(response, list):
            for r in response:
                if isinstance(r, TextSendMessage):
                    r.quick_reply = get_quick_reply()
        
        line_bot_api.reply_message(event.reply_token, response)
        logger.info(f"✅ بدأت لعبة {game_type} للمستخدم {user_id}")
        return True
    except Exception as e:
        logger.error(f"❌ خطأ بدء {game_type}: {e}")
        try:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="▫️ حدث خطأ في بدء اللعبة", quick_reply=get_quick_reply())
            )
        except:
            pass
        return False

# ═══════════════════════════════════════════════════════════════
# Routes
# ═══════════════════════════════════════════════════════════════

@app.route("/", methods=['GET'])
def home():
    games_status = []
    if SongGame: games_status.append("أغنية")
    if HumanAnimalPlantGame: games_status.append("لعبة")
    if ChainWordsGame: games_status.append("سلسلة")
    if FastTypingGame: games_status.append("أسرع")
    if OppositeGame: games_status.append("ضد")
    if LettersWordsGame: games_status.append("تكوين")
    if DifferencesGame: games_status.append("اختلاف")
    if CompatibilityGame: games_status.append("توافق")
    
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>بوت الحُوت</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <meta charset="utf-8">
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                background: linear-gradient(135deg, {COSMIC['bg_main']} 0%, {COSMIC['bg_card']} 100%);
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
                padding: 20px;
            }}
            .container {{
                background: {COSMIC['bg_card']};
                border: 2px solid {COSMIC['primary']};
                border-radius: 20px;
                box-shadow: 0 10px 40px rgba(0, 212, 255, 0.3);
                padding: 40px;
                max-width: 500px;
                width: 100%;
            }}
            h1 {{ 
                background: linear-gradient(135deg, {COSMIC['primary']} 0%, {COSMIC['secondary']} 100%);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                font-size: 2em; 
                margin-bottom: 10px; 
                text-align: center; 
            }}
            .status {{
                background: {COSMIC['bg_main']};
                border: 1px solid {COSMIC['border']};
                border-radius: 12px;
                padding: 20px;
                margin: 20px 0;
            }}
            .status-item {{
                display: flex;
                justify-content: space-between;
                padding: 10px 0;
                border-bottom: 1px solid {COSMIC['border']};
                color: {COSMIC['text_secondary']};
            }}
            .status-item:last-child {{ border-bottom: none; }}
            .label {{ color: {COSMIC['text_tertiary']}; }}
            .value {{ color: {COSMIC['primary']}; font-weight: bold; }}
            .games-list {{
                background: {COSMIC['bg_main']};
                border-radius: 8px;
                padding: 12px;
                margin-top: 10px;
                font-size: 0.85em;
                color: {COSMIC['text_secondary']};
            }}
            .footer {{ 
                text-align: center; 
                margin-top: 20px; 
                color: {COSMIC['text_muted']}; 
                font-size: 0.8em; 
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>♓ بوت الحُوت</h1>
            <div class="status">
                <div class="status-item">
                    <span class="label">حالة الخادم</span>
                    <span class="value">▪️ يعمل</span>
                </div>
                <div class="status-item">
                    <span class="label">Gemini AI</span>
                    <span class="value">{'✅ مفعّل' if USE_AI else '⚠️ معطّل'}</span>
                </div>
                <div class="status-item">
                    <span class="label">اللاعبون</span>
                    <span class="value">▫️ {len(registered_players)}</span>
                </div>
                <div class="status-item">
                    <span class="label">ألعاب نشطة</span>
                    <span class="value">▫️ {len(active_games)}</span>
                </div>
                <div class="status-item">
                    <span class="label">الألعاب المتوفرة</span>
                    <span class="value">▪️ {len(games_status)}/8</span>
                </div>
            </div>
            <div class="games-list">
                <strong>الألعاب الجاهزة:</strong><br>
                {', '.join(games_status) if games_status else 'لا توجد ألعاب متوفرة'}
            </div>
            <div class="footer">© Bot Al-Hout 2025 | Cosmic Depth</div>
        </div>
    </body>
    </html>
    """

@app.route("/health", methods=['GET'])
def health_check():
    """فحص صحة البوت"""
    with error_log_lock:
        error_count = len(error_log)
        last_error = error_log[-1] if error_log else None
    
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "active_games": len(active_games),
        "registered_players": len(registered_players),
        "cached_names": len(user_names_cache),
        "error_count": error_count,
        "last_error": last_error.get('timestamp') if last_error else None,
        "ai_enabled": USE_AI,
        "design": "Cosmic Depth"
    }, 200

@app.route("/callback", methods=['POST'])
def callback():
    """معالج Webhook"""
    signature = request.headers.get('X-Line-Signature')
    if not signature:
        logger.warning("⚠️ طلب بدون توقيع")
        abort(400)
    
    body = request.get_data(as_text=True)
    logger.info(f"📥 استلام webhook")
    
    try:
        handler.handle(body, signature)
        logger.info("✅ تم معالجة الحدث")
    except InvalidSignatureError:
        logger.error("❌ توقيع غير صالح")
        abort(400)
    except Exception as e:
        logger.error(f"❌ خطأ: {e}", exc_info=True)
    
    return 'OK', 200

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    """معالج الرسائل الرئيسي"""
    user_id = None
    text = None
    display_name = None
    game_id = None
    
    try:
        user_id = event.source.user_id
        text = event.message.text.strip() if event.message.text else ""
        
        if not user_id or not text:
            return
        
        with players_lock:
            if user_id not in registered_players:
                registered_players.add(user_id)
                ensure_user_exists(user_id)
        
        if not check_rate_limit(user_id):
            try:
                line_bot_api.reply_message(event.reply_token,
                    TextSendMessage(text="▪️ انتظر قليلاً", quick_reply=get_quick_reply()))
            except:
                pass
            return
        
        try:
            display_name = get_user_profile_safe(user_id)
        except:
            display_name = f"لاعب_{user_id[-4:]}"
        
        try:
            game_id = getattr(event.source, 'group_id', user_id)
        except:
            game_id = user_id
        
        logger.info(f"📨 {display_name}: {text[:50]}")
        
        # الأوامر الأساسية
        if text in ['البداية', 'ابدأ', 'start', 'البوت']:
            line_bot_api.reply_message(event.reply_token,
                FlexSendMessage(alt_text=f"مرحباً {display_name}",
                    contents=get_simple_welcome_card(display_name),
                    quick_reply=get_quick_reply()))
            return
        
        elif text in ['مساعدة', 'help']:
            line_bot_api.reply_message(event.reply_token,
                FlexSendMessage(alt_text="المساعدة", 
                    contents=get_help_card(), quick_reply=get_quick_reply()))
            return
        
        elif text in ['نقاطي', 'إحصائياتي', 'احصائياتي']:
            line_bot_api.reply_message(event.reply_token,
                FlexSendMessage(alt_text="إحصائياتك", 
                    contents=get_stats_card(user_id, display_name), quick_reply=get_quick_reply()))
            return
        
        elif text in ['الصدارة', 'المتصدرين']:
            line_bot_api.reply_message(event.reply_token,
                FlexSendMessage(alt_text="الصدارة", 
                    contents=get_leaderboard_card(), quick_reply=get_quick_reply()))
            return
        
        elif text in ['إيقاف', 'stop', 'ايقاف']:
            with games_lock:
                if game_id in active_games:
                    game_type = active_games[game_id]['type']
                    del active_games[game_id]
                    line_bot_api.reply_message(event.reply_token,
                        TextSendMessage(text=f"▪️ تم إيقاف لعبة {game_type}", quick_reply=get_quick_reply()))
                else:
                    line_bot_api.reply_message(event.reply_token,
                        TextSendMessage(text="▫️ لا توجد لعبة نشطة", quick_reply=get_quick_reply()))
            return
        
        elif text in ['انضم', 'تسجيل', 'join']:
            with players_lock:
                if user_id in registered_players:
                    line_bot_api.reply_message(event.reply_token,
                        TextSendMessage(text=f"▪️ أنت مسجل بالفعل يا {display_name}",
                            quick_reply=get_quick_reply()))
                else:
                    registered_players.add(user_id)
                    line_bot_api.reply_message(event.reply_token,
                        FlexSendMessage(alt_text="تم التسجيل", 
                            contents=get_simple_registration_card(display_name), 
                            quick_reply=get_quick_reply()))
                    logger.info(f"✅ انضم: {display_name}")
            return
        
        elif text in ['انسحب', 'خروج']:
            with players_lock:
                if user_id in registered_players:
                    registered_players.remove(user_id)
                    line_bot_api.reply_message(event.reply_token,
                        FlexSendMessage(alt_text="تم الانسحاب",
                            contents=get_simple_withdrawal_card(display_name),
                            quick_reply=get_quick_reply()))
                    logger.info(f"❌ انسحب: {display_name}")
                else:
                    line_bot_api.reply_message(event.reply_token,
                        TextSendMessage(text="▫️ أنت غير مسجل", quick_reply=get_quick_reply()))
            return
        
        # الأوامر النصية
        elif text in ['سؤال', 'سوال']:
            if QUESTIONS:
                line_bot_api.reply_message(event.reply_token,
                    TextSendMessage(text=f"▪️ {random.choice(QUESTIONS)}", quick_reply=get_quick_reply()))
            else:
                line_bot_api.reply_message(event.reply_token,
                    TextSendMessage(text="▫️ ملف الأسئلة غير متوفر", quick_reply=get_quick_reply()))
            return
        
        elif text in ['تحدي', 'challenge']:
            if CHALLENGES:
                line_bot_api.reply_message(event.reply_token,
                    TextSendMessage(text=f"▪️ {random.choice(CHALLENGES)}", quick_reply=get_quick_reply()))
            else:
                line_bot_api.reply_message(event.reply_token,
                    TextSendMessage(text="▫️ ملف التحديات غير متوفر", quick_reply=get_quick_reply()))
            return
        
        elif text in ['اعتراف', 'confession']:
            if CONFESSIONS:
                line_bot_api.reply_message(event.reply_token,
                    TextSendMessage(text=f"▪️ {random.choice(CONFESSIONS)}", quick_reply=get_quick_reply()))
            else:
                line_bot_api.reply_message(event.reply_token,
                    TextSendMessage(text="▫️ ملف الاعترافات غير متوفر", quick_reply=get_quick_reply()))
            return
        
        elif text in ['منشن', 'mention']:
            if MENTION_QUESTIONS:
                line_bot_api.reply_message(event.reply_token,
                    TextSendMessage(text=f"▪️ {random.choice(MENTION_QUESTIONS)}", quick_reply=get_quick_reply()))
            else:
                line_bot_api.reply_message(event.reply_token,
                    TextSendMessage(text="▫️ ملف المنشن غير متوفر", quick_reply=get_quick_reply()))
            return
        
        # بدء الألعاب
        games_map = {
            'أغنية': (SongGame, 'أغنية'),
            'لعبة': (HumanAnimalPlantGame, 'لعبة'),
            'سلسلة': (ChainWordsGame, 'سلسلة'),
            'أسرع': (FastTypingGame, 'أسرع'),
            'ضد': (OppositeGame, 'ضد'),
            'تكوين': (LettersWordsGame, 'تكوين'),
            'اختلاف': (DifferencesGame, 'اختلاف'),
            'توافق': (CompatibilityGame, 'توافق')
        }
        
        if text in games_map:
            game_class, game_type = games_map[text]
            
            if text == 'توافق':
                if CompatibilityGame is None:
                    line_bot_api.reply_message(event.reply_token,
                        TextSendMessage(text="▫️ لعبة التوافق غير متوفرة حالياً", quick_reply=get_quick_reply()))
                    return
                    
                with games_lock:
                    with players_lock:
                        participants = registered_players.copy()
                        participants.add(user_id)
                    game = CompatibilityGame(line_bot_api)
                    active_games[game_id] = {
                        'game': game,
                        'type': 'توافق',
                        'created_at': datetime.now(),
                        'participants': participants,
                        'answered_users': set(),
                        'last_game': text,
                        'waiting_for_names': True
                    }
                line_bot_api.reply_message(event.reply_token,
                    TextSendMessage(text="▪️ لعبة التوافق\n\nاكتب اسمين مفصولين بمسافة\n⚠️ نص فقط بدون @ أو رموز\n\nمثال: ميش عبير",
                        quick_reply=get_quick_reply()))
                logger.info(f"✅ بدأت لعبة توافق")
                return
            
            if game_id in active_games:
                active_games[game_id]['last_game'] = text
            
            start_game(game_id, game_class, game_type, user_id, event)
            return
        
        # معالجة لعبة التوافق
        if game_id in active_games:
            game_data = active_games[game_id]
            
            if game_data.get('type') == 'توافق' and game_data.get('waiting_for_names'):
                cleaned_text = text.replace('@', '').strip()
                
                if '@' in text:
                    line_bot_api.reply_message(event.reply_token,
                        TextSendMessage(text="▫️ اكتب الأسماء بدون @\nمثال: ميش عبير",
                            quick_reply=get_quick_reply()))
                    return
                
                names = cleaned_text.split()
                
                if len(names) < 2:
                    line_bot_api.reply_message(event.reply_token,
                        TextSendMessage(text="▫️ يجب كتابة اسمين مفصولين بمسافة\nمثال: ميش عبير",
                            quick_reply=get_quick_reply()))
                    return
                
                name1 = names[0].strip()
                name2 = names[1].strip()
                
                if not name1 or not name2:
                    line_bot_api.reply_message(event.reply_token,
                        TextSendMessage(text="▫️ الأسماء يجب أن تكون نصوص صحيحة",
                            quick_reply=get_quick_reply()))
                    return
                
                game = game_data['game']
                try:
                    result = game.check_answer(f"{name1} {name2}", user_id, display_name)
                    
                    game_data['waiting_for_names'] = False
                    
                    with games_lock:
                        if game_id in active_games:
                            del active_games[game_id]
                    
                    if result and result.get('response'):
                        response = result['response']
                        if isinstance(response, TextSendMessage):
                            response.quick_reply = get_quick_reply()
                        line_bot_api.reply_message(event.reply_token, response)
                    return
                except Exception as e:
                    logger.error(f"❌ خطأ في لعبة التوافق: {e}")
                    line_bot_api.reply_message(event.reply_token,
                        TextSendMessage(text="▫️ حدث خطأ. حاول مرة أخرى بكتابة: توافق",
                            quick_reply=get_quick_reply()))
                    return
        
        # معالجة إجابات الألعاب
        if game_id in active_games:
            game_data = active_games[game_id]
            
            with players_lock:
                is_registered = user_id in registered_players
            
            if not is_registered:
                return
            
            if 'answered_users' in game_data and user_id in game_data['answered_users']:
                return
            
            game = game_data['game']
            game_type = game_data['type']
            
            try:
                result = game.check_answer(text, user_id, display_name)
                if result:
                    if result.get('correct', False):
                        if 'answered_users' not in game_data:
                            game_data['answered_users'] = set()
                        game_data['answered_users'].add(user_id)
                    
                    points = result.get('points', 0)
                    if points > 0:
                        update_user_points(user_id, display_name, points,
                            result.get('won', False), game_type)
                    
                    if result.get('next_question', False):
                        game_data['answered_users'] = set()
                        next_q = game.next_question()
                        if next_q:
                            if isinstance(next_q, TextSendMessage):
                                next_q.quick_reply = get_quick_reply()
                            line_bot_api.reply_message(event.reply_token, next_q)
                        return
                    
                    if result.get('game_over', False):
                        with games_lock:
                            last_game_type = active_games[game_id].get('last_game', 'أغنية')
                            if game_id in active_games:
                                del active_games[game_id]
                        
                        if result.get('winner_card'):
                            winner_card = result['winner_card']
                            if 'footer' in winner_card and 'contents' in winner_card['footer']:
                                for button in winner_card['footer']['contents']:
                                    if button.get('type') == 'button' and 'لعب مرة أخرى' in button.get('action', {}).get('label', ''):
                                        button['action']['text'] = last_game_type
                            
                            line_bot_api.reply_message(event.reply_token,
                                FlexSendMessage(alt_text="الفائز", 
                                    contents=winner_card, quick_reply=get_quick_reply()))
                        else:
                            response = result.get('response', TextSendMessage(text=result.get('message', '')))
                            if isinstance(response, TextSendMessage):
                                response.quick_reply = get_quick_reply()
                            line_bot_api.reply_message(event.reply_token, response)
                        return
                    
                    response = result.get('response', TextSendMessage(text=result.get('message', '')))
                    if isinstance(response, TextSendMessage):
                        response.quick_reply = get_quick_reply()
                    elif isinstance(response, list):
                        for r in response:
                            if isinstance(r, TextSendMessage):
                                r.quick_reply = get_quick_reply()
                    line_bot_api.reply_message(event.reply_token, response)
                return
            except Exception as e:
                logger.error(f"❌ خطأ معالجة إجابة: {e}")
                return
    
    except Exception as e:
        logger.error(f"❌ خطأ في handle_message: {e}", exc_info=True)
        
        error_details = {
            'user_id': user_id[-4:] if user_id else 'Unknown',
            'text': text[:100] if text else 'Unknown',
            'display_name': display_name if display_name else 'Unknown',
            'game_id': str(game_id)[:20] if game_id else 'Unknown',
            'error': str(e)
        }
        
        try:
            log_error('handle_message', e, error_details)
            logger.error(f"   تفاصيل الخطأ: {error_details}")
        except:
            pass
        
        try:
            if hasattr(event, 'reply_token') and event.reply_token:
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(
                        text="▫️ حدث خطأ مؤقت. حاول مرة أخرى.",
                        quick_reply=get_quick_reply()
                    )
                )
        except Exception as reply_error:
            logger.error(f"❌ فشل إرسال رسالة الخطأ: {reply_error}")
            log_error('reply_error', reply_error, {'user_id': user_id[-4:] if user_id else 'Unknown'})

def cleanup_old_games():
    """تنظيف الألعاب القديمة"""
    while True:
        try:
            time.sleep(300)
            now = datetime.now()
            
            to_delete = []
            with games_lock:
                for game_id, game_data in active_games.items():
                    if now - game_data.get('created_at', now) > timedelta(minutes=15):
                        to_delete.append(game_id)
                for game_id in to_delete:
                    del active_games[game_id]
                if to_delete:
                    logger.info(f"🗑️ حذف {len(to_delete)} لعبة قديمة")
            
            with names_cache_lock:
                if len(user_names_cache) > 1000:
                    logger.info(f"🧹 تنظيف ذاكرة الأسماء: {len(user_names_cache)} → 0")
                    user_names_cache.clear()
        
        except Exception as e:
            logger.error(f"❌ خطأ التنظيف: {e}")

cleanup_thread = threading.Thread(target=cleanup_old_games, daemon=True)
cleanup_thread.start()

@app.errorhandler(InvalidSignatureError)
def handle_invalid_signature(error):
    logger.error(f"❌ توقيع غير صالح: {error}")
    return 'Invalid Signature', 400

@app.errorhandler(400)
def bad_request(error):
    logger.warning(f"⚠️ طلب غير صالح: {error}")
    return 'Bad Request', 400

@app.errorhandler(404)
def not_found(error):
    return 'Not Found', 404

@app.errorhandler(Exception)
def handle_error(error):
    logger.error(f"❌ خطأ غير متوقع: {error}", exc_info=True)
    if request.path == '/callback':
        return 'OK', 200
    return 'Internal Server Error', 500

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    logger.info("="*50)
    logger.info("🚀 بوت الحُوت - Cosmic Depth Edition")
    logger.info(f"🔌 المنفذ: {port}")
    logger.info(f"🤖 Gemini AI: {'✅ مفعّل' if USE_AI else '⚠️ معطّل'}")
    logger.info(f"📊 اللاعبون: {len(registered_players)}")
    logger.info(f"🎮 الألعاب: {len(active_games)}")
    logger.info(f"🎨 التصميم: Cosmic Depth")
    logger.info("="*50)
    
    app.run(host='0.0.0.0', port=port, debug=False, threaded=True)from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError, LineBotApiError
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
    QuickReply, QuickReplyButton, MessageAction,
    FlexSendMessage
)
import os
from datetime import datetime, timedelta
import sqlite3
from collections import defaultdict
import threading
import time
import random
import re
import logging
import sys

# ✅ إعداد Logger المحسّن
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("game-bot")

# ═══════════════════════════════════════════════════════════════
# 🎨 Cosmic Depth Design System
# ═══════════════════════════════════════════════════════════════

COSMIC = {
    'primary': '#00d4ff',      # نيون أزرق
    'secondary': '#0099ff',    # أزرق داكن
    'bg_main': '#0a0e27',      # خلفية رئيسية
    'bg_card': '#1a1f3a',      # خلفية البطاقات
    'bg_elevated': '#2a2f45',  # خلفية مرتفعة
    'text_main': '#ffffff',    # نص رئيسي
    'text_secondary': '#8b9dc3', # نص ثانوي
    'text_tertiary': '#6c7a8e',  # نص باهت
    'text_muted': '#4a5568',   # نص خافت
    'success': '#34C759',      # أخضر
    'warning': '#FF9500',      # برتقالي
    'error': '#FF3B30',        # أحمر
    'border': '#2a2f45'        # حدود
}

# إعداد Gemini AI
USE_AI = False
ask_gemini = None

try:
    import google.generativeai as genai
    GEMINI_API_KEYS = [
        os.getenv('GEMINI_API_KEY_1', ''),
        os.getenv('GEMINI_API_KEY_2', ''),
        os.getenv('GEMINI_API_KEY_3', '')
    ]
    GEMINI_API_KEYS = [key for key in GEMINI_API_KEYS if key]
    current_gemini_key_index = 0
    USE_AI = bool(GEMINI_API_KEYS)
    
    if USE_AI:
        genai.configure(api_key=GEMINI_API_KEYS[0])
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        logger.info(f"✅ Gemini AI جاهز - {len(GEMINI_API_KEYS)} مفاتيح")
        
        def ask_gemini(prompt, max_retries=2):
            """سؤال Gemini AI"""
            for attempt in range(max_retries):
                try:
                    response = model.generate_content(prompt)
                    return response.text.strip()
                except Exception as e:
                    logger.error(f"خطأ في Gemini (محاولة {attempt + 1}): {e}")
                    if attempt < max_retries - 1 and len(GEMINI_API_KEYS) > 1:
                        global current_gemini_key_index
                        current_gemini_key_index = (current_gemini_key_index + 1) % len(GEMINI_API_KEYS)
                        genai.configure(api_key=GEMINI_API_KEYS[current_gemini_key_index])
            return None
except Exception as e:
    USE_AI = False
    logger.warning(f"⚠️ Gemini AI غير متوفر: {e}")

# استيراد الألعاب مع معالجة الأخطاء
SongGame = None
HumanAnimalPlantGame = None
ChainWordsGame = None
FastTypingGame = None
OppositeGame = None
LettersWordsGame = None
DifferencesGame = None
CompatibilityGame = None

try:
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'games'))
    
    try:
        from song_game import SongGame
        logger.info("✅ تم استيراد SongGame")
    except Exception as e:
        logger.warning(f"⚠️ لم يتم استيراد SongGame: {e}")
    
    try:
        from human_animal_plant_game import HumanAnimalPlantGame
        logger.info("✅ تم استيراد HumanAnimalPlantGame")
    except Exception as e:
        logger.warning(f"⚠️ لم يتم استيراد HumanAnimalPlantGame: {e}")
    
    try:
        from chain_words_game import ChainWordsGame
        logger.info("✅ تم استيراد ChainWordsGame")
    except Exception as e:
        logger.warning(f"⚠️ لم يتم استيراد ChainWordsGame: {e}")
    
    try:
        from fast_typing_game import FastTypingGame
        logger.info("✅ تم استيراد FastTypingGame")
    except Exception as e:
        logger.warning(f"⚠️ لم يتم استيراد FastTypingGame: {e}")
    
    try:
        from opposite_game import OppositeGame
        logger.info("✅ تم استيراد OppositeGame")
    except Exception as e:
        logger.warning(f"⚠️ لم يتم استيراد OppositeGame: {e}")
    
    try:
        from letters_words_game import LettersWordsGame
        logger.info("✅ تم استيراد LettersWordsGame")
    except Exception as e:
        logger.warning(f"⚠️ لم يتم استيراد LettersWordsGame: {e}")
    
    try:
        from differences_game import DifferencesGame
        logger.info("✅ تم استيراد DifferencesGame")
    except Exception as e:
        logger.warning(f"⚠️ لم يتم استيراد DifferencesGame: {e}")
    
    try:
        from compatibility_game import CompatibilityGame
        logger.info("✅ تم استيراد CompatibilityGame")
    except Exception as e:
        logger.warning(f"⚠️ لم يتم استيراد CompatibilityGame: {e}")
        
except Exception as e:
    logger.error(f"❌ خطأ في استيراد الألعاب: {e}")

app = Flask(__name__)

LINE_CHANNEL_ACCESS_TOKEN = os.getenv('LINE_CHANNEL_ACCESS_TOKEN', 'YOUR_CHANNEL_ACCESS_TOKEN')
LINE_CHANNEL_SECRET = os.getenv('LINE_CHANNEL_SECRET', 'YOUR_CHANNEL_SECRET')

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

active_games = {}
registered_players = set()
user_message_count = defaultdict(lambda: {'count': 0, 'reset_time': datetime.now()})
user_names_cache = {}
error_log = []

games_lock = threading.Lock()
players_lock = threading.Lock()
names_cache_lock = threading.Lock()
error_log_lock = threading.Lock()

DB_NAME = 'game_scores.db'

def normalize_text(text):
    """تطبيع النص لقبول جميع أشكال الحروف"""
    if not text:
        return ""
    text = text.strip().lower()
    text = text.replace('أ', 'ا').replace('إ', 'ا').replace('آ', 'ا')
    text = text.replace('ؤ', 'و').replace('ئ', 'ي').replace('ء', '')
    text = text.replace('ة', 'ه').replace('ى', 'ي')
    text = re.sub(r'[\u064B-\u065F]', '', text)
    text = re.sub(r'\s+', '', text)
    return text

def get_db_connection():
    conn = sqlite3.connect(DB_NAME, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    try:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS users
                     (user_id TEXT PRIMARY KEY, display_name TEXT,
                      total_points INTEGER DEFAULT 0, games_played INTEGER DEFAULT 0,
                      wins INTEGER DEFAULT 0, last_played TEXT,
                      registered_at TEXT DEFAULT CURRENT_TIMESTAMP)''')
        c.execute('''CREATE TABLE IF NOT EXISTS game_history
                     (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT,
                      game_type TEXT, points INTEGER, won INTEGER,
                      played_at TEXT DEFAULT CURRENT_TIMESTAMP,
                      FOREIGN KEY (user_id) REFERENCES users(user_id))''')
        c.execute('''CREATE INDEX IF NOT EXISTS idx_user_points ON users(total_points DESC)''')
        conn.commit()
        conn.close()
        logger.info("✅ قاعدة البيانات جاهزة")
    except Exception as e:
        logger.error(f"❌ خطأ قاعدة البيانات: {e}")

init_db()

def update_user_points(user_id, display_name, points, won=False, game_type=""):
    """تحديث نقاط المستخدم مع حفظ/تحديث الاسم"""
    try:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        user = c.fetchone()
        
        if user:
            c.execute('''UPDATE users SET total_points = ?, games_played = ?, wins = ?, 
                         last_played = ?, display_name = ? WHERE user_id = ?''',
                      (user['total_points'] + points, user['games_played'] + 1,
                       user['wins'] + (1 if won else 0), datetime.now().isoformat(),
                       display_name, user_id))
            
            if user['display_name'] != display_name:
                logger.info(f"🔄 تحديث اسم عند حفظ النقاط: {user['display_name']} → {display_name}")
        else:
            c.execute('''INSERT INTO users (user_id, display_name, total_points, 
                         games_played, wins, last_played) VALUES (?, ?, ?, ?, ?, ?)''',
                      (user_id, display_name, points, 1, 1 if won else 0, datetime.now().isoformat()))
            logger.info(f"✅ إضافة مستخدم جديد: {display_name}")
        
        if game_type:
            c.execute('''INSERT INTO game_history (user_id, game_type, points, won) 
                         VALUES (?, ?, ?, ?)''', (user_id, game_type, points, 1 if won else 0))
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"❌ خطأ تحديث النقاط: {e}")
        return False

def get_user_stats(user_id):
    try:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        user = c.fetchone()
        conn.close()
        return user
    except Exception as e:
        logger.error(f"❌ خطأ إحصائيات: {e}")
        return None

def get_leaderboard(limit=10):
    try:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('''SELECT display_name, total_points, games_played, wins 
                     FROM users ORDER BY total_points DESC LIMIT ?''', (limit,))
        leaders = c.fetchall()
        conn.close()
        return leaders
    except Exception as e:
        logger.error(f"❌ خطأ الصدارة: {e}")
        return []

def check_rate_limit(user_id, max_messages=30, time_window=60):
    now = datetime.now()
    user_data = user_message_count[user_id]
    if now - user_data['reset_time'] > timedelta(seconds=time_window):
        user_data['count'] = 0
        user_data['reset_time'] = now
    if user_data['count'] >= max_messages:
        return False
    user_data['count'] += 1
    return True

def load_text_file(filename):
    try:
        filepath = os.path.join('games', filename)
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                return [line.strip() for line in f if line.strip()]
        return []
    except Exception as e:
        logger.error(f"❌ خطأ تحميل ملف {filename}: {e}")
        return []

QUESTIONS = load_text_file('questions.txt')
CHALLENGES = load_text_file('challenges.txt')
CONFESSIONS = load_text_file('confessions.txt')
MENTION_QUESTIONS = load_text_file('more_questions.txt')

def log_error(error_type, message, details=None):
    """تسجيل الأخطاء في سجل مؤقت"""
    try:
        with error_log_lock:
            error_entry = {
                'timestamp': datetime.now().isoformat(),
                'type': error_type,
                'message': str(message),
                'details': details or {}
            }
            error_log.append(error_entry)
            if len(error_log) > 50:
                error_log.pop(0)
    except:
        pass

def ensure_user_exists(user_id):
    """التأكد من وجود سجل المستخدم في قاعدة البيانات"""
    try:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('SELECT user_id FROM users WHERE user_id = ?', (user_id,))
        
        if not c.fetchone():
            display_name = f"لاعب_{user_id[-4:]}"
            c.execute('''INSERT INTO users (user_id, display_name, total_points, 
                         games_played, wins, last_played) 
                         VALUES (?, ?, 0, 0, 0, ?)''',
                      (user_id, display_name, datetime.now().isoformat()))
            conn.commit()
            logger.info(f"🆕 إنشاء سجل جديد: {display_name} ({user_id[-4:]})")
        
        conn.close()
        return True
    except Exception as e:
        logger.error(f"❌ خطأ في ensure_user_exists: {e}")
        return False

def get_user_profile_safe(user_id):
    """الحصول على اسم المستخدم مع معالجة 404"""
    with names_cache_lock:
        if user_id in user_names_cache:
            cached_name = user_names_cache[user_id]
            if cached_name:
                return cached_name
    
    try:
        profile = line_bot_api.get_profile(user_id)
        display_name = profile.display_name
        
        if display_name and display_name.strip():
            display_name = display_name.strip()
            
            with names_cache_lock:
                user_names_cache[user_id] = display_name
            
            try:
                conn = get_db_connection()
                c = conn.cursor()
                c.execute('SELECT display_name FROM users WHERE user_id = ?', (user_id,))
                result = c.fetchone()
                
                if result:
                    old_name = result['display_name']
                    if old_name != display_name:
                        c.execute('UPDATE users SET display_name = ? WHERE user_id = ?',
                                  (display_name, user_id))
                        conn.commit()
                        logger.info(f"🔄 تحديث اسم: {old_name} → {display_name}")
                else:
                    c.execute('''INSERT INTO users (user_id, display_name, total_points, 
                                 games_played, wins) VALUES (?, ?, 0, 0, 0)''',
                              (user_id, display_name))
                    conn.commit()
                    logger.info(f"✅ حفظ اسم جديد: {display_name}")
                
                conn.close()
            except Exception as e:
                logger.error(f"❌ خطأ في تحديث الاسم بقاعدة البيانات: {e}")
            
            logger.info(f"✅ تم جلب اسم المستخدم: {display_name}")
            return display_name
        
        fallback_name = f"لاعب_{user_id[-4:]}"
        logger.warning(f"⚠️ اسم المستخدم فارغ لـ {user_id[-4:]}")
        
        with names_cache_lock:
            user_names_cache[user_id] = fallback_name
        
        return fallback_name
    
    except LineBotApiError as e:
        if e.status_code == 404:
            fallback_name = f"لاعب_{user_id[-4:] if user_id else 'xxxx'}"
            logger.warning(f"⚠️ ملف مستخدم غير موجود (404): {user_id[-4:]}")
            
            with names_cache_lock:
                user_names_cache[user_id] = fallback_name
            
            try:
                conn = get_db_connection()
                c = conn.cursor()
                c.execute('SELECT user_id FROM users WHERE user_id = ?', (user_id,))
                if not c.fetchone():
                    c.execute('''INSERT INTO users (user_id, display_name, total_points, 
                                 games_played, wins) VALUES (?, ?, 0, 0, 0)''',
                              (user_id, fallback_name))
                    conn.commit()
                conn.close()
            except Exception as db_e:
                logger.error(f"❌ خطأ في حفظ الاسم البديل: {db_e}")
            
            return fallback_name
        else:
            fallback_name = f"لاعب_{user_id[-4:] if user_id else 'xxxx'}"
            logger.error(f"❌ خطأ LINE API ({e.status_code}): {e.message}")
            
            with names_cache_lock:
                user_names_cache[user_id] = fallback_name
            
            return fallback_name
    
    except Exception as e:
        fallback_name = f"لاعب_{user_id[-4:] if user_id else 'xxxx'}"
        logger.error(f"❌ خطأ غير متوقع في get_profile ({user_id[-4:] if user_id else 'xxxx'}): {e}")
        
        with names_cache_lock:
            user_names_cache[user_id] = fallback_name
        
        return fallback_name

# ═══════════════════════════════════════════════════════════════
# Cosmic Depth - Flex Cards
# ═══════════════════════════════════════════════════════════════

def get_quick_reply():
    """الأزرار الثابتة - Cosmic Style"""
    return QuickReply(items=[
        QuickReplyButton(action=MessageAction(label="▪️سؤال", text="سؤال")),
        QuickReplyButton(action=MessageAction(label="▪️تحدي", text="تحدي")),
        QuickReplyButton(action=MessageAction(label="▪️اعتراف", text="اعتراف")),
        QuickReplyButton(action=MessageAction(label="▪️منشن", text="منشن")),
        QuickReplyButton(action=MessageAction(label="▫️أغنية", text="أغنية")),
        QuickReplyButton(action=MessageAction(label="▫️لعبة", text="لعبة")),
        QuickReplyButton(action=MessageAction(label="▫️سلسلة", text="سلسلة")),
        QuickReplyButton(action=MessageAction(label="▫️أسرع", text="أسرع")),
        QuickReplyButton(action=MessageAction(label="▫️ضد", text="ضد")),
        QuickReplyButton(action=MessageAction(label="▫️تكوين", text="تكوين")),
        QuickReplyButton(action=MessageAction(label="▫️اختلاف", text="اختلاف")),
        QuickReplyButton(action=MessageAction(label="▫️توافق", text="توافق"))
    ])

def get_simple_registration_card(display_name):
    """بطاقة تم التسجيل - Cosmic Style"""
    return {
        "type": "bubble",
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {"type": "text", "text": "✨", "size": "xxl", "align": "center"},
                {"type": "text", "text": "تم التسجيل بنجاح", "size": "xl", "weight": "bold", "color": COSMIC['text_main'], "align": "center", "margin": "md"},
                {"type": "separator", "margin": "lg", "color": COSMIC['border']},
                {"type": "text", "text": display_name, "size": "lg", "weight": "bold", "color": COSMIC['success'], "align": "center", "margin": "lg"},
                {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                        {"type": "text", "text": "يمكنك الآن:", "size": "sm", "color": COSMIC['text_secondary'], "weight": "bold"},
                        {"type": "text", "text": "⚡ اللعب وجمع النقاط", "size": "xs", "color": COSMIC['text_secondary'], "margin": "sm"},
                        {"type": "text", "text": "🏆 الظهور في لوحة الصدارة", "size": "xs", "color": COSMIC['text_secondary'], "margin": "sm"}
                    ],
                    "backgroundColor": COSMIC['bg_card'],
                    "cornerRadius": "12px",
                    "paddingAll": "md",
                    "margin": "lg",
                    "borderWidth": "1px",
                    "borderColor": COSMIC['border']
                }
            ],
            "backgroundColor": COSMIC['bg_main'],
            "paddingAll": "xl"
        },
        "footer": {
            "type": "box",
            "layout": "horizontal",
            "contents": [
                {"type": "button", "action": {"type": "message", "label": "⚡ ابدأ اللعب", "text": "أغنية"}, "style": "primary", "color": COSMIC['primary'], "height": "sm"}
            ],
            "backgroundColor": COSMIC['bg_main'],
            "paddingAll": "lg"
        }
    }

def get_simple_withdrawal_card(display_name):
    """بطاقة الانسحاب - Cosmic Style"""
    return {
        "type": "bubble",
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {"type": "text", "text": "👋", "size": "xxl", "align": "center"},
                {"type": "text", "text": "تم الانسحاب", "size": "xl", "weight": "bold", "color": COSMIC['text_main'], "align": "center", "margin": "md"},
                {"type": "separator", "margin": "lg", "color": COSMIC['border']},
                {"type": "text", "text": display_name, "size": "lg", "color": COSMIC['text_secondary'], "align": "center", "margin": "lg"},
                {"type": "text", "text": "نتمنى رؤيتك مرة أخرى", "size": "sm", "color": COSMIC['text_tertiary'], "align": "center", "margin": "md"}
            ],
            "backgroundColor": COSMIC['bg_main'],
            "paddingAll": "xl"
        }
    }

def get_simple_welcome_card(display_name):
    """بطاقة البداية - Cosmic Style"""
    return {
        "type": "bubble",
        "size": "mega",
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                        {"type": "text", "text": "♓", "size": "xxl", "weight": "bold", "color": COSMIC['primary'], "align": "center"}
                    ],
                    "width": "180px",
                    "height": "180px",
                    "cornerRadius": "90px",
                    "borderWidth": "4px",
                    "borderColor": COSMIC['primary'],
                    "backgroundColor": COSMIC['bg_card'],
                    "alignItems": "center",
                    "justifyContent": "center",
                    "margin": "xxl"
                },
                {"type": "text", "text": "بوت الحوت", "size": "3xl", "weight": "bold", "color": COSMIC['text_main'], "align": "center", "margin": "xl"},
                {"type": "text", "text": "3D Gaming Experience", "size": "lg", "color": COSMIC['text_secondary'], "align": "center", "margin": "md", "weight": "bold"},
                {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                        {"type": "text", "text": f"مرحباً {display_name}", "size": "md", "color": COSMIC['text_tertiary'], "align": "center", "wrap": True},
                        {"type": "text", "text": "استخدم الأزرار أدناه للعب", "size": "sm", "color": COSMIC['text_tertiary'], "align": "center", "margin": "sm", "wrap": True}
                    ],
                    "paddingAll": "md",
                    "backgroundColor": COSMIC['bg_card'],
                    "cornerRadius": "12px",
                    "margin": "lg",
                    "borderWidth": "1px",
                    "borderColor": COSMIC['border']
                },
                {"type": "text", "text": "© Bot Al-Hout 2025", "size": "xs", "color": COSMIC['text_muted'], "align": "center", "margin": "lg"}
            ],
            "paddingAll": "xl",
            "backgroundColor": COSMIC['bg_main']
        },
        "footer": {
            "type": "box",
            "layout": "horizontal",
            "contents": [
                {"type": "button", "action": {"type": "message", "label": "⚡ انضم", "text": "انضم"}, "style": "primary", "color": COSMIC['primary'], "height": "sm"},
                {"type": "button", "action": {"type": "message", "label": "📖 مساعدة", "text": "مساعدة"}, "style": "secondary", "height": "sm"}
            ],
            "spacing": "sm",
            "backgroundColor": COSMIC['bg_main'],
            "paddingAll": "lg"
        }
    }

def get_help_card():
    """بطاقة المساعدة - Cosmic Style"""
    return {
        "type": "bubble",
        "size": "mega",
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {"type": "text", "text": "📖 دليل الاستخدام", "size": "xxl", "weight": "bold", "color": COSMIC['text_main'], "align": "center"},
                {"type": "separator", "margin": "lg", "color": COSMIC['border']},
                {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                        {"type": "text", "text": "🎮 الأوامر الأساسية", "size": "md", "weight": "bold", "color": COSMIC['primary']},
                        {"type": "text", "text": "▫️ انضم - التسجيل في البوت\n▫️ انسحب - إلغاء التسجيل\n▫️ نقاطي - عرض إحصائياتك\n▫️ الصدارة - أفضل اللاعبين\n▫️ إيقاف - إنهاء اللعبة\n▫️ مساعدة - عرض هذا الدليل", "size": "sm", "color": COSMIC['text_secondary'], "wrap": True, "margin": "md"}
                    ],
                    "backgroundColor": COSMIC['bg_card'],
                    "cornerRadius": "16px",
                    "paddingAll": "lg",
                    "margin": "lg",
                    "borderWidth": "2px",
                    "borderColor": COSMIC['border']
                },
                {
                    "type": "box",
                    "layout": "
