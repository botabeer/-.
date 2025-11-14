"""
ملف التصاميم المنفصل - Flex Message Templates
تصاميم أنيقة بألوان محايدة (أبيض، أسود، رمادي)
"""

class FlexTemplates:
    """قوالب التصاميم الثابتة"""
    
    # الألوان الثابتة
    COLORS = {
        'primary': '#1a1a1a',      # أسود غامق
        'secondary': '#4a4a4a',    # رمادي غامق
        'light': '#f5f5f5',        # رمادي فاتح جداً
        'medium': '#9a9a9a',       # رمادي متوسط
        'text_dark': '#2a2a2a',    # نص أسود
        'text_light': '#6a6a6a',   # نص رمادي
        'white': '#ffffff',        # أبيض
        'border': '#e8e8e8',       # حدود فاتحة
        'background': '#f8f8f8'    # خلفية فاتحة
    }
    
    @staticmethod
    def get_winner_announcement(winner_name, game_type, total_score, questions_count=5, 
                               correct_answers=0, wrong_answers=0, time_taken=""):
        """
        إعلان الفائز بتصميم أنيق
        
        Args:
            winner_name: اسم الفائز
            game_type: نوع اللعبة
            total_score: مجموع النقاط
            questions_count: عدد الأسئلة
            correct_answers: الإجابات الصحيحة
            wrong_answers: الإجابات الخاطئة
            time_taken: الوقت المستغرق (اختياري)
        """
        colors = FlexTemplates.COLORS
        
        # حساب النسبة المئوية
        percentage = (correct_answers / questions_count * 100) if questions_count > 0 else 0
        
        # تحديد الميدالية حسب الأداء
        if percentage >= 90:
            medal = "🥇"
            performance = "ممتاز"
            perf_color = colors['primary']
        elif percentage >= 70:
            medal = "🥈"
            performance = "جيد جداً"
            perf_color = colors['secondary']
        elif percentage >= 50:
            medal = "🥉"
            performance = "جيد"
            perf_color = colors['text_light']
        else:
            medal = "⭐"
            performance = "مقبول"
            perf_color = colors['medium']
        
        flex_message = {
            "type": "bubble",
            "size": "mega",
            "header": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                            {
                                "type": "text",
                                "text": medal,
                                "size": "4xl",
                                "align": "center",
                                "color": colors['primary']
                            }
                        ],
                        "paddingAll": "md"
                    },
                    {
                        "type": "text",
                        "text": "🎉 تهانينا 🎉",
                        "weight": "bold",
                        "size": "xl",
                        "color": colors['primary'],
                        "align": "center",
                        "margin": "md"
                    },
                    {
                        "type": "text",
                        "text": winner_name,
                        "size": "lg",
                        "color": colors['text_dark'],
                        "align": "center",
                        "margin": "sm",
                        "weight": "bold"
                    }
                ],
                "backgroundColor": colors['white'],
                "paddingAll": "20px"
            },
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "text",
                        "text": f"لعبة {game_type}",
                        "size": "md",
                        "color": colors['text_light'],
                        "align": "center",
                        "weight": "bold"
                    },
                    {
                        "type": "separator",
                        "margin": "lg",
                        "color": colors['border']
                    },
                    # النقاط الكلية
                    {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                            {
                                "type": "text",
                                "text": "مجموع النقاط",
                                "size": "xs",
                                "color": colors['text_light'],
                                "align": "center"
                            },
                            {
                                "type": "text",
                                "text": str(total_score),
                                "size": "4xl",
                                "color": colors['primary'],
                                "align": "center",
                                "weight": "bold",
                                "margin": "xs"
                            }
                        ],
                        "margin": "lg",
                        "backgroundColor": colors['light'],
                        "cornerRadius": "md",
                        "paddingAll": "16px"
                    },
                    {
                        "type": "separator",
                        "margin": "lg",
                        "color": colors['border']
                    },
                    # الإحصائيات
                    {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                            {
                                "type": "text",
                                "text": "الإحصائيات",
                                "size": "sm",
                                "color": colors['text_dark'],
                                "weight": "bold",
                                "margin": "none"
                            },
                            # الأسئلة
                            {
                                "type": "box",
                                "layout": "horizontal",
                                "contents": [
                                    {
                                        "type": "text",
                                        "text": "عدد الأسئلة",
                                        "size": "sm",
                                        "color": colors['text_light'],
                                        "flex": 3
                                    },
                                    {
                                        "type": "text",
                                        "text": str(questions_count),
                                        "size": "sm",
                                        "color": colors['text_dark'],
                                        "flex": 1,
                                        "align": "end",
                                        "weight": "bold"
                                    }
                                ],
                                "margin": "md"
                            },
                            # الإجابات الصحيحة
                            {
                                "type": "box",
                                "layout": "horizontal",
                                "contents": [
                                    {
                                        "type": "text",
                                        "text": "✓ إجابات صحيحة",
                                        "size": "sm",
                                        "color": colors['text_light'],
                                        "flex": 3
                                    },
                                    {
                                        "type": "text",
                                        "text": str(correct_answers),
                                        "size": "sm",
                                        "color": colors['primary'],
                                        "flex": 1,
                                        "align": "end",
                                        "weight": "bold"
                                    }
                                ],
                                "margin": "sm"
                            },
                            # الإجابات الخاطئة
                            {
                                "type": "box",
                                "layout": "horizontal",
                                "contents": [
                                    {
                                        "type": "text",
                                        "text": "✗ إجابات خاطئة",
                                        "size": "sm",
                                        "color": colors['text_light'],
                                        "flex": 3
                                    },
                                    {
                                        "type": "text",
                                        "text": str(wrong_answers),
                                        "size": "sm",
                                        "color": colors['medium'],
                                        "flex": 1,
                                        "align": "end",
                                        "weight": "bold"
                                    }
                                ],
                                "margin": "sm"
                            },
                            # النسبة المئوية
                            {
                                "type": "box",
                                "layout": "horizontal",
                                "contents": [
                                    {
                                        "type": "text",
                                        "text": "نسبة النجاح",
                                        "size": "sm",
                                        "color": colors['text_light'],
                                        "flex": 3
                                    },
                                    {
                                        "type": "text",
                                        "text": f"{percentage:.0f}%",
                                        "size": "sm",
                                        "color": perf_color,
                                        "flex": 1,
                                        "align": "end",
                                        "weight": "bold"
                                    }
                                ],
                                "margin": "sm"
                            }
                        ],
                        "margin": "lg",
                        "spacing": "sm"
                    },
                    # الوقت (إن وُجد)
                    *([{
                        "type": "box",
                        "layout": "horizontal",
                        "contents": [
                            {
                                "type": "text",
                                "text": "⏱ الوقت المستغرق",
                                "size": "sm",
                                "color": colors['text_light'],
                                "flex": 3
                            },
                            {
                                "type": "text",
                                "text": time_taken,
                                "size": "sm",
                                "color": colors['text_dark'],
                                "flex": 2,
                                "align": "end",
                                "weight": "bold"
                            }
                        ],
                        "margin": "sm"
                    }] if time_taken else []),
                    # التقييم
                    {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                            {
                                "type": "text",
                                "text": performance,
                                "size": "lg",
                                "color": perf_color,
                                "align": "center",
                                "weight": "bold"
                            }
                        ],
                        "margin": "lg",
                        "backgroundColor": colors['light'],
                        "cornerRadius": "md",
                        "paddingAll": "12px"
                    }
                ],
                "backgroundColor": colors['white'],
                "paddingAll": "20px",
                "spacing": "none"
            },
            "footer": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "separator",
                        "color": colors['border']
                    },
                    {
                        "type": "box",
                        "layout": "horizontal",
                        "contents": [
                            {
                                "type": "button",
                                "action": {
                                    "type": "message",
                                    "label": "لعبة جديدة",
                                    "text": game_type
                                },
                                "style": "primary",
                                "color": colors['primary'],
                                "height": "sm"
                            },
                            {
                                "type": "button",
                                "action": {
                                    "type": "message",
                                    "label": "الصدارة",
                                    "text": "الصدارة"
                                },
                                "style": "secondary",
                                "height": "sm"
                            }
                        ],
                        "spacing": "sm",
                        "margin": "md"
                    },
                    {
                        "type": "text",
                        "text": "شكراً لمشاركتك!",
                        "size": "xs",
                        "color": colors['medium'],
                        "align": "center",
                        "margin": "md"
                    }
                ],
                "backgroundColor": colors['background'],
                "paddingAll": "16px"
            }
        }
        
        return flex_message
    
    @staticmethod
    def get_game_start(game_type, instructions, question_number=1, total_questions=5):
        """تصميم بداية اللعبة"""
        colors = FlexTemplates.COLORS
        
        return {
            "type": "bubble",
            "size": "mega",
            "header": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "text",
                        "text": f"🎮 {game_type}",
                        "weight": "bold",
                        "size": "xl",
                        "color": colors['primary'],
                        "align": "center"
                    },
                    {
                        "type": "box",
                        "layout": "horizontal",
                        "contents": [
                            {
                                "type": "text",
                                "text": f"السؤال {question_number}",
                                "size": "sm",
                                "color": colors['text_light'],
                                "flex": 1,
                                "align": "start"
                            },
                            {
                                "type": "text",
                                "text": f"{question_number}/{total_questions}",
                                "size": "sm",
                                "color": colors['text_dark'],
                                "flex": 0,
                                "align": "end",
                                "weight": "bold"
                            }
                        ],
                        "margin": "md"
                    }
                ],
                "backgroundColor": colors['white'],
                "paddingAll": "20px"
            },
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "text",
                        "text": instructions,
                        "size": "md",
                        "color": colors['text_dark'],
                        "wrap": True,
                        "align": "center"
                    }
                ],
                "backgroundColor": colors['light'],
                "paddingAll": "24px"
            }
        }
    
    @staticmethod
    def get_help_message():
        """رسالة المساعدة"""
        colors = FlexTemplates.COLORS
        
        return {
            "type": "bubble",
            "size": "mega",
            "header": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "text",
                        "text": "دليل الاستخدام",
                        "weight": "bold",
                        "size": "xxl",
                        "color": colors['primary'],
                        "align": "center"
                    }
                ],
                "backgroundColor": colors['white'],
                "paddingAll": "20px"
            },
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                            {
                                "type": "text",
                                "text": "الأوامر الأساسية",
                                "weight": "bold",
                                "size": "lg",
                                "color": colors['text_dark'],
                                "margin": "none"
                            },
                            {
                                "type": "separator",
                                "margin": "md",
                                "color": colors['border']
                            }
                        ],
                        "margin": "none",
                        "spacing": "sm"
                    },
                    {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                            FlexTemplates._create_command_row("انضم", "التسجيل في البوت", colors),
                            FlexTemplates._create_command_row("انسحب", "إلغاء التسجيل", colors),
                            FlexTemplates._create_command_row("نقاطي", "عرض إحصائياتك", colors),
                            FlexTemplates._create_command_row("الصدارة", "أفضل اللاعبين", colors),
                            FlexTemplates._create_command_row("إيقاف", "إنهاء اللعبة الحالية", colors)
                        ],
                        "spacing": "md",
                        "margin": "md"
                    },
                    {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                            {
                                "type": "text",
                                "text": "أثناء اللعب",
                                "weight": "bold",
                                "size": "lg",
                                "color": colors['text_dark'],
                                "margin": "none"
                            },
                            {
                                "type": "separator",
                                "margin": "md",
                                "color": colors['border']
                            }
                        ],
                        "margin": "xl",
                        "spacing": "sm"
                    },
                    {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                            FlexTemplates._create_command_row("لمح", "الحصول على تلميح", colors),
                            FlexTemplates._create_command_row("جاوب", "عرض الإجابة الصحيحة", colors)
                        ],
                        "spacing": "md",
                        "margin": "md"
                    },
                    {
                        "type": "text",
                        "text": "💡 كل لعبة تحتوي على 5 أسئلة",
                        "size": "xs",
                        "color": colors['medium'],
                        "align": "center",
                        "margin": "xl",
                        "wrap": True
                    }
                ],
                "spacing": "md",
                "backgroundColor": colors['white'],
                "paddingAll": "20px"
            },
            "footer": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "separator",
                        "color": colors['border']
                    },
                    {
                        "type": "box",
                        "layout": "horizontal",
                        "contents": [
                            {
                                "type": "button",
                                "action": {
                                    "type": "message",
                                    "label": "انضم",
                                    "text": "انضم"
                                },
                                "style": "primary",
                                "color": colors['primary'],
                                "height": "sm"
                            },
                            {
                                "type": "button",
                                "action": {
                                    "type": "message",
                                    "label": "نقاطي",
                                    "text": "نقاطي"
                                },
                                "style": "secondary",
                                "height": "sm"
                            }
                        ],
                        "spacing": "sm",
                        "margin": "md"
                    }
                ],
                "backgroundColor": colors['background'],
                "paddingAll": "16px"
            }
        }
    
    @staticmethod
    def _create_command_row(command, description, colors):
        """إنشاء صف الأمر"""
        return {
            "type": "box",
            "layout": "horizontal",
            "contents": [
                {
                    "type": "text",
                    "text": command,
                    "size": "sm",
                    "color": colors['primary'],
                    "flex": 2,
                    "weight": "bold"
                },
                {
                    "type": "text",
                    "text": description,
                    "size": "sm",
                    "color": colors['text_light'],
                    "flex": 5,
                    "wrap": True
                }
            ],
            "spacing": "md"
        }
    
    @staticmethod
    def get_progress_bar(current, total):
        """شريط التقدم"""
        colors = FlexTemplates.COLORS
        filled = int((current / total) * 10)
        empty = 10 - filled
        bar = "█" * filled + "░" * empty
        
        return {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "box",
                    "layout": "horizontal",
                    "contents": [
                        {
                            "type": "text",
                            "text": f"السؤال {current} من {total}",
                            "size": "xs",
                            "color": colors['text_light'],
                            "flex": 1
                        },
                        {
                            "type": "text",
                            "text": f"{int(current/total*100)}%",
                            "size": "xs",
                            "color": colors['text_dark'],
                            "align": "end",
                            "weight": "bold",
                            "flex": 0
                        }
                    ]
                },
                {
                    "type": "text",
                    "text": bar,
                    "size": "sm",
                    "color": colors['secondary'],
                    "margin": "sm"
                }
            ]
        }
    
    @staticmethod
    def get_welcome_message(display_name):
        """رسالة الترحيب"""
        colors = FlexTemplates.COLORS
        
        return {
            "type": "bubble",
            "size": "mega",
            "header": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "text",
                        "text": "منصة الألعاب",
                        "weight": "bold",
                        "size": "xxl",
                        "color": colors['primary'],
                        "align": "center"
                    },
                    {
                        "type": "text",
                        "text": f"مرحباً {display_name}",
                        "size": "md",
                        "color": colors['text_light'],
                        "align": "center",
                        "margin": "sm"
                    }
                ],
                "backgroundColor": colors['white'],
                "paddingAll": "24px"
            },
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                            {
                                "type": "text",
                                "text": "خطوات البدء",
                                "weight": "bold",
                                "size": "md",
                                "color": colors['text_dark']
                            },
                            {
                                "type": "separator",
                                "margin": "md",
                                "color": colors['border']
                            }
                        ],
                        "spacing": "sm"
                    },
                    {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                            FlexTemplates._create_step_box("1", "اضغط على زر انضم للتسجيل", colors, True),
                            FlexTemplates._create_step_box("2", "اختر لعبة من الأزرار أدناه", colors, False),
                            FlexTemplates._create_step_box("3", "ابدأ اللعب واجمع النقاط (5 أسئلة لكل لعبة)", colors, False)
                        ],
                        "margin": "md"
                    },
                    {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                            {
                                "type": "text",
                                "text": "15 لعبة متاحة",
                                "size": "xs",
                                "color": colors['medium'],
                                "align": "center"
                            },
                            {
                                "type": "text",
                                "text": "إجاباتك تُحسب تلقائياً بعد التسجيل",
                                "size": "xs",
                                "color": colors['medium'],
                                "align": "center",
                                "margin": "xs"
                            }
                        ],
                        "margin": "lg"
                    }
                ],
                "backgroundColor": colors['white'],
                "paddingAll": "20px"
            },
            "footer": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "separator",
                        "color": colors['border']
                    },
                    {
                        "type": "box",
                        "layout": "horizontal",
                        "contents": [
                            {
                                "type": "button",
                                "action": {
                                    "type": "message",
                                    "label": "انضم",
                                    "text": "انضم"
                                },
                                "style": "primary",
                                "color": colors['primary'],
                                "height": "sm"
                            },
                            {
                                "type": "button",
                                "action": {
                                    "type": "message",
                                    "label": "مساعدة",
                                    "text": "مساعدة"
                                },
                                "style": "secondary",
                                "height": "sm"
                            }
                        ],
                        "spacing": "sm",
                        "margin": "md"
                    }
                ],
                "backgroundColor": colors['background'],
                "paddingAll": "16px"
            }
        }
    
    @staticmethod
    def get_join_success(display_name):
        """رسالة نجاح التسجيل"""
        colors = FlexTemplates.COLORS
        
        return {
            "type": "bubble",
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "text",
                        "text": "✅",
                        "size": "4xl",
                        "align": "center",
                        "color": colors['primary']
                    },
                    {
                        "type": "text",
                        "text": "تم التسجيل بنجاح",
                        "weight": "bold",
                        "size": "xl",
                        "color": colors['primary'],
                        "align": "center",
                        "margin": "md"
                    },
                    {
                        "type": "text",
                        "text": f"مرحباً بك {display_name}",
                        "size": "md",
                        "color": colors['text_light'],
                        "align": "center",
                        "margin": "md"
                    },
                    {
                        "type": "separator",
                        "margin": "xl",
                        "color": colors['border']
                    },
                    {
                        "type": "text",
                        "text": "يمكنك الآن اللعب في جميع الألعاب\n\nإجاباتك ستُحسب تلقائياً",
                        "size": "sm",
                        "color": colors['text_dark'],
                        "align": "center",
                        "wrap": True,
                        "margin": "xl"
                    }
                ],
                "backgroundColor": colors['white'],
                "paddingAll": "28px"
            }
        }
    
    @staticmethod
    def get_user_stats(display_name, is_registered, total_points, games_played, wins):
        """إحصائيات المستخدم"""
        colors = FlexTemplates.COLORS
        
        status = "مسجل" if is_registered else "غير مسجل"
        status_color = colors['primary'] if is_registered else colors['medium']
        win_rate = (wins / games_played * 100) if games_played > 0 else 0
        
        return {
            "type": "bubble",
            "size": "mega",
            "header": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "text",
                        "text": "إحصائياتك",
                        "weight": "bold",
                        "size": "xl",
                        "color": colors['primary'],
                        "align": "center"
                    },
                    {
                        "type": "text",
                        "text": display_name,
                        "size": "sm",
                        "color": colors['text_light'],
                        "align": "center",
                        "margin": "sm"
                    }
                ],
                "backgroundColor": colors['white'],
                "paddingAll": "20px"
            },
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "box",
                        "layout": "horizontal",
                        "contents": [
                            {
                                "type": "text",
                                "text": "الحالة",
                                "size": "sm",
                                "color": colors['text_light'],
                                "flex": 2
                            },
                            {
                                "type": "text",
                                "text": status,
                                "size": "sm",
                                "color": status_color,
                                "flex": 3,
                                "align": "end",
                                "weight": "bold"
                            }
                        ]
                    },
                    {
                        "type": "separator",
                        "margin": "md",
                        "color": colors['border']
                    },
                    {
                        "type": "box",
                        "layout": "horizontal",
                        "contents": [
                            {
                                "type": "text",
                                "text": "النقاط",
                                "size": "sm",
                                "color": colors['text_light'],
                                "flex": 2
                            },
                            {
                                "type": "text",
                                "text": str(total_points),
                                "size": "xl",
                                "color": colors['primary'],
                                "flex": 3,
                                "align": "end",
                                "weight": "bold"
                            }
                        ],
                        "margin": "md"
                    },
                    {
                        "type": "separator",
                        "margin": "md",
                        "color": colors['border']
                    },
                    {
                        "type": "box",
                        "layout": "horizontal",
                        "contents": [
                            {
                                "type": "text",
                                "text": "الألعاب",
                                "size": "sm",
                                "color": colors['text_light'],
                                "flex": 2
                            },
                            {
                                "type": "text",
                                "text": str(games_played),
                                "size": "sm",
                                "color": colors['text_dark'],
                                "flex": 3,
                                "align": "end",
                                "weight": "bold"
                            }
                        ],
                        "margin": "md"
                    },
                    {
                        "type": "box",
                        "layout": "horizontal",
                        "contents": [
                            {
                                "type": "text",
                                "text": "الفوز",
                                "size": "sm",
                                "color": colors['text_light'],
                                "flex": 2
                            },
                            {
                                "type": "text",
                                "text": str(wins),
                                "size": "sm",
                                "color": colors['text_dark'],
                                "flex": 3,
                                "align": "end",
                                "weight": "bold"
                            }
                        ],
                        "margin": "sm"
                    },
                    {
                        "type": "box",
                        "layout": "horizontal",
                        "contents": [
                            {
                                "type": "text",
                                "text": "نسبة الفوز",
                                "size": "sm",
                                "color": colors['text_light'],
                                "flex": 2
                            },
                            {
                                "type": "text",
                                "text": f"{win_rate:.1f}%",
                                "size": "sm",
                                "color": colors['text_dark'],
                                "flex": 3,
                                "align": "end",
                                "weight": "bold"
                            }
                        ],
                        "margin": "sm"
                    }
                ],
                "backgroundColor": colors['white'],
                "paddingAll": "20px"
            },
            "footer": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "separator",
                        "color": colors['border']
                    },
                    {
                        "type": "button",
                        "action": {
                            "type": "message",
                            "label": "الصدارة",
                            "text": "الصدارة"
                        },
                        "style": "secondary",
                        "height": "sm",
                        "margin": "md"
                    }
                ],
                "backgroundColor": colors['background'],
                "paddingAll": "16px"
            }
        }
    
    @staticmethod
    def get_leaderboard(leaders):
        """لوحة الصدارة"""
        colors = FlexTemplates.COLORS
        
        players_list = []
        for i, leader in enumerate(leaders, 1):
            if i <= 3:
                rank_bg = colors['secondary']
                rank_color = colors['white']
                name_color = colors['white']
            else:
                rank_bg = colors['light']
                rank_color = colors['text_dark']
                name_color = colors['text_dark']
            
            player_box = {
                "type": "box",
                "layout": "horizontal",
                "contents": [
                    {
                        "type": "text",
                        "text": str(i),
                        "size": "sm",
                        "color": rank_color,
                        "align": "center",
                        "weight": "bold",
                        "flex": 0
                    },
                    {
                        "type": "text",
                        "text": leader['display_name'],
                        "size": "sm",
                        "color": name_color,
                        "flex": 3,
                        "margin": "md",
                        "weight": "bold" if i <= 3 else "regular"
                    },
                    {
                        "type": "text",
                        "text": str(leader['total_points']),
                        "size": "sm",
                        "color": name_color,
                        "flex": 1,
                        "align": "end",
                        "weight": "bold" if i <= 3 else "regular"
                    }
                ],
                "backgroundColor": rank_bg,
                "cornerRadius": "md",
                "paddingAll": "12px",
                "spacing": "md",
                "margin": "xs" if i > 1 else "none"
            }
            players_list.append(player_box)
        
        return {
            "type": "bubble",
            "size": "mega",
            "header": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "text",
                        "text": "🏆 لوحة الصدارة",
                        "weight": "bold",
                        "size": "xl",
                        "color": colors['primary'],
                        "align": "center"
                    },
                    {
                        "type": "text",
                        "text": "أفضل اللاعبين",
                        "size": "sm",
                        "color": colors['text_light'],
                        "align": "center",
                        "margin": "sm"
                    }
                ],
                "backgroundColor": colors['white'],
                "paddingAll": "20px"
            },
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": players_list,
                "backgroundColor": colors['white'],
                "paddingAll": "20px"
            },
            "footer": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "separator",
                        "color": colors['border']
                    },
                    {
                        "type": "button",
                        "action": {
                            "type": "message",
                            "label": "نقاطي",
                            "text": "نقاطي"
                        },
                        "style": "secondary",
                        "height": "sm",
                        "margin": "md"
                    }
                ],
                "backgroundColor": colors['background'],
                "paddingAll": "16px"
            }
        }
    
    @staticmethod
    def _create_step_box(number, text, colors, is_first=False):
        """إنشاء صندوق خطوة"""
        bg = colors['primary'] if is_first else colors['light']
        text_color = colors['white'] if is_first else colors['text_dark']
        num_color = colors['white'] if is_first else colors['primary']
        
        return {
            "type": "box",
            "layout": "horizontal",
            "contents": [
                {
                    "type": "text",
                    "text": number,
                    "size": "sm",
                    "color": num_color,
                    "align": "center",
                    "weight": "bold",
                    "flex": 0
                },
                {
                    "type": "text",
                    "text": text,
                    "size": "sm",
                    "color": text_color,
                    "flex": 1,
                    "margin": "md",
                    "wrap": True
                }
            ],
            "backgroundColor": bg,
            "cornerRadius": "md",
            "paddingAll": "12px",
            "spacing": "md",
            "margin": "sm" if not is_first else "none"
        }
