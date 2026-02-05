import streamlit as st
import google.generativeai as genai
import time
import base64
import os
import plotly.graph_objects as go
import json

# ==========================================
# 🔧 設定エリア
# ==========================================
TEST_MODE = False 
MODELS_TO_TRY = ["gemini-2.5-flash", "gemini-3.0-flash", "gemini-2.5-pro"]
MAX_TURN_COUNT = 3

# ==========================================

# --- ページ設定 ---
st.set_page_config(
    page_title="FORTUNE CAREER",
    page_icon="🔮",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 背景画像のWeb URL
URL_BG_MANSION = 'https://images.unsplash.com/photo-1560183441-6333262aa22c?q=80&w=2070&auto=format&fit=crop'
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
        val = st.text_input("Gemini API Key", type="password")
        if val: return val
    return None

@st.cache_data
def get_base64_of_bin_file(bin_file):
    try:
        if os.path.exists(bin_file):
            with open(bin_file, 'rb') as f:
                data = f.read()
            return base64.b64encode(data).decode()
        
        script_dir = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(script_dir, bin_file)
        if os.path.exists(file_path):
            with open(file_path, 'rb') as f:
                data = f.read()
            return base64.b64encode(data).decode()
    except Exception:
        return None
    return None

def apply_custom_css(bg_url):
    st.markdown(f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@700&family=Shippori+Mincho+B1:wght@400;700;900&display=swap');
        
        html, body, [class*="st-"] {{
            font-family: 'Shippori Mincho B1', serif !important;
            color: #E0E0E0 !important;
            font-size: 1.05rem !important; 
        }}

        /* 背景画像設定 */
        [data-testid="stAppViewContainer"] {{
            background-image: {bg_url} !important;
            background-size: cover !important;
            background-position: center center !important;
            background-repeat: no-repeat !important;
            background-attachment: fixed !important;
        }}
        [data-testid="stAppViewContainer"]::before {{
            content: ""; position: fixed; top: 0; left: 0; width: 100%; height: 100%;
            background: rgba(0, 0, 0, 0.5); z-index: -1; pointer-events: none;
        }}

        [data-testid="stHeader"] {{ visibility: hidden; }}

        .main-title {{
            font-family: 'Cinzel', serif !important;
            color: #FFD700 !important;
            text-shadow: 0 0 10px #FFD700, 0 0 20px #000;
            font-size: 3.5rem !important;
            text-align: center;
            margin-top: 20px !important;
        }}

        .intro-box {{
            background: rgba(0, 0, 0, 0.85);
            border: 2px solid #FFD700;
            border-radius: 15px;
            padding: 30px;
            text-align: center;
            font-size: 1.2rem; 
            line-height: 2;
            box-shadow: 0 0 30px rgba(0,0,0,0.8);
        }}

        h3 {{
            font-size: 1.6rem !important;
            color: #FFD700 !important;
            text-shadow: 2px 2px 4px #000;
            margin-bottom: 20px !important;
        }}

        div[role="radiogroup"] label {{
            background-color: rgba(20, 20, 40, 0.9) !important;
            border: 1px solid #FFD700 !important;
            border-radius: 10px !important;
            padding: 15px 20px !important;
            margin-bottom: 10px !important;
            color: white !important;
            transition: all 0.2s ease-in-out;
            box-shadow: 0 4px 6px rgba(0,0,0,0.5);
        }}
        div[role="radiogroup"] label:hover {{
            background-color: rgba(60, 60, 80, 1.0) !important;
            transform: translateX(5px);
            box-shadow: 0 0 10px #FFD700;
        }}
        div[role="radiogroup"] label p {{
            font-size: 1.25rem !important;
            font-weight: bold !important; 
            color: #FFFFFF !important;
        }}

        [data-testid="stBottom"] {{ background: transparent !important; }}
        .stChatInput textarea {{
            background-color: rgba(0, 0, 0, 0.8) !important;
            color: #FFD700 !important;
            border: 2px solid #FFD700 !important;
            border-radius: 25px !important;
            font-size: 1.1rem !important;
        }}
        div[data-testid="stChatMessage"] {{
            background-color: rgba(20, 10, 30, 0.9) !important;
            border: 1px solid rgba(255, 215, 0, 0.3) !important;
            border-radius: 15px !important;
        }}
        div[data-testid="stChatMessage"] p {{
            font-size: 1.1rem !important;
            line-height: 1.6;
        }}

        /* ★ボタン修正★ 白くしない。フォーム送信ボタンも強制的に金色にする */
        @keyframes pulse-gold {{
            0% {{ box-shadow: 0 0 0 0 rgba(255, 215, 0, 0.7); }}
            70% {{ box-shadow: 0 0 0 15px rgba(255, 215, 0, 0); }}
            100% {{ box-shadow: 0 0 0 0 rgba(255, 215, 0, 0); }}
        }}

        /* 通常のボタンと、フォーム送信ボタン(stFormSubmitButton)の両方を指定 */
        .stButton button, 
        [data-testid="stFormSubmitButton"] button {{
            width: 100% !important;
            background: linear-gradient(45deg, #FFD700, #FDB931, #DAA520) !important;
            color: #000000 !important; /* 文字は黒 */
            font-weight: 900 !important;
            border: 2px solid #8B6508 !important; /* 枠線も金色 */
            padding: 20px 30px !important;
            border-radius: 50px !important;
            font-family: 'Cinzel', serif !important;
            font-size: 1.6rem !important;
            text-shadow: none !important;
            animation: pulse-gold 2s infinite !important;
            transition: all 0.3s ease !important;
            margin-top: 15px !important;
        }}
        
        .stButton button:hover,
        [data-testid="stFormSubmitButton"] button:hover {{
            transform: scale(1.05) !important;
            background: linear-gradient(45deg, #FFED4B, #FFD700) !important;
            border-color: #8B6508 !important;
            color: #000000 !important;
            box-shadow: 0 0 30px rgba(255, 215, 0, 0.8) !important;
        }}
        
        /* 結果カード */
        .card-frame {{
            padding: 5px;
            background: linear-gradient(135deg, #BF953F, #FCF6BA, #B38728, #FBF5B7);
            border-radius: 20px;
            box-shadow: 0 0 30px rgba(255, 215, 0, 0.3);
            margin-bottom: 20px;
        }}
        .card-content {{
            background: #1a0f2e;
            padding: 20px;
            border-radius: 15px;
            text-align: center;
        }}
        .advice-box {{
            background: rgba(255, 248, 220, 0.95); 
            border: 3px double #8B4513;
            border-radius: 10px; 
            padding: 25px; 
            margin-top: 30px;
            color: #3E2723 !important;
            font-size: 1.1rem !important;
        }}
        .advice-box * {{ color: #3E2723 !important; }}
    </style>
    """, unsafe_allow_html=True)

def get_gemini_response(prompt, api_key):
    if TEST_MODE: 
        time.sleep(1)
        return "【テスト】そなたの運命、しかと見届けた。"
    
    if not api_key: return "⚠️ APIキーを設定してください。"
    genai.configure(api_key=api_key)
    
    for model_name in MODELS_TO_TRY:
        try:
            model = genai.GenerativeModel(model_name)
            res = model.generate_content(prompt)
            if res.text: return res.text
        except: continue
    return "申し訳ございません。星々の声が届きにくくなっております。"

def calculate_type():
    scores = {"fire": 0, "water": 0, "wind": 0}
    for q_id, val in st.session_state.answers.items():
        for q in QUESTIONS:
            if q["id"] == q_id:
                scores[q["options"][val]] += 1
    
    sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    t1, s1 = sorted_scores[0]
    t2, s2 = sorted_scores[1]
    if s1 - s2 >= 2: return t1, t1
    return f"{min(t1,t2)}-{max(t1,t2)}", t1

def create_result_html(base_data, dynamic_data, final_advice, img_base64):
    try:
        return f"""
        <html>
        <body style="background:#050510; color:#E0E0E0; font-family:serif; text-align:center; padding:20px;">
            <div style="border:4px double #FFD700; padding:40px; background:#1a0f2e; border-radius:20px;">
                <h1 style="color:#FFD700; font-family:serif;">{base_data['title']}</h1>
                <img src="data:image/jpeg;base64,{img_base64}" style="width:200px; border-radius:10px; border:2px solid #FFD700;">
                <h3 style="color:#FFF;">“{dynamic_data.get('desc','')}”</h3>
                <div style="text-align:left; background:rgba(255,255,255,0.1); padding:20px; border-radius:10px;">
                    <p><b>適職:</b> {', '.join(dynamic_data['jobs'])}</p>
                    <p><b>助言:</b> {final_advice}</p>
                </div>
            </div>
        </body>
        </html>
        """
    except: return "<html><body>Error</body></html>"

# --- メイン処理 ---
def main():
    if "step" not in st.session_state: st.session_state.step = 0
    if "answers" not in st.session_state: st.session_state.answers = {}
    if "chat_history" not in st.session_state: st.session_state.chat_history = []
    if "dynamic_result" not in st.session_state: st.session_state.dynamic_result = None
    if "final_advice" not in st.session_state: st.session_state.final_advice = ""

    api_key = get_api_key()
    
    # 画像ファイル読み込み
    mansion_local = get_base64_of_bin_file("mansion.jpg")
    room_local = get_base64_of_bin_file("room.jpg")
    
    # 背景切り替えロジック
    bg_css_url = f"url('{URL_BG_MANSION}')"
    if st.session_state.step == 0:
        if mansion_local:
            bg_css_url = f"url('data:image/jpeg;base64,{mansion_local}')"
        else:
            bg_css_url = f"url('{URL_BG_MANSION}')"
    else:
        if room_local:
            bg_css_url = f"url('data:image/jpeg;base64,{room_local}')"
        else:
            bg_css_url = f"url('{URL_BG_ROOM}')"
    
    apply_custom_css(bg_css_url)

    # --- STEP 0: トップ ---
    if st.session_state.step == 0:
        st.markdown('<div class="main-title">FORTUNE CAREER</div>', unsafe_allow_html=True)
        st.markdown('<div style="text-align:center; margin-bottom:40px;">〜 学生のためのAI職業診断 〜</div>', unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.markdown("""
            <div class="intro-box">
                ようこそ、迷える若き魂よ。<br>
                ここは星々の導きと、就活の叡智が交わる場所。<br>
                あなたの真の才能と、未来のキャリアを紐解いて進ぜよう。
            </div>
            """, unsafe_allow_html=True)
            if st.button("🚪 運命の扉を開く"):
                if not api_key and not TEST_MODE:
                    st.error("左のサイドバーからAPIキーを入力してください")
                else:
                    st.session_state.step = 1
                    st.rerun()

    # --- STEP 1: 質問 ---
    elif st.session_state.step == 1:
        st.markdown('<div class="main-title">The 10 Prophecies</div>', unsafe_allow_html=True)
        st.markdown('<p style="text-align:center; color:#DDD; font-size:1.2rem;">そなたの価値観について、10の問いに答えよ…</p>', unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([1, 3, 1])
        with col2:
            with st.form("quiz"):
                for q_data in QUESTIONS:
                    st.markdown(f"<h3 style='color:#FFD700; text-shadow:1px 1px 2px #000;'>{q_data['q']}</h3>", unsafe_allow_html=True)
                    st.radio("選択肢", list(q_data['options'].keys()), key=f"ans_{q_data['id']}", index=None, label_visibility="collapsed")
                
                st.markdown("<div style='height: 40px;'></div>", unsafe_allow_html=True)
                
                # ここが修正ポイント：フォーム送信ボタン
                if st.form_submit_button("🔮 真実を明らかにする"):
                    valid = True
                    temp_ans = {}
                    for q in QUESTIONS:
                        val = st.session_state.get(f"ans_{q['id']}")
                        if val is None:
                            valid = False
                            break
                        temp_ans[q['id']] = val
                    
                    if valid:
                        st.session_state.answers = temp_ans
                        st.session_state.step = 2
                        st.rerun()
                    else:
                        st.error("全ての問いに答えてください。")

    # --- STEP 2: チャット ---
    elif st.session_state.step == 2:
        st.markdown('<div class="main-title">Talk with Spirits</div>', unsafe_allow_html=True)
        
        if not st.session_state.chat_history:
            _, main_attr = calculate_type()
            first_prompt = f"""
            あなたは「運命の館」の主（占い師）であり、超一流の学生キャリアコンサルタントです。
            ユーザーの属性は「{main_attr}」です。
            
            【役割】
            占い師の口調（〜じゃ、そなた、〜かのう）で話してください。
            質問内容は「ガクチカ」や「自己分析」のための超具体的な深掘りです。
            
            【禁止事項】
            絶対に「選択肢」や「以下から選んでください」といった提示をしてはいけません。
            対話として自然に、一つだけ質問を投げかけてください。
            """
            st.session_state.chat_history.append({"role": "assistant", "content": get_gemini_response(first_prompt, api_key)})

        col1, col2, col3 = st.columns([1, 3, 1])
        with col2:
            user_count = len([m for m in st.session_state.chat_history if m["role"] == "user"])
            
            for msg in st.session_state.chat_history:
                icon = "🔮" if msg["role"] == "assistant" else "🧑‍🎓"
                with st.chat_message(msg["role"], avatar=icon):
                    st.write(msg["content"])
            
            if user_count < MAX_TURN_COUNT:
                if val := st.chat_input("回答を入力..."):
                    st.session_state.chat_history.append({"role": "user", "content": val})
                    
                    if user_count + 1 >= MAX_TURN_COUNT:
                        next_prompt = "十分な情報が集まりました。占い師として「ふむ、そなたの進むべき道が見えたぞ...」と、結果を見るよう促すセリフだけで締めくくってください。選択肢は不要です。"
                    else:
                        next_prompt = f"会話履歴:{st.session_state.chat_history}\n占い師として、学生の強みを特定するための鋭い追加質問を1つだけ行ってください。選択肢は提示しないでください。"
                    
                    st.session_state.chat_history.append({"role": "assistant", "content": get_gemini_response(next_prompt, api_key)})
                    st.rerun()
            else:
                st.success("運命の結果が出ました。")
                if st.button("📜 運命の書を開く"): st.session_state.step = 3; st.rerun()

    # --- STEP 3: 結果 ---
    elif st.session_state.step == 3:
        st.balloons()
        st.markdown('<div class="main-title">Your Destiny Card</div>', unsafe_allow_html=True)
        r_type, _ = calculate_type()
        cards = {
            "fire": {"title": "開拓の騎士", "file": "icon_fire.jpg"},
            "water": {"title": "叡智の賢者", "file": "icon_water.jpg"},
            "wind": {"title": "調和の精霊", "file": "icon_wind.jpg"},
            "fire-water": {"title": "蒼炎の軍師", "file": "icon_fire_water.jpg"},
            "fire-wind": {"title": "陽光の詩人", "file": "icon_fire_wind.jpg"},
            "water-wind": {"title": "星詠みの司書", "file": "icon_water_wind.jpg"}
        }
        card_data = cards.get(r_type, cards["fire"])

        if not st.session_state.dynamic_result:
            with st.spinner("分析中..."):
                prompt = f"会話履歴:{st.session_state.chat_history} から強み分析JSONを出力: {{'skills':['スキル1','スキル2','スキル3'], 'jobs':['職種1','職種2','職種3'], 'desc':'一言キャッチコピー'}} JSON形式のみ出力せよ。"
                try:
                    res = get_gemini_response(prompt, api_key)
                    cleaned_res = res.replace("```json", "").replace("```", "").strip()
                    st.session_state.dynamic_result = json.loads(cleaned_res)
                except: st.session_state.dynamic_result = {"skills":["分析"], "jobs":["総合職"], "desc":"可能性"}
                
                adv_prompt = "診断結果に基づき、占い師として学生の背中を押すアドバイスを300文字でください。選択肢は不要です。"
                st.session_state.final_advice = get_gemini_response(adv_prompt, api_key)

        d_res = st.session_state.dynamic_result
        col1, col2 = st.columns(2)
        
        with col1:
            img_b64 = get_base64_of_bin_file(card_data['file'])
            src = f"data:image/jpeg;base64,{img_b64}" if img_b64 else "https://placehold.co/300x300/000/FFF?text=Card"
            st.markdown(f"""
            <div class="card-frame">
                <div class="card-content">
                    <h2 style="color:#FFD700;">{card_data['title']}</h2>
                    <img src="{src}" style="width:100%; border-radius:10px; margin:10px 0;">
                    <p style="color:#FFF; font-weight:bold;">“{d_res['desc']}”</p>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            raw = {"fire":0, "water":0, "wind":0}
            for k,v in st.session_state.answers.items():
                for q in QUESTIONS:
                    if q["id"]==k: raw[q["options"][v]] += 1
            vals = [raw["fire"], raw["water"], raw["wind"], (raw["fire"]+raw["wind"])/1.5, (raw["fire"]+raw["water"])/1.5, raw["fire"]]
            fig = go.Figure(data=go.Scatterpolar(r=vals, theta=['実行力','論理力','共感力','創造性','戦略性','実行力'], fill='toself', line_color='#FFD700'))
            fig.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                polar=dict(
                    bgcolor='rgba(0,0,0,0.5)',
                    radialaxis=dict(visible=True, range=[0, 10], showticklabels=False),
                    angularaxis=dict(tickfont=dict(color='white', size=16))
                ),
                margin=dict(l=40, r=40, t=40, b=40),
                height=400
            )
            st.plotly_chart(fig, use_container_width=True)
            
            st.markdown(f"""
            <div style="background:rgba(0,0,0,0.7); padding:20px; border-radius:10px; border:1px solid #FFD700; font-size:1.1rem;">
                <p><b>🗝️ スキル:</b> {' / '.join(d_res['skills'])}</p>
                <p><b>💼 適職:</b> {' / '.join(d_res['jobs'])}</p>
            </div>
            """, unsafe_allow_html=True)

        st.markdown(f"<div class='advice-box'><h3>📜 Oracle's Message</h3>{st.session_state.final_advice}</div>", unsafe_allow_html=True)
        
        html = create_result_html(base_data, st.session_state.dynamic_result, st.session_state.final_advice, user_icon if user_icon else "")
        st.download_button("📄 鑑定書を保存", data=html, file_name="result.html", mime="text/html")
        if st.button("↩️ 戻る"): st.session_state.clear(); st.rerun()

if __name__ == "__main__": main()
