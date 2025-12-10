import os
from pathlib import Path
import streamlit as st
import base64
import streamlit.components.v1 as stc

from google import genai
from google.genai import types

# ページ設定
st.title("Gemini Chat")

# GIFファイルの読み込み
gif_path = Path(__file__).resolve().parent / "TokeruMendako.gif"
gif_b64 = None
if gif_path.exists():
    try:
        gif_bytes = gif_path.read_bytes()
        gif_b64 = base64.b64encode(gif_bytes).decode()
    except Exception:
        st.warning(f"GIF を読み込めませんでした: {gif_path}")
else:
    st.warning(f"GIF が見つかりません: {gif_path}")

# Gemini APIクライアントの初期化
@st.cache_resource
def get_client():
    api_key = os.environ.get("GEMINI_API_KEY")
    return genai.Client(api_key=api_key)

client = get_client()
model = "gemini-flash-lite-latest"

# セッションステートで会話履歴を管理
if "messages" not in st.session_state:
    st.session_state.messages = []

# カラムレイアウト（チャット部分と画像部分）
col1, col2 = st.columns([3, 1])

# 左カラム：チャット表示エリア
with col1:
    # 過去のメッセージを表示
    for message in st.session_state.messages:
        avatar = f"data:image/gif;base64,{gif_b64}" if message["role"] == "assistant" and gif_b64 else "👤"
        with st.chat_message(message["role"], avatar=avatar):
            st.markdown(message["content"])

    # ユーザー入力を受け取る
    if prompt := st.chat_input("メッセージを入力してください"):
        # ユーザーメッセージを表示して履歴に追加
        with st.chat_message("user", avatar="👤"):
            st.markdown(prompt)
        st.session_state.messages.append({"role": "user", "content": prompt})

        # 会話履歴をGemini形式に変換
        contents = []
        for msg in st.session_state.messages:
            role = "user" if msg["role"] == "user" else "model"
            contents.append(
                types.Content(role=role, parts=[types.Part(text=msg["content"])])
            )

        # Gemini APIにリクエストを送信する直前にGIF（アニメーション）を表示
        placeholder = None
        if gif_b64:
            placeholder = st.empty()
            gif_html = f'<div style="text-align:center;"><img src="data:image/gif;base64,{gif_b64}" alt="loading" style="max-width:220px;"/></div>'
            placeholder.markdown(gif_html, unsafe_allow_html=True)

        response = client.models.generate_content(
            model=model,
            contents=contents,
            config=types.GenerateContentConfig()
        )

        # 応答を受け取ったらGIFを消す
        if placeholder is not None:
            placeholder.empty()

        # アシスタントの応答を表示して履歴に追加
        avatar = f"data:image/gif;base64,{gif_b64}" if gif_b64 else "🧙"
        with st.chat_message("assistant", avatar=avatar):
            st.markdown(response.text)
        st.session_state.messages.append({"role": "assistant", "content": response.text})

# 右カラム：GIF画像を常に表示
with col2:
    if gif_b64:
        gif_html = f'<div style="text-align:center;"><img src="data:image/gif;base64,{gif_b64}" alt="loading" style="max-width:100%;"/></div>'
        st.markdown(gif_html, unsafe_allow_html=True)
