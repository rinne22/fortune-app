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
# ★★★ 本番モード (APIを使用する) ★★★
TEST_MODE = False 

# 使用するモデルの優先順位 (API制限対策)
MODELS_TO_TRY = ["gemini-2.0-flash", "gemini-1.5-flash", "gemini-1.5-pro"]

# 会話の往復回数制限
MAX_TURN_COUNT = 3

# ==========================================

# --- ページ設定 ---
st.set_page_config(
    page_title="FORTUNE CAREER - 学生のためのAI職業診断",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 背景画像（デフォルト：外観）
URL_BG_MANSION = 'https://images.unsplash.com/photo-1560183441-6333262aa22c?q=80&w=2070&auto=format&fit=crop'
# 背景画像（デフォルト：部屋の中 ※room.jpgがない場合の保険）
URL_BG_ROOM = 'https://images.unsplash.com/photo-1519074069444-1ba4fff66d16?q=80&w=2070&auto=format&fit=crop'

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
    if "GEMINI_API_KEY" in st.secrets:
        return st.secrets["GEMINI_API_KEY"]
    with st.sidebar:
        st.warning("⚠️ APIキーが設定されていません")
        val = st.text_input("Gemini APIキーを入力", type="password")
        if val: return val
    return None

def get_base64_of_bin_file(bin_file):
    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(base_dir, bin_file)
        if not os.path.exists(file_path): return None
        with open(file_path, 'rb') as f: return base64.b64encode(f.read()).decode()
    except: return None

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

        .intro-text {{
            font-size: 1.5rem !important;
            line-height: 2.2; 
            text-align: center; 
            color: #FFD700; 
            font-weight: bold;
            text-shadow: 2px 2px 4px #000;
            background: rgba(0, 0, 0, 0.85);
            padding: 30px; 
            border-radius: 15px;
            border: 2px solid #FFD700;
            box-shadow: 0 0 20px rgba(0,0,0,0.8);
        }}

        div[role="radiogroup"] label {{
            background-color: rgba(0, 0, 0, 0.9) !important;
            border: 2px solid rgba(255, 215, 0, 0.6) !important;
            padding: 20px !important; 
            border-radius: 15px !important; 
            margin-bottom: 15px !important; 
            cursor: pointer;
            box-shadow: 0 4px 6px rgba(0,0,0,0.5);
        }}
        div[role="radiogroup"] label:hover {{
            border-color: #FFD700 !important;
            background-color: rgba(50, 50, 50, 1.0) !important;
            transform: translateX(5px);
        }}
        div[role="radiogroup"] label p {{
            font-size: 1.3rem !important; 
            font-weight: bold !important; 
            color: #FFFFFF !important;
        }}

        [data-testid="stBottom"] {{ background-color: transparent !important; border: none !important; }}
        [data-testid="stBottom"] > div {{ background-color: transparent !important; }}

        .stChatInput textarea {{
            background-color: rgba(0, 0, 0, 0.85) !important;
            color: #FFD700 !important;
            border: 2px solid #FFD700 !important;
            border-radius: 30px !important;
            caret-color: #FFD700 !important;
            font-family: 'Shippori Mincho B1', serif !important;
        }}
        button[data-testid="stChatInputSubmitButton"] {{ color: #FFD700 !important; }}

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
        div[data-testid="stChatMessage"] .stAvatar {{ background-color: #FFD700 !important; color: #000 !important; }}

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
        div[data-testid="stDownloadButton"] button * {{ color: #000000 !important; }}

        .tarot-card-outer {{
            padding: 5px; 
            background: linear-gradient(135deg, #BF953F, #FCF6BA, #B38728, #FBF5B7);
            border-radius: 20px; 
            box-shadow: 0 0 30px rgba(255, 215, 0, 0.3);
            margin: 0 auto; 
            max-width: 600px;
        }}
        .tarot-card-inner {{
            background: #1a0f2e; 
            border-radius: 15px; 
            padding: 30px; 
            text-align: center;
        }}
        .result-sub {{ font-size: 1.2em; letter-spacing: 0.2em; color: #AAAAAA; }}
        .result-title {{ font-size: 2.5em; margin: 15px 0; color: #FFD700; font-family: 'Cinzel', serif; }}
        .result-simple-text {{
            color: #FFD700; 
            font-weight: bold; 
            font-size: 1.2em; 
            margin-bottom: 15px;
            background: rgba(255, 255, 255, 0.1); 
            padding: 5px 15px; 
            border-radius: 15px; 
            display: inline-block;
        }}
        .result-desc {{ font-size: 1.3em; font-style: italic; margin-top: 15px; color: #FFFFFF; }}
        
        .advice-box {{
            background: rgba(255, 248, 220, 0.9); 
            border: 3px double #8B4513;
            border-radius: 10px; 
            padding: 25px; 
            margin-top: 30px;
            color: #3E2723 !important;
        }}
        .advice-box * {{ color: #3E2723 !important; }}
    </style>
    """, unsafe_allow_html=True)

def get_gemini_response(prompt, api_key):
    if TEST_MODE: return "【テスト応答】そなたの運命、しかと見届けたぞ。"
    if not api_key: return "⚠️ APIキーが設定されていません。"
    genai.configure(api_key=api_key)
    for model_name in MODELS_TO_TRY:
        try:
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(prompt)
            if response.text: return response.text
        except: continue
    return "申し訳ございません。現在、星々の声が届きにくくなっております。"

def calculate_type():
    scores = {"fire": 0, "water": 0, "wind": 0}
    for q_id, label in st.session_state.answers.items():
        for q in QUESTIONS:
            if q["id"] == q_id: scores[q["options"][label]] += 1
    sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    res_type = sorted_scores[0][0] if (sorted_scores[0][1] - sorted_scores[1][1] >= 2) else "-".join(sorted([sorted_scores[0][0], sorted_scores[1][0]]))
    return res_type, sorted_scores[0][0]

def create_result_html(base_data, dynamic_data, final_advice, img_base64):
    try:
        html = f"""
        <!DOCTYPE html>
        <html lang="ja">
        <head>
            <meta charset="UTF-8">
            <title>運命の鑑定書</title>
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
                <p style="margin-top: 30px; font-size: 0.8em; color: #666;">Issued by FORTUNE CAREER - 学生のためのAI職業診断</p>
            </div>
        </body>
        </html>
        """
        return html
    except: return "<html><body><h1>Error Creating Card</h1></body></html>"

def main():
    if "step" not in st.session_state: st.session_state.step = 0
    if "answers" not in st.session_state: st.session_state.answers = {}
    if "chat_history" not in st.session_state: st.session_state.chat_history = []
    if "dynamic_result" not in st.session_state: st.session_state.dynamic_result = None
    if "final_advice" not in st.session_state: st.session_state.final_advice = ""

    api_key = get_api_key()
    
    # 画像読み込み
    bg_mansion_base64 = get_base64_of_bin_file("mansion.jpg")
    bg_room_base64 = get_base64_of_bin_file("room.jpg")
    
    # ★背景ロジック修正: ローカル画像がない場合は、必ず「適切なWeb画像」を使う
    # これにより「room.jpgがないからといってmansion.jpgを使う」誤作動を防ぐ
    bg_css_url = f"url('{URL_BG_MANSION}')"
    
    if st.session_state.step in [0, 1]:
        # ステップ0,1は外観
        if bg_mansion_base64:
            bg_css_url = f"url('data:image/jpeg;base64,{bg_mansion_base64}')"
        else:
            bg_css_url = f"url('{URL_BG_MANSION}')"
            
    elif st.session_state.step in [2, 3]:
        # ステップ2,3は部屋の中
        if bg_room_base64:
            bg_css_url = f"url('data:image/jpeg;base64,{bg_room_base64}')"
        else:
            # ここでmansionにフォールバックせず、URL_BG_ROOMを使うのが正解
            bg_css_url = f"url('{URL_BG_ROOM}')"

    apply_custom_css(bg_css_url)

    # STEP 0: トップ
    if st.session_state.step == 0:
        st.markdown('<h1 class="main-title">FORTUNE CAREER</h1>', unsafe_allow_html=True)
        st.markdown('<div style="text-align:center; font-size:1.5rem; margin-bottom:2rem; color:#FFD700; text-shadow:1px 1px 2px black;">〜 学生のためのAI職業診断 〜</div>', unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([1, 2, 1])
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

    # STEP 1: クイズ（変数名 q_data に統一して修正）
    elif st.session_state.step == 1:
        st.markdown("<h1 class='main-title' style='margin-top:20px !important;'>The 10 Prophecies</h1>", unsafe_allow_html=True)
        col_m1, col_m2, col_m3 = st.columns([1, 3, 1])
        with col_m2:
            st.markdown("<p style='text-align:center; font-style:italic; font-size:1.5em; color:#FFD700; font-weight:900;'>「そなたの価値観について、10の問いに答えよ…」</p>", unsafe_allow_html=True)
            with st.form("questions_form"):
                for q_data in QUESTIONS:
                    st.markdown(f"<h3 style='color:#FFD700; text-shadow: 2px 2px 4px #000; font-size:1.4em;'>{q_data['q']}</h3>", unsafe_allow_html=True)
                    st.radio("選択肢", list(q_data['options'].keys()), key=f"ans_{q_data['id']}", index=None, label_visibility="collapsed")
                if st.form_submit_button("🔮 真実を明らかにする"):
                    all_answered = True
                    temp_answers = {}
                    for q_data in QUESTIONS:
                        if st.session_state.get(f"ans_{q_data['id']}") is None:
                            all_answered = False
                            break
                        temp_answers[q_data['id']] = st.session_state[f"ans_{q_data['id']}"]
                    
                    if not all_answered:
                        st.error("まだ答えられていない予言があります。")
                    else:
                        st.session_state.answers = temp_answers
                        st.session_state.step = 2; st.rerun()

    # STEP 2: チャット
    elif st.session_state.step == 2:
        st.markdown("<h1 class='main-title' style='margin-top:20px !important;'>Talk with Spirits</h1>", unsafe_allow_html=True)
        if not st.session_state.chat_history:
            res_type, main_attr = calculate_type()
            # プロンプト強化：職業適性重視 + 具体性重視
            system_prompt = f"""
            あなたは「運命の館」の主であり、裏の顔は【学生専門の凄腕キャリアコンサルタント】です。
            ユーザーの診断属性「{main_attr}」に基づき、職業適性をガチで分析するためのヒアリングを行ってください。
            
            【厳守ルール】
            1. キャラ作り：語尾は「〜じゃ」「そなた」等の占い師口調を崩さない。
            2. ヒアリング内容：
               - 「なんとなく」の話は許さず、「具体的にいつ？誰と？どんな成果が出た？」と突っ込んで聞くこと。
               - 学生が答えやすいように、「例えば部活の大会で〜」「アルバイトの接客で〜」と具体的なシーンを例示して問いかけること。
            3. 目的：最終的にこの学生に最適な「具体的な職種（例：Webマーケター、法人営業）」を提案するための材料を集めること。
            """
            st.session_state.chat_history.append({"role": "assistant", "content": get_gemini_response(system_prompt, api_key)})

        col_c1, col_c2, col_c3 = st.columns([1, 3, 1])
        with col_c2:
            # ユーザーの発言回数カウント
            user_msg_count = len([m for m in st.session_state.chat_history if m["role"] == "user"])

            for msg in st.session_state.chat_history:
                with st.chat_message(msg["role"], avatar="🔮" if msg["role"] == "assistant" else "🧑‍🎓"): st.write(msg["content"])
            
            if user_msg_count < MAX_TURN_COUNT:
                if prompt := st.chat_input("ここに回答を入力してください..."):
                    st.session_state.chat_history.append({"role": "user", "content": prompt})
                    next_prompt = f"会話履歴: {st.session_state.chat_history}\n占い師口調で、さらに具体的に職業適性を探る質問をして。"
                    if user_msg_count + 1 >= MAX_TURN_COUNT:
                        next_prompt = f"会話履歴: {st.session_state.chat_history}\nこれまでの情報を踏まえ、占い師口調で「ふむ、そなたの真の力が完全に見えたぞ...」と締めくくり、結果を見るように促して。"
                    st.session_state.chat_history.append({"role": "assistant", "content": get_gemini_response(next_prompt, api_key)})
                    st.rerun()
            else:
                st.success("星々の導きが出揃いました。運命の書を開くときです。")
            
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("📜 運命の書を開く"): st.session_state.step = 3; st.rerun()

    # STEP 3: 結果表示
    elif st.session_state.step == 3:
        st.balloons()
        st.markdown("<h1 class='main-title' style='margin-top:20px !important;'>✨ Your Destiny Card ✨</h1>", unsafe_allow_html=True)
        
        res_type, _ = calculate_type()
        type_info = {
            "fire": {"title": "開拓の騎士", "sub": "THE LEADER", "simple_text": "行動力と情熱でチームを引っ張るリーダータイプ", "file": "icon_fire.jpg"},
            "water": {"title": "叡智の賢者", "sub": "THE ENGINEER", "simple_text": "論理的思考で問題を解決する分析・開発タイプ", "file": "icon_water.jpg"},
            "wind": {"title": "調和の精霊", "sub": "THE HEALER", "simple_text": "周りと協力して空気を良くするサポータータイプ", "file": "icon_wind.jpg"},
            "fire-water": {"title": "蒼炎の軍師", "sub": "THE STRATEGIST", "simple_text": "冷静な計算と大胆な行動を併せ持つ戦略家タイプ", "file": "icon_fire_water.jpg"},
            "fire-wind": {"title": "陽光の詩人", "sub": "THE ARTIST", "simple_text": "独自の感性で人を惹きつける表現者タイプ", "file": "icon_fire_wind.jpg"},
            "water-wind": {"title": "星詠みの司書", "sub": "THE GUIDE", "simple_text": "知識と優しさで人を導くアドバイザータイプ", "file": "icon_water_wind.jpg"},
        }
        base_data = type_info.get(res_type, type_info["fire"])
        
        if not st.session_state.dynamic_result:
            with st.spinner("能力を紡ぎ出しています..."):
                analysis = get_gemini_response(f"会話履歴 {st.session_state.chat_history} から強みを分析しJSONで出力せよ: {{'skills':['スキル1','スキル2','スキル3'], 'jobs':['職種1','職種2','職種3'], 'desc':'一言キャッチコピー'}}", api_key)
                try: st.session_state.dynamic_result = json.loads(analysis[analysis.find('{'):analysis.rfind('}')+1].replace("'", '"'))
                except: st.session_state.dynamic_result = {"skills":["コミュニケーション力", "継続力", "分析力"], "jobs":["総合職", "営業", "企画"], "desc":"あなたの可能性は無限大です"}
                st.session_state.final_advice = get_gemini_response("診断結果に基づき、占い師として学生へ300文字程度の分かりやすく熱いアドバイスを送れ。", api_key)

        user_icon = get_base64_of_bin_file(base_data['file'])
        
        # レーダーチャート
        raw_scores = {"fire": 0, "water": 0, "wind": 0}
        for q_id, label in st.session_state.answers.items():
            for q in QUESTIONS:
                if q["id"] == q_id: raw_scores[q["options"][label]] += 1
        
        vals = [
            raw_scores["fire"], raw_scores["water"], raw_scores["wind"],
            (raw_scores["fire"]+raw_scores["wind"])/1.2, (raw_scores["fire"]+raw_scores["water"])/1.2
        ]
        vals += [vals[0]]
        categories = ['実行力', '論理力', '共感力', '創造性', '戦略性', '実行力']

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
                angularaxis=dict(tickfont=dict(color='#FFD700', size=15, family='Shippori Mincho B1', weight='bold'), gridcolor='rgba(255,255,255,0.4)', gridwidth=2),
                bgcolor='rgba(0,0,0,0)'
            ),
            font=dict(color='white'), showlegend=False, margin=dict(l=60, r=60, t=60, b=60), height=400
        )

        col1, col2 = st.columns([1, 1], gap="large")
        with col1:
            st.markdown(f"""
            <div class="tarot-card-outer">
                <div class="tarot-card-inner">
                    <div class="result-sub">{base_data['sub']}</div>
                    <div class="result-title">{base_data['title']}</div>
                    <div class="result-simple-text">{base_data['simple_text']}</div>
                    <img src="data:image/jpeg;base64,{user_icon if user_icon else ''}" style="width:100%; border-radius:10px;">
                    <div class="result-desc">“{st.session_state.dynamic_result['desc']}”</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            st.markdown("<h3 style='text-align: center; color: #FFD700; margin-bottom: 15px; font-size: 2em;'>能力チャート</h3>", unsafe_allow_html=True)
            st.plotly_chart(fig, use_container_width=True)
            st.markdown(f"""
            <div style="background:rgba(15, 15, 25, 0.9); padding:20px; border-radius:10px; border:1px solid #FFD700;">
                <p style='color:#FFD700; font-weight:bold;'>🗝️ スキル: {' / '.join(st.session_state.dynamic_result['skills'])}</p>
                <p style='color:#FFD700; font-weight:bold;'>💼 適職: {' / '.join(st.session_state.dynamic_result['jobs'])}</p>
            </div>""", unsafe_allow_html=True)

        st.markdown(f"""<div class="advice-box"><div style="font-weight:900; color:#8B4513; font-size:1.2em; border-bottom:1px solid #8B4513; padding-bottom:5px; margin-bottom:10px;">📜 Oracle's Message</div><div style="line-height:2.0;">{st.session_state.final_advice}</div></div>""", unsafe_allow_html=True)
        
        html = create_result_html(base_data, st.session_state.dynamic_result, st.session_state.final_advice, user_icon if user_icon else "")
        st.download_button("📄 鑑定書を保存", data=html, file_name="result.html", mime="text/html")
        if st.button("↩️ 戻る"): st.session_state.clear(); st.rerun()

if __name__ == "__main__": main()

