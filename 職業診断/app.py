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
# ★★★ 本番モード (APIを使用する) ★★★
TEST_MODE = False 

# 使用するモデルの優先順位 (API制限対策)
MODELS_TO_TRY = ["gemini-2.5-flash", "gemini-3.0-flash"]

# ==========================================

# --- ページ設定 ---
st.set_page_config(
    page_title="FORTUNE CAREER - 学生のためのAI職業診断",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 背景画像（デフォルト）
URL_BG_DEFAULT = 'https://images.unsplash.com/photo-1560183441-6333262aa22c?q=80&w=2070&auto=format&fit=crop&v=force_reload_new'

# 質問データ (構文エラー修正済み)
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
    try: return st.secrets.get("GEMINI_API_KEY")
    except: return None

def get_base64_of_bin_file(bin_file):
    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(base_dir, bin_file)
        with open(file_path, 'rb') as f: return base64.b64encode(f.read()).decode()
    except: return None

def apply_custom_css(bg_image_url):
    st.markdown(f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@700&family=Shippori+Mincho+B1:wght@400;700;900&display=swap');
        .stApp {{ background-image: {bg_image_url} !important; background-size: cover; background-attachment: fixed; }}
        .stApp::before {{ content: ""; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0, 0, 0, 0.6); z-index: -1; }}
        h1, h2, h3, p, div, span, label, li {{ color: #E0E0E0 !important; font-family: 'Shippori Mincho B1', serif; }}
        .main-title {{ font-family: 'Cinzel', serif !important; color: #FFD700 !important; font-size: 4rem !important; text-align: center; margin-top: 5vh !important; text-shadow: 0 0 10px #FFD700; }}
        [data-testid="stBottom"] {{ background-color: transparent !important; }}
        .stChatInput textarea {{ background-color: rgba(0, 0, 0, 0.8) !important; color: #FFD700 !important; border: 2px solid #FFD700 !important; border-radius: 20px !important; }}
        div[data-testid="stChatMessage"] {{ background-color: rgba(20, 10, 40, 0.9) !important; border: 1px solid #FFD700 !important; border-radius: 15px !important; }}
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

def main():
    if "step" not in st.session_state: st.session_state.step = 0
    if "answers" not in st.session_state: st.session_state.answers = {}
    if "chat_history" not in st.session_state: st.session_state.chat_history = []
    if "dynamic_result" not in st.session_state: st.session_state.dynamic_result = None
    if "final_advice" not in st.session_state: st.session_state.final_advice = ""

    api_key = get_api_key()
    bg_mansion = get_base64_of_bin_file("mansion.jpg")
    bg_css = f"url('data:image/jpeg;base64,{bg_mansion}')" if bg_mansion else f"url('{URL_BG_DEFAULT}')"
    apply_custom_css(bg_css)

    # STEP 0: トップ
    if st.session_state.step == 0:
        st.markdown('<h1 class="main-title">FORTUNE CAREER</h1>', unsafe_allow_html=True)
        st.markdown('<div style="text-align:center; font-size:1.5rem; margin-bottom:2rem;">〜 学生のためのAI職業診断 〜</div>', unsafe_allow_html=True)
        if st.button("🚪 運命の扉を開く"):
            if not api_key and not TEST_MODE: st.error("⚠️ APIキーを設定してください")
            else: st.session_state.step = 1; st.rerun()

    # STEP 1: クイズ（初期選択なし）
    elif st.session_state.step == 1:
        st.markdown("<h1 style='text-align:center;'>The 10 Prophecies</h1>", unsafe_allow_html=True)
        with st.form("quiz"):
            for q in QUESTIONS:
                st.markdown(f"### {q['q']}")
                st.radio("選択肢", list(q['options'].keys()), key=f"ans_{q['id']}", index=None, label_visibility="collapsed")
            if st.form_submit_button("🔮 真実を明らかにする"):
                st.session_state.answers = {q['id']: st.session_state[f"ans_{q['id']}"] for q in QUESTIONS}
                if None in st.session_state.answers.values(): st.error("まだ答えられていない予言があります。")
                else: st.session_state.step = 2; st.rerun()

    # STEP 2: チャット（占い師風・平易な表現）
    elif st.session_state.step == 2:
        st.markdown("<h1 style='text-align:center;'>Talk with Spirits</h1>", unsafe_allow_html=True)
        if not st.session_state.chat_history:
            res_type, main_attr = calculate_type()
            system_prompt = f"""
            あなたは「運命の館」の主であり、学生専門のキャリア占い師です。属性「{main_attr}」に基づき対話してください。
            【対話ルール】
            1. 語尾は「〜じゃ」「そなた」等の神秘的な口調を貫くこと。
            2. 質問内容は、専門用語を使わず、学生が日常の言葉で答えやすいようにすること（例：ガクチカ→学生時代に一番頑張ったこと）。
            3. 「部活、バイト、勉強などで夢中になったエピソード」を2回ほど深掘りし、最後に「運命の準備が整いました」と伝えて。
            """
            st.session_state.chat_history.append({"role": "assistant", "content": get_gemini_response(system_prompt, api_key)})

        for msg in st.session_state.chat_history:
            with st.chat_message(msg["role"], avatar="🔮" if msg["role"] == "assistant" else "🧑‍🎓"): st.write(msg["content"])
        
        if prompt := st.chat_input("ここに回答を..."):
            st.session_state.chat_history.append({"role": "user", "content": prompt})
            st.session_state.chat_history.append({"role": "assistant", "content": get_gemini_response(f"会話履歴: {st.session_state.chat_history}\n占い師口調を維持しつつ、さらに深く聞き出して。十分なら締めて。", api_key)})
            st.rerun()
        if st.button("📜 運命の書を開く"): st.session_state.step = 3; st.rerun()

    # STEP 3: 結果表示
    elif st.session_state.step == 3:
        st.balloons()
        res_type, _ = calculate_type()
        type_info = {"fire": {"title": "開拓の騎士", "file": "icon_fire.jpg"}, "water": {"title": "叡智の賢者", "file": "icon_water.jpg"}, "wind": {"title": "調和の精霊", "file": "icon_wind.jpg"}}
        base_data = type_info.get(res_type.split('-')[0], type_info["fire"])
        
        if not st.session_state.dynamic_result:
            with st.spinner("能力を紡ぎ出しています..."):
                analysis = get_gemini_response(f"会話履歴 {st.session_state.chat_history} から強みを分析しJSONで出力せよ: {{'skills':[], 'jobs':[], 'desc':''}}", api_key)
                try: st.session_state.dynamic_result = json.loads(analysis[analysis.find('{'):analysis.rfind('}')+1].replace("'", '"'))
                except: st.session_state.dynamic_result = {"skills":["努力"], "jobs":["総合職"], "desc":"大いなる可能性"}
                st.session_state.final_advice = get_gemini_response("診断結果に基づき、占い師として学生へ分かりやすく熱いアドバイスを送れ。", api_key)

        col1, col2 = st.columns(2)
        with col1:
            user_icon = get_base64_of_bin_file(base_data['file'])
            st.markdown(f"<div style='text-align:center; border:2px solid #FFD700; padding:20px; border-radius:20px;'><h2>{base_data['title']}</h2><img src='data:image/jpeg;base64,{user_icon if user_icon else ''}' style='width:200px;'><p>{st.session_state.dynamic_result['desc']}</p></div>", unsafe_allow_html=True)
        with col2:
            st.markdown(f"**🗝️ スキル:** {' / '.join(st.session_state.dynamic_result['skills'])}")
            st.markdown(f"**💼 適職:** {' / '.join(st.session_state.dynamic_result['jobs'])}")
            st.write(st.session_state.final_advice)
        
        if st.button("↩️ 戻る"): st.session_state.clear(); st.rerun()

if __name__ == "__main__": main()
