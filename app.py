
import streamlit as st
import openai
import os

# テキストデータの読み込み関数
@st.cache_data
def load_text_data(file_path):
    abs_path = os.path.join(os.path.dirname(__file__), file_path)
    
    # 別のエンコーディング（例: shift_jis）を試してみる
    with open(abs_path, "r", encoding="shift_jis") as file:
        text_data = file.read()
    
    return text_data

# Toshishunのテキストを読み込む
text_data = load_text_data("toshishun.txt")

st.write("Toshishunのテキストデータ:")
st.text_area("テキストデータ", text_data, height=300)


# Streamlit Community Cloudの「Secrets」からOpenAI API keyを取得
openai.api_key = st.secrets.OpenAIAPI.openai_api_key

# st.session_stateを使いメッセージのやりとりを保存
if "messages" not in st.session_state:
    st.session_state["messages"] = [
        {"role": "system", "content": st.secrets.AppSettings.chatbot_setting} 
    ]
    
# チャットボットとやりとりする関数
def communicate():
    messages = st.session_state["messages"]

    user_message = {"role": "user", "content": st.session_state["user_input"]}
    messages.append(user_message)

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=messages
    )

    bot_message = response["choices"][0]["message"]
    messages.append(bot_message)

    st.session_state["user_input"] = ""  # 入力欄を消去


# ユーザーインターフェイスの構築
st.title("My AI Assistant")
st.write("ChatGPT APIを使ったチャットボットです。")

user_input = st.text_input("メッセージを入力してください。", key="user_input", on_change=communicate)

if st.session_state["messages"]:
    messages = st.session_state["messages"]

    for message in reversed(messages[1:]):  # 直近のメッセージを上に
        speaker = "🙂"
        if message["role"]=="assistant":
            speaker="🤖"

        st.write(speaker + ": " + message["content"])
