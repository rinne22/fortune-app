import streamlit as st
import google.generativeai as genai
import time
import base64
import os
import plotly.graph_objects as go
import json
import streamlit.components.v1 as components

# ==========================================
# 🔧 設定エリア
# ==========================================

# ★★★ テストモード設定 ★★★
TEST_MODE = True 

# 使用するモデルの優先順位
MODELS_TO_TRY = ["gemini-2.0-flash", "gemini-1.5-flash", "gemini-1.5-pro"]

# ==========================================

# --- ページ設定 ---
st.set_page_config(
    page_title="FORTUNE CAREER - 学生のためのAI職業診断",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- 定数 ---
URL_BG_DEFAULT = 'https://images.unsplash.com/photo-1560183441-6333262aa22c?q=80&w=2070&auto=format&fit=crop&v=force_reload_new'

# 質問データ
QUESTIONS = [
    {"id": "q1", "q": "I. 魂の渇望 - 将来、仕事を通じて得たいものは？", "options": {"💰 高い年収と社会的地位（成功・野心）": "fire", "🧠 専門スキルと知的好奇心（成長・探究）": "water", "🤝 仲間からの感謝と安心感（貢献・安定）": "wind"}},
    {"id": "q2", "q": "II. 魔力の源泉 - グループワークや部活での役割は？", "options": {"🔥 皆を引っ張るリーダー・部長タイプ": "fire", "💧 計画を立てる参謀・書記タイプ": "water", "🌿 間を取り持つ調整役・ムードメーカー": "wind"}},
    {"id": "q3", "q": "III. 冒険の指針 - 全く新しい課題が出たらどうする？", "options": {"⚔️ 「とりあえずやってみよう」と手を動かす": "fire", "🗺️ 「まずは情報を集めよう」と教科書を開く": "water", "🛡️ 「みんなはどう思う？」と友達と相談する": "wind"}},
    {"id": "q4", "q": "IV. 求める秘宝 - 居心地が良いと感じる環境は？", "options": {"👑 実力主義で、成果を出せば評価される場所": "fire", "📜 静かで、自分の研究や作業に没頭できる場所": "water", "🕊️ アットホームで、先輩後輩が仲良い場所": "wind"}},
    {"id": "q5", "q": "V. 試練の刻 - バイトや部活でトラブル発生！どう動く？", "options": {"⚡️ 自分が先頭に立って、その場で解決する": "fire", "🔍 なぜ起きたか原因を分析し、再発を防ぐ": "water", "📣 周りの人に状況を伝え、協力を仰ぐ": "wind"}},
    {"id": "q6", "q": "VI. 交信の作法 - プレゼンや発表で意識することは？", "options": {"🔥 「情熱」や「想い」を熱く伝える": "fire", "💧 「データ」や「論理」を正確に伝える": "water", "🌿 「聞き手」が楽しんでいるかを気にする": "wind"}},
    {"id": "q7", "q": "VII. 失敗の代償 - テストや試合で負けた時、どう思う？", "options": {"🔥 「次は絶対勝つ！」と闘志を燃やす": "fire", "💧 「敗因は何か？」と冷静に分析する": "water", "🌿 「チームに申し訳ない」と責任を感じる": "wind"}},
    {"id": "q8", "q": "VIII. 究極スキル - 今、大学生活で身につけたい力は？", "options": {"🔥 人を巻き込み、何かを成し遂げる「行動力」": "fire", "💧 物事の本質を見抜き、解決する「思考力」": "water", "🌿 誰とでも信頼関係を築ける「対人力」": "wind"}},
    {"id": "q9", "q": "IX. 安息の地 - 休日の理想的な過ごし方は？", "options": {"🔥 イベントや旅行など、アクティブに動く": "fire", "💧 読書、映画、ゲームなど、知識を深める": "water", "🌿 友達や恋人とカフェでのんびり話す": "wind"}},
    {"id": "q10", "q": "X. 伝説の終わり - 卒業時、周りからどう言われたい？", "options": {"🔥 「あいつは凄かった、伝説だ」": "fire", "💧 「あいつがいれば何でも解決した」": "water", "🌿 「あいつがいてくれて本当に楽しかった」": "wind"}},
]

# --- ヘルパー関数 ---

def get_api_key():
    try:
        if "GEMINI_API_KEY" in st.secrets:
            return st.secrets["GEMINI_API_KEY"]
        return "dummy_key" if TEST_MODE else None
    except:
        return "dummy_key" if TEST_MODE else None

def get_base64_of_bin_file(bin_file):
    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(base_dir, bin_file)
        if not os.path.exists(file_path): return None
        with open(file_path, 'rb') as f: data = f.read()
        return base64.b64encode(data).decode()
    except: return None

# --- HTML生成関数 ---
def create_result_html(base_data, dynamic_data, final_advice, img_base64):
    try:
        html = f"""
        <!DOCTYPE html>
        <html lang="ja">
        <head>
            <meta charset="UTF-8">
            <title>運命の鑑定書 - {base_data['title']}</title>
            <link href="https://fonts.googleapis.com/css2?family=Cinzel:wght@700&family=Shippori+Mincho+B1:wght@400;700;900&display=swap" rel="stylesheet">
            <style>
                body {{ background-color: #050510; color: #E0E0E0; font-family: 'Shippori Mincho B1', serif; text-align: center; padding: 40px; }}
                .container {{ max-width: 800px; margin: 0 auto; background-color: #1a0f2e; border: 4px double #FFD700; border-radius: 20px; padding: 40px; box-shadow: 0 0 50px rgba(255, 215, 0, 0.3); }}
                h1 {{ font-family: 'Cinzel', serif; color: #FFD700; font-size: 3em; margin-bottom: 5px; text-shadow: 0 0 10px #FFD700; }}
                .sub-title {{ color: #AAAAAA; letter-spacing: 0.2em; margin-bottom: 20px; }}
                .catchphrase {{ color: #FFD700; font-weight: bold; font-size: 1.2em; margin-bottom: 20px; background: rgba(255, 215, 0, 0.1); display: inline-block; padding: 5px 15px; border-radius: 20px; }}
                .main-img {{ width: 300px; height: 300px; object-fit: cover; border-radius: 50%; border: 3px solid #FFD700; margin: 10px auto; display: block; box-shadow: 0 0 20px rgba(255, 215, 0, 0.5); }}
                .section-box {{ background: rgba(255, 255, 255, 0.1); border-radius: 10px; padding: 20px; margin: 30px 0; text-align: left; }}
                .section-title {{ color: #FFD700; font-weight: bold; font-size: 1.2em; border-bottom: 1px solid #FFD700; padding-bottom: 5px; margin-bottom: 15px; }}
                .advice-text {{ line-height: 2.0; font-size: 1.1em; }}
                ul {{ padding-left: 20px; }}
                li {{ margin-bottom: 10px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>{base_data['title']}</h1>
                <div class="sub-title">{base_data['sub']}</div>
                <div class="catchphrase">{base_data['simple_text']}</div>
                <img src="data:image/jpeg;base64,{img_base64}" class="main-img">
                <div style="font-size: 1.5em; font-weight: bold; margin: 20px 0; color: #FFF;">“{dynamic_data.get('desc', '運命は開かれた')}”</div>
                <div class="section-box"><div class="section-title">🗝️ 今伸ばすべきスキル</div><ul>{''.join([f'<li>{skill}</li>' for skill in dynamic_data['skills']])}</ul></div>
                <div class="section-box"><div class="section-title">💼 おすすめインターン・適職</div><ul>{''.join([f'<li>{job}</li>' for job in dynamic_data['jobs']])}</ul></div>
                <div class="section-box" style="background: rgba(255, 248, 220, 0.9); color: #3E2723;"><div class="section-title" style="color: #8c5e24; border-color: #8c5e24;">📜 賢者からの助言</div><div class="advice-text">{final_advice.replace('\n', '<br>')}</div></div>
                <p style="margin-top: 30px; font-size: 0.8em; color: #666;">Issued by FORTUNE CAREER</p>
            </div>
        </body>
        </html>
        """
        return html
    except: return "<html><body><h1>Error Creating Card</h1></body></html>"

def apply_custom_css(bg_image_url):
    st.markdown(f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@700&family=Shippori+Mincho+B1:wght@400;700;900&display=swap');
        
        #MainMenu, footer, header, [data-testid="stToolbar"], .stDeployButton {{ visibility: hidden; display: none; }}
        
        .block-container {{ padding-top: 2rem !important; padding-bottom: 150px !important; }}

        .stApp {{
            background-color: #050510; 
            background-image: {bg_image_url} !important;
            background-size: cover !important;
            background-repeat: no-repeat !important;
            background-attachment: fixed !important;
            background-position: center center !important;
        }}
        .stApp::before {{
            content: ""; position: fixed; top: 0; left: 0; width: 100%; height: 100%;
            background: rgba(0, 0, 0, 0.6); z-index: -1; pointer-events: none;
        }}
        
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
        
        /* --- チャット入力欄の劇的改善（白い帯を消す！） --- */
        
        /* 下部の固定コンテナ自体を透明にする */
        [data-testid="stBottom"] {{
            background-color: transparent !important;
            background: transparent !important;
            border: none !important;
            box-shadow: none !important;
        }}
        [data-testid="stBottom"] > div {{
            background-color: transparent !important;
        }}

        /* 入力欄（テキストエリア）のデザイン */
        .stChatInput textarea {{
            background-color: rgba(0, 0, 0, 0.85) !important; /* 黒の半透明 */
            color: #FFD700 !important; /* 文字は金 */
            border: 2px solid #FFD700 !important; /* 枠は金 */
            border-radius: 30px !important; /* 丸くする */
            caret-color: #FFD700 !important;
            font-family: 'Shippori Mincho B1', serif !important;
        }}
        /* フォーカス時の光る演出 */
        .stChatInput textarea:focus {{
            box-shadow: 0 0 15px rgba(255, 215, 0, 0.6) !important;
            border-color: #FFF !important;
        }}
        
        /* 送信ボタンアイコン */
        button[data-testid="stChatInputSubmitButton"] {{
            color: #FFD700 !important;
        }}
        button[data-testid="stChatInputSubmitButton"]:hover {{
            color: #FFFFFF !important;
        }}

        /* --- チャット吹き出し --- */
        div[data-testid="stChatMessage"] {{
            background-color: rgba(20, 10, 40, 0.9) !important;
            border: 1px solid rgba(255, 215, 0, 0.6) !important;
            border-radius: 15px !important;
            padding: 20px !important;
            margin-bottom: 15px !important;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.5) !important;
        }}
        div[data-testid="stChatMessage"][data-test-role="user"] {{
            background-color: rgba(40, 40, 60, 0.9) !important;
            border-color: rgba(100, 100, 255, 0.4) !important;
        }}
        div[data-testid="stChatMessage"] .stAvatar {{
            background-color: #FFD700 !important;
            color: #000 !important;
        }}

        /* ボタン */
        div[data-testid="stFormSubmitButton"] button, 
        .stButton button,
        div[data-testid="stDownloadButton"] button {{
            width: 100%;
            background: linear-gradient(45deg, #FFD700, #FDB931, #DAA520) !important;
            color: #000000 !important;
            border: 2px solid #FFFFFF !important;
            border-radius: 50px !important;
            font-family: 'Cinzel', serif !important;
            font-weight: 900 !important;
            font-size: 1.5rem !important;
            padding: 15px 30px !important;
            margin-top: 20px !important;
        }}
        div[data-testid="stFormSubmitButton"] button:hover, 
        .stButton button:hover,
        div[data-testid="stDownloadButton"] button:hover {{
            transform: scale(1.05) !important;
            background: linear-gradient(45deg, #FFFACD, #FFD700) !important;
        }}
        div[data-testid="stDownloadButton"] button * {{ color: #000000 !important; }}

        div[role="radiogroup"] label {{
            background-color: rgba(0, 0, 0, 0.9) !important;
            border: 2px solid rgba(255, 215, 0, 0.6) !important;
            padding: 20px !important; 
            border-radius: 15px !important; 
            margin-bottom: 15px !important; 
        }}
        div[role="radiogroup"] label:hover {{ border-color: #FFD700 !important; background-color: rgba(50, 50, 50, 1.0) !important; }}
        div[role="radiogroup"] label p {{ font-size: 1.3rem !important; font-weight: bold !important; color: #FFFFFF !important; }}

        .intro-text {{ font-size: 1.5rem !important; text-align: center; color: #FFD700; font-weight: bold; background: rgba(0, 0, 0, 0.85); padding: 30px; border-radius: 15px; border: 2px solid #FFD700; }}
        
        .tarot-card-outer {{ padding: 5px; background: linear-gradient(135deg, #BF953F, #FCF6BA, #B38728, #FBF5B7); border-radius: 20px; box-shadow: 0 0 30px rgba(255, 215, 0, 0.3); margin: 0 auto; max-width: 600px; }}
        .tarot-card-inner {{ background: #1a0f2e; border-radius: 15px; padding: 30px; text-align: center; }}
        .result-simple-text {{ color: #FFD700; font-weight: bold; font-size: 1.2em; margin-bottom: 10px; background: rgba(255, 255, 255, 0.1); padding: 5px 10px; border-radius: 15px; display: inline-block; }}
        .advice-box {{ background: rgba(255, 248, 220, 0.9); border: 3px double #8B4513; border-radius: 10px; padding: 25px; margin-top: 30px; color: #3E2723 !important; }}
        .advice-box * {{ color: #3E2723 !important; }}
    </style>
    """, unsafe_allow_html=True)

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
    res_type = sorted_scores[0][0] if (sorted_scores[0][1] - sorted_scores[1][1] >= 2) else "-".join(sorted([sorted_scores[0][0], sorted_scores[1][0]]))
    return res_type, sorted_scores[0][0]

# --- AI応答関数（テストモード対応版） ---
def get_gemini_response(prompt, api_key):
    if TEST_MODE:
        time.sleep(1) 
        return "【テストモード】これはAPIを使わないテスト用の返信じゃ。\nそなたの言葉は届いておるぞ。API消費を気にせず、UIの確認をするがよい。\n\n（※本番ではここにAIの深い洞察が入ります）"

    if not api_key: return "⚠️ APIキーが設定されていません。"
    genai.configure(api_key=api_key)
    
    for model_name in MODELS_TO_TRY:
        try:
            model = genai.GenerativeModel(model_name)
            formatted_history = []
            for msg in st.session_state.chat_history:
                role = "user" if msg["role"] == "user" else "model"
                formatted_history.append({"role": role, "parts": [msg["content"]]})
            chat = model.start_chat(history=formatted_history)
            response = chat.send_message(prompt)
            if not response.text: raise ValueError("Empty response")
            return response.text 
        except Exception as e:
            print(f"Model {model_name} failed: {e}")
            continue
    return "申し訳ございません。現在、星々の声が届きにくくなっております（アクセス集中）。時間を置いて再度お試しください。"

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
    if st.session_state.step == 0:
        if bg_mansion_base64: bg_css_url = f"url('data:image/jpeg;base64,{bg_mansion_base64}')"
    elif bg_room_base64:
        bg_css_url = f"url('data:image/jpeg;base64,{bg_room_base64}')"
    
    apply_custom_css(bg_css_url)

    # STEP 0: トップページ
    if st.session_state.step == 0:
        st.markdown("""
        <div style="text-align: center;">
            <h1 class="main-title">FORTUNE CAREER</h1>
            <p style='letter-spacing: 0.1em; color: #FFD700; font-size: 2.0em; margin-top: 15px; font-weight:bold; text-shadow: 2px 2px 4px #000; background: rgba(0,0,0,0.6); display: inline-block; padding: 5px 20px; border-radius: 10px;'>〜 学生のためのAI職業診断 〜</p>
        </div>
        """, unsafe_allow_html=True)
        if TEST_MODE:
            st.warning("🚧 現在「テストモード」で動作中です。AIの返信は固定文になります。")
        st.markdown("<br>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1,2,1]) 
        with col2:
            st.markdown("""
            <div class="intro-text">
                ようこそ、迷える若き魂よ。<br>
                ここは星々の導きと、就活の叡智が交わる場所。<br>
                あなたの真の才能と、未来のキャリアを紐解いて進ぜよう。
            </div>
            """, unsafe_allow_html=True)
            if st.button("🚪 運命の扉を開く"):
                if not api_key and not TEST_MODE: st.error("⚠️ APIキーを設定してください")
                else: st.session_state.step = 1; st.rerun()

    # STEP 1: 質問フォーム
    elif st.session_state.step == 1:
        st.markdown("<h1 class='main-title' style='margin-top:20px !important;'>The 10 Prophecies</h1>", unsafe_allow_html=True)
        col_main1, col_main2, col_main3 = st.columns([1, 3, 1])
        with col_main2:
            st.markdown("""
            <div style="text-align: center; margin-bottom: 30px;">
                <p style="margin-top: 20px; font-style: italic; font-size: 1.5em; color: #FFD700; font-weight: 900; text-shadow: 2px 2px 0px #000;">
                    「そなたの価値観について、10の問いに答えよ…」
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
            あなたは「運命の館」の占い師ですが、正体は**「学生専門のキャリアコンサルタント」**です。
            ユーザーの属性「{main_attr}」({res_type})に基づき、就職活動や将来のキャリアに向けた具体的なアドバイスを行うため、深掘りをしてください。
            """
            with st.spinner("キャリアガイドと通信中..."):
                initial_response = get_gemini_response(system_prompt, api_key)
                st.session_state.chat_history.append({"role": "assistant", "content": initial_response})
                st.rerun()

        col_chat1, col_chat2, col_chat3 = st.columns([1, 3, 1])
        with col_chat2:
            for msg in st.session_state.chat_history:
                if msg["role"] == "assistant":
                    with st.chat_message("assistant", avatar="🔮"):
                        st.write(msg["content"])
                else:
                    with st.chat_message("user", avatar="🧑‍🎓"):
                        st.write(msg["content"])
        
        prompt = st.chat_input("ここに回答を入力してください...")
        if prompt:
            st.session_state.chat_history.append({"role": "user", "content": prompt})
            with st.spinner("..."):
                ai_res = get_gemini_response(prompt, api_key)
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
            "fire": {"title": "開拓の騎士", "sub": "THE LEADER", "simple_text": "行動力と情熱でチームを引っ張るリーダータイプ", "file": "icon_fire.jpg", "ph": "https://placehold.co/400x400/201335/FFD700?text=Leader"},
            "water": {"title": "叡智の賢者", "sub": "THE ENGINEER", "simple_text": "論理的思考で問題を解決する分析・開発タイプ", "file": "icon_water.jpg", "ph": "https://placehold.co/400x400/201335/FFD700?text=Wizard"},
            "wind": {"title": "調和の精霊", "sub": "THE HEALER", "simple_text": "周りと協力して空気を良くするサポータータイプ", "file": "icon_wind.jpg", "ph": "https://placehold.co/400x400/201335/FFD700?text=Healer"},
            "fire-water": {"title": "蒼炎の軍師", "sub": "THE STRATEGIST", "simple_text": "冷静な計算と大胆な行動を併せ持つ戦略家タイプ", "file": "icon_fire_water.jpg", "ph": "https://placehold.co/400x400/201335/FFD700?text=Strategist"},
            "fire-wind": {"title": "陽光の詩人", "sub": "THE ARTIST", "simple_text": "独自の感性で人を惹きつける表現者タイプ", "file": "icon_fire_wind.jpg", "ph": "https://placehold.co/400x400/201335/FFD700?text=Artist"},
            "water-wind": {"title": "星詠みの司書", "sub": "THE GUIDE", "simple_text": "知識と優しさで人を導くアドバイザータイプ", "file": "icon_water_wind.jpg", "ph": "https://placehold.co/400x400/201335/FFD700?text=Guide"},
        }
        base_data = type_info.get(res_type, type_info["fire"])

        # テストモード時の固定診断結果
        if TEST_MODE and not st.session_state.dynamic_result:
             st.session_state.dynamic_result = {
                "skills": ["（テスト）コミュニケーション力", "（テスト）問題解決力", "（テスト）創造性"],
                "jobs": ["（テスト）エンジニア", "（テスト）デザイナー", "（テスト）PM"],
                "desc": "これはテストモード用のダミー結果です。本番ではAIが分析します。"
            }
             st.session_state.final_advice = "【テストモード】これはテスト用のアドバイスじゃ。APIは消費しておらん。UIの確認に使うがよい。"

        if not st.session_state.dynamic_result:
            with st.spinner("精霊たちが会話の記憶から、あなたの真の能力を紡ぎ出しています..."):
                genai.configure(api_key=api_key)
                success = False
                for model_name in MODELS_TO_TRY:
                    try:
                        st.session_state.dynamic_result = {"skills": ["分析中..."], "jobs": ["分析中..."], "desc": "APIエラー"}
                        success = True
                        break 
                    except: continue
                if not success:
                    st.session_state.dynamic_result = {"skills": ["API Error"], "jobs": ["API Error"], "desc": "API Error"}
        
        dynamic_data = st.session_state.dynamic_result
        user_icon = get_base64_of_bin_file(base_data['file'])
        
        raw_scores = {"fire": 0, "water": 0, "wind": 0}
        for q_id, selected_label in st.session_state.answers.items():
            for q in QUESTIONS:
                if q["id"] == q_id:
                    attr = q["options"][selected_label]
                    raw_scores[attr] += 1
        vals = [raw_scores["fire"], raw_scores["water"], raw_scores["wind"], (raw_scores["fire"]+raw_scores["wind"])/1.2, (raw_scores["fire"]+raw_scores["water"])/1.2]
        categories = ['実行力', '論理力', '共感力', '創造性', '戦略性']
        vals += [vals[0]]; categories += [categories[0]]
        fig = go.Figure()
        fig.add_trace(go.Scatterpolar(r=vals, theta=categories, fill='toself', name=base_data['title'], line=dict(color='#FFD700', width=4), fillcolor='rgba(255, 215, 0, 0.5)', mode='lines+markers', marker=dict(size=10, color='#FFD700', symbol='diamond')))
        fig.update_layout(paper_bgcolor='rgba(15, 15, 25, 0.9)', polar=dict(radialaxis=dict(visible=True, range=[0, 10], tickfont=dict(color='white', size=12, weight='bold'), gridcolor='rgba(255,255,255,0.4)', gridwidth=2, layer='below traces'), angularaxis=dict(tickfont=dict(color='#FFD700', size=22, family='Shippori Mincho B1', weight='bold'), gridcolor='rgba(255,255,255,0.4)', gridwidth=2), bgcolor='rgba(0,0,0,0)'), font=dict(color='white'), showlegend=False, margin=dict(l=60, r=60, t=60, b=60), height=500)

        col_res1, col_res2 = st.columns([1, 1], gap="large")
        with col_res1:
            st.markdown(f"""
            <div class="tarot-card-outer"><div class="tarot-card-inner">
                <div class="result-sub" style="font-size: 1.2em; letter-spacing: 0.2em;">{base_data['sub']}</div>
                <div class="result-title" style="font-size: 2.5em; margin: 15px 0;">{base_data['title']}</div>
                <div class="result-simple-text">{base_data['simple_text']}</div>
                <img src="data:image/jpeg;base64,{user_icon if user_icon else ''}" class="result-image" style="width:100%; max-width:300px; border-radius:10px;">
                <div class="result-desc" style="font-size: 1.3em; font-style: italic;">“{dynamic_data.get('desc', '運命は開かれた')}”</div>
            </div></div>
            """, unsafe_allow_html=True)

        with col_res2:
            st.markdown("<h3 style='text-align: center; color: #FFD700; margin-bottom: 15px; font-size: 2em;'>能力チャート</h3>", unsafe_allow_html=True)
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
            st.markdown(f"""
            <div style="background: rgba(15, 15, 25, 0.9); padding: 25px; border-radius: 10px; border: 1px solid rgba(255,215,0,0.3); margin-top: 10px;">
                <p style="color: #FFD700 !important; font-weight: bold; margin-bottom: 5px; font-size: 1.2em;">🗝️ 今伸ばすべきスキル:</p>
                <p style="font-size: 1.1em; margin-bottom: 20px;">{' / '.join(dynamic_data['skills'])}</p>
                <p style="color: #FFD700 !important; font-weight: bold; margin-bottom: 5px; font-size: 1.2em;">💼 おすすめインターン・適職:</p>
                <p style="font-size: 1.3em; font-weight: bold;">{' / '.join(dynamic_data['jobs'])}</p>
            </div>
            """, unsafe_allow_html=True)

        if not st.session_state.final_advice and not TEST_MODE:
            prompt = f"ユーザーの診断結果: {base_data['title']}..." 
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
            html_data = create_result_html(base_data, dynamic_data, st.session_state.final_advice, user_icon if user_icon else "")
            st.download_button(label="📄 結果をHTMLファイルで保存", data=html_data, file_name="fortune_result.html", mime="text/html")
            st.caption("※ダウンロードしたファイルは、ブラウザ（ChromeやEdgeなど）で開いてください。")

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("↩️ 最初に戻る"):
            st.session_state.clear()
            st.rerun()

if __name__ == "__main__":
    main()
