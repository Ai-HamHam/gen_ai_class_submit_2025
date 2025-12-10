import os
from pathlib import Path
import streamlit as st
import base64
import streamlit.components.v1 as stc

from google import genai
from google.genai import types

# ページ設定
st.title("Gemini Chat")

# GIFファイルへのパスを解決して表示する

gif_files = [
    "TokeruMendako.gif",
    "MendakoKaiwaTyu.gif",
]

gif_b64_dict = {}

base_path = Path(__file__).resolve().parent
for gif_name in gif_files:
    gif_path = base_path / gif_name
    if gif_path.exists():
        try:
            gif_bytes = gif_path.read_bytes()
            gif_b64 = base64.b64encode(gif_bytes).decode()
            gif_b64_dict[gif_name] = gif_b64
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

# 過去のメッセージを表示
for message in st.session_state.messages:
    if message["role"] == "assistant":
        mendako_gif_b64 = gif_b64_dict.get("MendakoKaiwaTyu.gif")
        avatar = f"data:image/gif;base64,{mendako_gif_b64}" if mendako_gif_b64 else "🧙"
    else:
        avatar = "👤"
    with st.chat_message(message["role"], avatar=avatar):
        # アシスタントの場合は大きなGIFも表示
        if message["role"] == "assistant" and mendako_gif_b64:
            st.markdown(f'<div style="text-align:center;"><img src="data:image/gif;base64,{mendako_gif_b64}" alt="assistant" style="max-width:320px; max-height:320px;"/></div>', unsafe_allow_html=True)
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


    # Gemini APIにリクエストを送信する直前にロード中GIF（TokeruMendako.gif）を表示
    placeholder = None
    loading_gif_b64 = gif_b64_dict.get("TokeruMendako.gif")
    if loading_gif_b64:
        placeholder = st.empty()
        gif_html = f'<div style="text-align:center;"><img src="data:image/gif;base64,{loading_gif_b64}" alt="loading" style="max-width:320px; max-height:320px;"/></div>'
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
    mendako_gif_b64 = gif_b64_dict.get("MendakoKaiwaTyu.gif")
    avatar = f"data:image/gif;base64,{mendako_gif_b64}" if mendako_gif_b64 else "🧙"
    with st.chat_message("assistant", avatar=avatar):
        if mendako_gif_b64:
            st.markdown(f'<div style="text-align:center;"><img src="data:image/gif;base64,{mendako_gif_b64}" alt="assistant" style="max-width:320px; max-height:320px;"/></div>', unsafe_allow_html=True)
        st.markdown(response.text)
    st.session_state.messages.append({"role": "assistant", "content": response.text})
