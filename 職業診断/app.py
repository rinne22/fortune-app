import streamlit as st
import google.generativeai as genai
import time
import base64
import os
import plotly.graph_objects as go
import json
import io

# --- PDF生成用ライブラリ ---
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# --- 設定: Geminiモデル ---
MODEL_NAME = "gemini-2.5-flash"

# --- ページ設定 ---
st.set_page_config(
    page_title="AI適職占いの館",
    page_icon="🔮",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- 定数・アセット定義 ---
URL_BG_DEFAULT = 'https://images.unsplash.com/photo-1560183441-6333262aa22c?q=80&w=2070&auto=format&fit=crop&v=force_reload_new'
URL_FRAME_GOLD = 'https://www.transparenttextures.com/patterns/always-grey.png'
URL_AGED_PAPER = 'https://www.transparenttextures.com/patterns/aged-paper.png'

# 質問データ
QUESTIONS = [
    {"id": "q1", "q": "I. 魂の渇望 - 仕事で最も得たい報酬は？", "options": {"💰 圧倒的な成果と地位（昇進・独立）": "fire", "🧠 新しい知識と専門性（スキルアップ）": "water", "🤝 仲間との信頼と感謝（チームワーク）": "wind"}},
    {"id": "q2", "q": "II. 魔力の源泉 - チーム内での役割は？", "options": {"🔥 皆を引っ張るリーダー（方針決定）": "fire", "💧 冷静な参謀・分析役（課題発見）": "water", "🌿 相談役・ムードメーカー（環境調整）": "wind"}},
    {"id": "q3", "q": "III. 冒険の指針 - 新規プロジェクト、どう進める？", "options": {"⚔️ 「まずはやってみよう」と行動開始": "fire", "🗺️ 「成功確率は？」とデータを収集": "water", "🛡️ 「みんなの意見は？」と合意形成": "wind"}},
    {"id": "q4", "q": "IV. 求める秘宝 - 理想の職場環境は？", "options": {"👑 実力主義で競争がある環境": "fire", "📜 静かで作業に没頭できる環境": "water", "🕊️ アットホームで協力的な環境": "wind"}},
    {"id": "q5", "q": "V. 試練の刻 - トラブル発生！どう動く？", "options": {"⚡️ 自分が先頭に立って解決に走る": "fire", "🔍 原因を根本から論理的に突き止める": "water", "📣 関係各所に連絡し、被害を最小限にする": "wind"}},
    {"id": "q6", "q": "VI. 交信の作法 - プレゼンで重視することは？", "options": {"🔥 熱意とビジョンを伝えること": "fire", "💧 正確なデータと根拠を示すこと": "water", "🌿 相手の感情やニーズに寄り添うこと": "wind"}},
    {"id": "q7", "q": "VII. 失敗の代償 - ミスをした時、どう思う？", "options": {"🔥 「次は絶対成功させる」と燃える": "fire", "💧 「なぜ起きたか」プロセスを見直す": "water", "🌿 「周りに迷惑をかけた」と反省する": "wind"}},
    {"id": "q8", "q": "VIII. 究極スキル - 今一番欲しい能力は？", "options": {"🔥 人を動かす影響力・交渉力": "fire", "💧 物事の本質を見抜く分析力": "water", "🌿 誰とでも仲良くなれる対人力": "wind"}},
    {"id": "q9", "q": "IX. 安息の地 - 休暇の過ごし方は？", "options": {"🔥 アクティブに新しい体験をする": "fire", "💧 読書や学習で知見を広める": "water", "🌿 友人や家族とゆっくり過ごす": "wind"}},
    {"id": "q10", "q": "X. 伝説の終わり - 引退時、どう言われたい？", "options": {"🔥 「彼/彼女が業界を変えた」": "fire", "💧 「彼/彼女の仕事は完璧だった」": "water", "🌿 「彼/彼女がいてくれて良かった」": "wind"}},
]

# --- ヘルパー関数群 ---

def get_api_key():
    if "GEMINI_API_KEY" in st.secrets:
        return st.secrets["GEMINI_API_KEY"]
    else:
        with st.sidebar:
            st.warning("⚠️ APIキーが設定されていません")
            val = st.text_input("Gemini APIキーを入力", type="password")
            if val: return val
        return None

def get_base64_of_bin_file(bin_file):
    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(base_dir, bin_file)
        if not os.path.exists(file_path):
            return None
        with open(file_path, 'rb') as f:
            data = f.read()
        return base64.b64encode(data).decode()
    except Exception:
        return None

def apply_custom_css(bg_image_url):
    st.markdown(f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@700&family=Shippori+Mincho+B1:wght@400;700;900&display=swap');
        
        /* 不要な要素を隠す */
        #MainMenu, footer, header, [data-testid="stToolbar"], .stDeployButton {{ visibility: hidden; display: none; }}
        
        /* 全体の余白調整 */
        .block-container {{ 
            padding-top: 2rem !important; 
            padding-bottom: 150px !important; /* 入力欄のために下を空ける */
        }}

        /* 背景画像の設定 */
        .stApp {{
            background-color: #050510; 
            background-image: {bg_image_url} !important;
            background-size: cover !important;
            background-repeat: no-repeat !important;
            background-attachment: fixed !important;
            background-position: center center !important;
        }}
        /* 背景を少し暗くするオーバーレイ */
        .stApp::before {{
            content: ""; position: fixed; top: 0; left: 0; width: 100%; height: 100%;
            background: rgba(0, 0, 0, 0.6); z-index: -1; pointer-events: none;
        }}
        
        /* --- テキストの装飾 --- */
        h1, h2, h3, h4, p, div, span, label, li {{
            color: #E0E0E0 !important;
            font-family: 'Shippori Mincho B1', serif;
            letter-spacing: 0.05em;
        }}
        .main-title {{
            font-family: 'Cinzel', serif !important;
            color: #FFD700 !important;
            text-shadow: 0 0 10px #FFD700, 0 0 20px #FFD700;
            font-size: 4rem !important; text-align: center;
            margin-top: 5vh !important;
        }}
        .intro-text {{
            font-size: 1.2rem; line-height: 2.0; text-align: center; color: #FFD700; font-weight: bold;
            text-shadow: 2px 2px 4px #000;
            background: rgba(0,0,0,0.5); padding: 20px; border-radius: 15px;
        }}

        /* --- チャット入力欄の劇的改善 --- */
        /* 下部の固定エリアを透明にする */
        [data-testid="stBottom"] {{
            background-color: transparent !important;
            background-image: linear-gradient(to top, #000000, rgba(0,0,0,0)); /* 下から黒くフェード */
            padding-bottom: 20px;
        }}
        
        /* 入力ボックス自体のデザイン */
        .stChatInput textarea {{
            background-color: rgba(20, 20, 35, 0.9) !important; /* 暗い紫紺色 */
            color: #FFD700 !important; /* 金色の文字 */
            border: 1px solid rgba(255, 215, 0, 0.5) !important; /* 金色の枠線 */
            border-radius: 20px !important;
        }}
        /* 送信ボタンの色 */
        [data-testid="stChatInputSubmitButton"] {{
            color: #FFD700 !important;
        }}

        /* --- チャット吹き出しのデザイン --- */
        .stChatMessage {{
            background-color: rgba(10, 10, 20, 0.85) !important; /* 半透明の黒 */
            border: 1px solid rgba(255, 215, 0, 0.3) !important;
            border-radius: 15px !important;
            padding: 10px !important;
            margin-bottom: 10px !important;
            box-shadow: 0 4px 6px rgba(0,0,0,0.3);
        }}
        /* ユーザーのアイコン背景 */
        [data-testid="stChatMessageAvatarUser"] {{
            background-color: #333 !important;
        }}
        /* AIのアイコン背景 */
        [data-testid="stChatMessageAvatarAssistant"] {{
            background-color: #220044 !important;
        }}

        /* --- ボタン共通デザイン --- */
        .stButton button, div[data-testid="stDownloadButton"] button {{
            width: 100%;
            background: linear-gradient(45deg, #FFD700, #DAA520) !important;
            color: #000 !important;
            border: none !important;
            border-radius: 30px !important;
            font-family: 'Cinzel', serif !important;
            font-weight: bold !important;
            padding: 12px 24px !important;
            box-shadow: 0 0 15px rgba(255, 215, 0, 0.4) !important;
            transition: all 0.3s;
        }}
        .stButton button:hover, div[data-testid="stDownloadButton"] button:hover {{
            transform: scale(1.02) !important;
            box-shadow: 0 0 25px rgba(255, 215, 0, 0.8) !important;
        }}
        /* ダウンロードボタンの文字色強制 */
        div[data-testid="stDownloadButton"] button * {{
            color: #000000 !important;
        }}

        /* --- ラジオボタンの選択肢 --- */
        div[role="radiogroup"] label {{
            background: rgba(30, 30, 50, 0.8) !important;
            border: 1px solid rgba(255, 255, 255, 0.2);
            padding: 15px; border-radius: 10px; margin-bottom: 10px;
            transition: 0.3s;
        }}
        div[role="radiogroup"] label:hover {{
            border-color: #FFD700; background: rgba(50, 40, 80, 0.9) !important;
        }}

        /* --- 診断結果カード --- */
        .tarot-card-outer {{
            padding: 5px;
            background: linear-gradient(135deg, #BF953F, #FCF6BA, #B38728, #FBF5B7);
            border-radius: 20px;
            box-shadow: 0 0 30px rgba(255, 215, 0, 0.3);
            margin: 0 auto; max-width: 600px;
        }}
        .tarot-card-inner {{
            background: #1a0f2e;
            border-radius: 15px; padding: 30px; text-align: center;
        }}
        .advice-box {{
            background: rgba(255, 248, 220, 0.9);
            border: 3px double #8B4513;
            border-radius: 10px; padding: 25px; margin-top: 30px;
            color: #3E2723 !important;
        }}
        .advice-box * {{ color: #3E2723 !important; }}
    </style>
    """, unsafe_allow_html=True)

# --- PDF生成用関数 ---
def create_pdf(user_type, title, skills, jobs, advice):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer)
    try:
        font_path = "C:\\Windows\\Fonts\\msgothic.ttc"
        pdfmetrics.registerFont(TTFont('Gothic', font_path))
        font_name = 'Gothic'
    except:
        font_name = 'Helvetica'

    c.setFont(font_name, 24)
    c.drawString(50, 800, "THE FORTUNE CAREER - 鑑定書")
    c.setFont(font_name, 12)
    c.drawString(400, 820, f"Date: {time.strftime('%Y/%m/%d')}")
    c.line(50, 780, 550, 780)
    c.setFont(font_name, 18)
    c.drawString(50, 730, f"あなたの属性: {title} ({user_type})")
    c.setFont(font_name, 14)
    c.drawString(50, 680, "【獲得したスキル】")
    skills_text = " / ".join(skills) if isinstance(skills, list) else str(skills)
    c.drawString(70, 660, skills_text)
    c.drawString(50, 620, "【運命の適職】")
    jobs_text = " / ".join(jobs) if isinstance(jobs, list) else str(jobs)
    c.drawString(70, 600, jobs_text)
    c.drawString(50, 550, "【賢者からの助言】")
    
    c.setFont(font_name, 10)
    y_pos = 530
    clean_advice = advice.replace("**", "").replace("\n", "") 
    for i in range(0, len(clean_advice), 35):
        line = clean_advice[i:i+35]
        c.drawString(60, y_pos, line)
        y_pos -= 15
        if y_pos < 50: break

    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer

# --- ロジック関数 ---
def calculate_type():
    scores = {"fire": 0, "water": 0, "wind": 0}
    for q_id, selected_label in st.session_state.answers.items():
        for q in QUESTIONS:
            if q["id"] == q_id:
                attr = q["options"][selected_label]
                scores[attr] += 1
                break
    
    sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    first_attr, first_score = sorted_scores[0]
    second_attr, second_score = sorted_scores[1]
    
    res_type = first_attr if (first_score - second_score >= 2) else "-".join(sorted([first_attr, second_attr]))
    return res_type, first_attr

def get_gemini_response(prompt, api_key):
    if not api_key: return "⚠️ APIキーが設定されていません。"
    genai.configure(api_key=api_key)
    max_retries = 3
    for attempt in range(max_retries):
        try:
            model = genai.GenerativeModel(MODEL_NAME)
            formatted_history = []
            for msg in st.session_state.chat_history:
                role = "user" if msg["role"] == "user" else "model"
                formatted_history.append({"role": role, "parts": [msg["content"]]})
            
            chat = model.start_chat(history=formatted_history)
            response = chat.send_message(prompt)
            return response.text
        except Exception as e:
            error_str = str(e)
            if "429" in error_str or "quota" in error_str.lower():
                return "申し訳ございません。現在、星々の声が届きにくくなっております（アクセス集中による制限）。\n少し時間を置いてから、もう一度お試しください。"
            if attempt < max_retries - 1: time.sleep(2); continue
            else: return f"精霊との交信が途絶えました... (Error: {error_str})"

# --- メイン処理 ---
def main():
    if "step" not in st.session_state: st.session_state.step = 0
    if "answers" not in st.session_state: st.session_state.answers = {}
    if "chat_history" not in st.session_state: st.session_state.chat_history = []
    if "final_advice" not in st.session_state: st.session_state.final_advice = ""
    if "dynamic_result" not in st.session_state: st.session_state.dynamic_result = None

    api_key = get_api_key()
    
    bg_mansion_base64 = get_base64_of_bin_file("mansion.jpg")
    bg_room_base64 = get_base64_of_bin_file("room.jpg")
    
    bg_css_url = f"url('{URL_BG_DEFAULT}')"
    if st.session_state.step == 0 and bg_mansion_base64:
        bg_css_url = f"url('data:image/jpeg;base64,{bg_mansion_base64}')"
    elif bg_room_base64:
        bg_css_url = f"url('data:image/jpeg;base64,{bg_room_base64}')"
    
    apply_custom_css(bg_css_url)

    # STEP 0: トップページ
    if st.session_state.step == 0:
        st.markdown("""
        <div style="text-align: center;">
            <h1 class="main-title">FORTUNE CAREER</h1>
            <p style='letter-spacing: 0.5em; color: #FFD700; font-size: 1.2em; margin-top: 10px; font-weight:bold; text-shadow: 2px 2px 4px #000;'>AI 適職占いの館</p>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1,2,1]) 
        with col2:
            st.markdown("""
            <div class="intro-text">
                ようこそ、迷える魂よ。<br>
                ここは星々の導きと、ビジネスの叡智が交わる場所。<br>
                あなたの真の才能と、現代における天職を紐解いて進ぜよう。
            </div>
            """, unsafe_allow_html=True)
            if st.button("🚪 運命の扉を開く"):
                if not api_key: st.error("⚠️ APIキーを設定してください")
                else: st.session_state.step = 1; st.rerun()

    # STEP 1: 質問フォーム
    elif st.session_state.step == 1:
        st.markdown("<h1 class='main-title' style='margin-top:20px !important;'>The 10 Prophecies</h1>", unsafe_allow_html=True)
        col_main1, col_main2, col_main3 = st.columns([1, 3, 1])
        with col_main2:
            st.markdown("""
            <div style="text-align: center; margin-bottom: 30px;">
                <p style="margin-top: 20px; font-style: italic; font-size: 1.5em; color: #FFD700; font-weight: 900; text-shadow: 2px 2px 0px #000;">
                    「そなたの仕事観について、10の問いに答えよ…」
                </p>
            </div>
            """, unsafe_allow_html=True)
            with st.form("questions_form"):
                for q_data in QUESTIONS:
                    st.markdown(f"<h3 style='color:#FFD700; text-shadow: 2px 2px 4px #000; font-size:1.4em;'>{q_data['q']}</h3>", unsafe_allow_html=True)
                    choice = st.radio("選択肢", list(q_data['options'].keys()), key=q_data['id'], label_visibility="collapsed", index=None)
                    if choice: st.session_state.answers[q_data['id']] = choice
                    st.markdown("<hr style='border-color: rgba(255,215,0,0.3); margin: 30px 0;'>", unsafe_allow_html=True)
                if st.form_submit_button("🔮 真実を明らかにする"):
                    if len(st.session_state.answers) < len(QUESTIONS) or any(v is None for v in st.session_state.answers.values()):
                        st.error("まだ答えられていない予言があります。")
                    else: st.session_state.step = 2; st.rerun()

    # STEP 2: チャット
    elif st.session_state.step == 2:
        st.markdown("<h1 class='main-title' style='margin-top:20px !important;'>Talk with Spirits</h1>", unsafe_allow_html=True)
        if not st.session_state.chat_history:
            res_type, main_attr = calculate_type()
            system_prompt = f"""
            あなたは「運命の館」の占い師であり、優秀なキャリアコンサルタントです。
            ユーザーの属性は「{main_attr}」({res_type})です。
            口調は「神秘的な占い師（〜じゃ、そなたは〜）」ですが、中身は「具体的で深いキャリアヒアリング」を行ってください。
            
            【重要：対話のルール】
            ・**一方的に質問を投げつけないでください。**
            ・ユーザーが回答したら、まずその内容に対して共感・リアクションを示してください。
            
            【進行手順】
            1. **【重要】冒頭の提案**: まず、診断された属性「{main_attr}」から読み取れる**「ユーザーの才能や適職の仮説（提案）」**を提示してください。
            2. その提案に対し、ユーザーがどう思うか、実際の経験と照らし合わせてどう感じるかを問いかけてください。
            3. その後、ユーザーの反応に合わせて深掘りし、合計**4往復**ほど会話を続けてください。
            4. 十分な情報が集まったら、「では、運命の書に記された結果を見るがよい...」と締めくくってください。
            """
            with st.spinner("キャリアガイドと通信中..."):
                initial_response = get_gemini_response(system_prompt, api_key)
                st.session_state.chat_history.append({"role": "assistant", "content": initial_response})
                st.rerun()

        col_chat1, col_chat2, col_chat3 = st.columns([1, 3, 1])
        with col_chat2:
            for msg in st.session_state.chat_history:
                role_icon = "🔮" if msg["role"] == "assistant" else "👤"
                with st.chat_message(msg["role"], avatar=role_icon):
                    st.write(msg["content"])
        
        # 入力欄を下に固定
        prompt = st.chat_input("回答を入力...")
        if prompt:
            st.session_state.chat_history.append({"role": "user", "content": prompt})
            
            final_instruction = ""
            current_user_count = len([m for m in st.session_state.chat_history if m["role"] == "user"])
            if current_user_count >= 4:
                final_instruction = " (※システム指示: ヒアリング終了です。これ以上質問せず、「では、運命の書に記された結果を見るがよい...」と伝え、会話を締めてください。)"
            else:
                final_instruction = " (※システム指示: 必ずユーザーの回答に「共感」や「感想」を述べてから、次の質問や話題へ自然に繋げてください。)"
            
            with st.spinner("..."):
                ai_res = get_gemini_response(prompt + final_instruction, api_key)
            st.session_state.chat_history.append({"role": "assistant", "content": ai_res})
            st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("📜 運命の書を開く（診断結果へ）"):
            st.session_state.step = 3
            st.rerun()

    # STEP 3: 診断結果
    elif st.session_state.step == 3:
        st.balloons()
        st.markdown("<h1 class='main-title' style='margin-top:20px !important; font-size: 6rem !important;'>✨ Your Destiny Card ✨</h1>", unsafe_allow_html=True)
        
        res_type, _ = calculate_type()
        
        type_info = {
            "fire": {"title": "開拓の騎士", "sub": "THE LEADER", "file": "icon_fire.jpg", "ph": "https://placehold.co/400x400/201335/FFD700?text=Leader"},
            "water": {"title": "叡智の賢者", "sub": "THE ENGINEER", "file": "icon_water.jpg", "ph": "https://placehold.co/400x400/201335/FFD700?text=Wizard"},
            "wind": {"title": "調和の精霊", "sub": "THE HEALER", "file": "icon_wind.jpg", "ph": "https://placehold.co/400x400/201335/FFD700?text=Healer"},
            "fire-water": {"title": "蒼炎の軍師", "sub": "THE STRATEGIST", "file": "icon_fire_water.jpg", "ph": "https://placehold.co/400x400/201335/FFD700?text=Strategist"},
            "fire-wind": {"title": "陽光の詩人", "sub": "THE ARTIST", "file": "icon_fire_wind.jpg", "ph": "https://placehold.co/400x400/201335/FFD700?text=Artist"},
            "water-wind": {"title": "星詠みの司書", "sub": "THE GUIDE", "file": "icon_water_wind.jpg", "ph": "https://placehold.co/400x400/201335/FFD700?text=Guide"},
        }
        base_data = type_info.get(res_type, type_info["fire"])

        if not st.session_state.dynamic_result:
            with st.spinner("精霊たちが会話の記憶から、あなたの真の能力を紡ぎ出しています..."):
                genai.configure(api_key=api_key)
                model = genai.GenerativeModel(MODEL_NAME)
                
                formatted_history = []
                for msg in st.session_state.chat_history:
                      role = "user" if msg["role"] == "user" else "model"
                      formatted_history.append({"role": role, "parts": [msg["content"]]})

                analysis_prompt = f"""
                あなたは優秀なキャリア分析官です。
                以下の「ユーザーとの会話履歴」と「基本タイプ」に基づき、このユーザーに**本当にマッチする**以下の要素を推測してください。
                会話でユーザーが語った具体的な経験や好みを必ず反映させてください。
                
                診断された基本タイプ: {base_data['title']} ({res_type})
                
                出力は以下のJSONフォーマットのみで行ってください:
                {{
                    "skills": ["スキル1", "スキル2", "スキル3"],
                    "jobs": ["適職1", "適職2", "適職3"],
                    "desc": "ユーザーの特性を表す、短く神秘的かつ本質的な紹介文（50文字以内）"
                }}
                """
                try:
                    chat_text = "\n".join([f"{msg['role']}: {msg['content']}" for msg in st.session_state.chat_history])
                    full_prompt = analysis_prompt + "\n\n【会話履歴】\n" + chat_text
                    
                    response = model.generate_content(full_prompt)
                    text = response.text.strip()
                    if text.startswith("```json"): text = text[7:]
                    if text.endswith("```"): text = text[:-3]
                    
                    st.session_state.dynamic_result = json.loads(text)
                except Exception as e:
                    st.session_state.dynamic_result = {
                        "skills": ["潜在能力", "未知の可能性"],
                        "jobs": ["冒険者", "自由業"],
                        "desc": "まだ霧の中にいるようだ..."
                    }
        
        dynamic_data = st.session_state.dynamic_result
        
        user_icon = get_base64_of_bin_file(base_data['file'])
        final_img_src = f"data:image/jpeg;base64,{user_icon}" if user_icon else base_data['ph']

        raw_scores = {"fire": 0, "water": 0, "wind": 0}
        for q_id, selected_label in st.session_state.answers.items():
            for q in QUESTIONS:
                if q["id"] == q_id:
                    attr = q["options"][selected_label]
                    raw_scores[attr] += 1
        
        vals = [
            raw_scores["fire"], raw_scores["water"], raw_scores["wind"],
            (raw_scores["fire"]+raw_scores["wind"])/1.2, (raw_scores["fire"]+raw_scores["water"])/1.2
        ]
        categories = ['実行力', '論理力', '共感力', '創造性', '戦略性']
        vals += [vals[0]]
        categories += [categories[0]]

        fig = go.Figure()
        fig.add_trace(go.Scatterpolar(
            r=vals, theta=categories, fill='toself', name=base_data['title'],
            line=dict(color='#FFD700', width=4), fillcolor='rgba(255, 215, 0, 0.5)',
            mode='lines+markers', marker=dict(size=10, color='#FFD700', symbol='diamond')
        ))
        fig.update_layout(
            paper_bgcolor='rgba(15, 15, 25, 0.9)',
            polar=dict(
                radialaxis=dict(visible=True, range=[0, 10], tickfont=dict(color='white', size=12, weight='bold'), gridcolor='rgba(255,255,255,0.4)', gridwidth=2, layer='below traces'),
                angularaxis=dict(tickfont=dict(color='#FFD700', size=22, family='Shippori Mincho B1', weight='bold'), gridcolor='rgba(255,255,255,0.4)', gridwidth=2),
                bgcolor='rgba(0,0,0,0)'
            ),
            font=dict(color='white'), showlegend=False, margin=dict(l=60, r=60, t=60, b=60), height=500
        )

        col_res1, col_res2 = st.columns([1, 1], gap="large")
        with col_res1:
            st.markdown(f"""
            <div class="tarot-card-outer">
                <div class="tarot-card-inner">
                    <div class="result-sub" style="font-size: 1.2em; letter-spacing: 0.2em;">{base_data['sub']}</div>
                    <div class="result-title" style="font-size: 2.5em; margin: 15px 0;">{base_data['title']}</div>
                    <img src="{final_img_src}" class="result-image">
                    <div class="result-desc" style="font-size: 1.3em; font-style: italic;">“{dynamic_data.get('desc', '運命は開かれた')}”</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        with col_res2:
            st.markdown("<h3 style='text-align: center; color: #FFD700; margin-bottom: 15px; font-size: 2em;'>能力チャート</h3>", unsafe_allow_html=True)
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
            
            st.markdown(f"""
            <div style="background: rgba(15, 15, 25, 0.9); padding: 25px; border-radius: 10px; border: 1px solid rgba(255,215,0,0.3); margin-top: 10px;">
                <p style="color: #FFD700 !important; font-weight: bold; margin-bottom: 5px; font-size: 1.2em;">🗝️ あなただけの獲得スキル:</p>
                <p style="font-size: 1.1em; margin-bottom: 20px;">{' / '.join(dynamic_data['skills'])}</p>
                <p style="color: #FFD700 !important; font-weight: bold; margin-bottom: 5px; font-size: 1.2em;">💼 運命の適職:</p>
                <p style="font-size: 1.3em; font-weight: bold;">{' / '.join(dynamic_data['jobs'])}</p>
            </div>
            """, unsafe_allow_html=True)

        if not st.session_state.final_advice:
            prompt = f"""
            ユーザーの診断結果: {base_data['title']}
            AI分析による適職: {','.join(dynamic_data['jobs'])}
            会話履歴: {st.session_state.chat_history}
            
            上記を踏まえ、神秘的な占い師として、キャリアのアドバイスを300文字程度で記述してください。
            """
            with st.spinner("運命を記しています..."):
                st.session_state.final_advice = get_gemini_response(prompt, api_key)

        st.markdown(f"""
        <div class="advice-box">
            <div class="advice-title">📜 Oracle's Message</div>
            <div style="line-height: 2.0;">{st.session_state.final_advice}</div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        col_dl1, col_dl2, col_dl3 = st.columns([1, 2, 1])
        with col_dl2:
            has_error = "申し訳ございません" in st.session_state.final_advice or "Error:" in st.session_state.final_advice
            if st.session_state.final_advice and st.session_state.dynamic_result and not has_error:
                pdf_data = create_pdf(
                    res_type, 
                    base_data['title'], 
                    st.session_state.dynamic_result['skills'], 
                    st.session_state.dynamic_result['jobs'], 
                    st.session_state.final_advice
                )
                st.download_button(
                    label="📜 運命の鑑定書をPDFで受け取る",
                    data=pdf_data,
                    file_name="fortune_career_result.pdf",
                    mime="application/pdf"
                )
            elif has_error:
                st.warning("⚠️ 現在、アクセスの集中により鑑定書を発行できませんでした。時間を置いて再試行してください。")

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("↩️ 最初に戻る"):
            st.session_state.clear()
            st.rerun()

if __name__ == "__main__":
    main()
