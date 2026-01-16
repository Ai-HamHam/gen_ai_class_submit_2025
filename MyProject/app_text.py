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
    "MendakoKaiten.gif",
    "MendakoOdoroki.gif",
    "MendakoNaki.gif",

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
    # 表示中の大きなGIFを保持（デフォルトは会話用GIF）
    st.session_state.selected_mendako = "MendakoKaiwaTyu.gif"

# 既にセッションにキーがない場合の保険
if "selected_mendako" not in st.session_state:
    st.session_state.selected_mendako = "MendakoKaiwaTyu.gif"
# 一度だけ表示する大きなGIFを保持する（ポジティブ判定で設定され、表示後にリセットされる）
if "one_time_mendako" not in st.session_state:
    st.session_state.one_time_mendako = None

# ユーザー入力から「嬉しい/楽しい」を検出する簡易判定
positive_keywords = [
    "嬉しい", "うれしい", "嬉", "楽しい", "たのしい", "楽", "感謝", "ありがとう", "有難う", "有り難う","最高", "やった", "よかった", "良", "楽しかった"
]

def contains_positive(text: str) -> bool:
    if not text:
        return False
    for kw in positive_keywords:
        if kw in text:
            return True
    return False

negative_keywords = [
    "かなしい", "悲", "寂", "さびしい", "怒", "むかつく", "悪", "嫌", "いやだ", "つらい", "辛", "苦","疲", "痛", "病", "しんどい"
]

def contains_negative(text: str) -> bool:
    if not text:
        return False
    for kw in negative_keywords:
        if kw in text:
            return True
    return False

surprise_keywords = [
    "びっくり", "驚", "おどろき", "まじ", "本当", "ほんと", "えっ", "えー", "うそ", "ウソ", "信じられない", "しんじられない", "嘘", "ヤバい", "やばい"
]

def contains_surprise(text: str) -> bool:
    if not text:
        return False
    for kw in surprise_keywords:
        if kw in text:
            return True
    return False


# 過去のメッセージを表示
for message in st.session_state.messages:
    # アバターは常に MendakoKaiwaTyu.gif を使用
    fixed_avatar_b64 = gif_b64_dict.get("MendakoKaiwaTyu.gif")
    avatar = f"data:image/gif;base64,{fixed_avatar_b64}" if fixed_avatar_b64 else "🧙" if message["role"] == "assistant" else "👤"
    with st.chat_message(message["role"], avatar=avatar):
        # アシスタントの場合は、そのメッセージで選ばれた大きなGIFを表示（履歴に保存されていればそれを使う）
        if message["role"] == "assistant":
            big_gif_name = message.get("mendako", "MendakoKaiwaTyu.gif")
            big_gif_b64 = gif_b64_dict.get(big_gif_name)
            if big_gif_b64:
                st.markdown(f'<div style="text-align:center;"><img src="data:image/gif;base64,{big_gif_b64}" alt="assistant" style="max-width:320px; max-height:320px;"/></div>', unsafe_allow_html=True)
        st.markdown(message["content"])

# ユーザー入力を受け取る
if prompt := st.chat_input("メッセージを入力してください"):
    # ユーザーメッセージを表示して履歴に追加
    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    # ユーザーの文章からポジティブな表現を検出し、表示する大きなGIFを決定
    positive = contains_positive(prompt)
    # ポジティブなら次回のアシスタント応答で一度だけMendakoKaiten.gifを表示する
    if positive:
        st.session_state.one_time_mendako = "MendakoKaiten.gif"
    # 表示対象は、一時設定があればそれを優先し、なければ現在の選択を使用
    selected_mendako = st.session_state.one_time_mendako or st.session_state.selected_mendako

    # ユーザーの文章からネガティブな表現を検出し、表示する大きなGIFを決定
    negative = contains_negative(prompt)
    if negative:
        st.session_state.one_time_mendako = "MendakoNaki.gif"
    # 表示対象は、一時設定があればそれを優先し、なければ現在の選択を使用
    selected_mendako = st.session_state.one_time_mendako or st.session_state.selected_mendako

    # ユーザーの文章から驚きの表現を検出し、表示する大きなGIFを決定
    surprise = contains_surprise(prompt)
    if surprise:
        st.session_state.one_time_mendako = "MendakoOdoroki.gif"
    # 表示対象は、一時設定があればそれを優先し、なければ現在の選択を使用
    selected_mendako = st.session_state.one_time_mendako or st.session_state.selected_mendako



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

    # アシスタントの応答を表示して履歴に追加（選択されたGIFを使用）
    # avatar は常に MendakoKaiwaTyu.gif を使う（小さいアバターとして渡す）
    fixed_avatar_b64 = gif_b64_dict.get("MendakoKaiwaTyu.gif")
    avatar = f"data:image/gif;base64,{fixed_avatar_b64}" if fixed_avatar_b64 else "🧙"
    with st.chat_message("assistant", avatar=avatar):
        # 本文上部に表示する大きなGIFはセッションで保持されているものを使用
        mendako_gif_b64 = gif_b64_dict.get(selected_mendako)
        if mendako_gif_b64:
            st.markdown(f'<div style="text-align:center;"><img src="data:image/gif;base64,{mendako_gif_b64}" alt="assistant" style="max-width:320px; max-height:320px;"/></div>', unsafe_allow_html=True)
        st.markdown(response.text)
    # 履歴には、その時点で表示している大きなGIF名も保存しておく
    st.session_state.messages.append({"role": "assistant", "content": response.text, "mendako": selected_mendako})
    # one_time_mendako が使われた場合はリセット（次のポジティブ判定まで保持しない）
    if st.session_state.one_time_mendako is not None:
        st.session_state.one_time_mendako = None
