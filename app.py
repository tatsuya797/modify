import streamlit as st
import openai
import os
import zipfile
import tempfile
from pathlib import Path
from text_preprocessing import save_cleanse_text  # 前処理の関数をインポート

# ZIPファイルを解凍する関数
@st.cache_resource
def extract_zip(file):
    temp_dir = tempfile.mkdtemp()
    try:
        with zipfile.ZipFile(file, 'r') as zip_ref:
            zip_ref.extractall(temp_dir)
        st.write(f"ZIPファイルを {temp_dir} に解凍しました。")
    except zipfile.BadZipFile:
        st.error("ZIPファイルが壊れています。正しいZIPファイルをアップロードしてください。")
        st.stop()
    except Exception as e:
        st.error(f"ZIPファイルの解凍中にエラーが発生しました: {e}")
        st.stop()
    return temp_dir

# テキストデータを再帰的に読み込む関数
@st.cache_data
def load_all_texts_from_directory(directory):
    all_texts = ""
    file_count = 0  # 読み込んだファイルの数
    failed_files = []

    # 試行するエンコーディングのリスト
    encodings = ['utf-8', 'shift_jis', 'iso-2022-jp']

    for root, dirs, files in os.walk(directory):
        # __MACOSX ディレクトリをスキップ
        if '__MACOSX' in root:
            continue
        for file in files:
            # ._ で始まるファイルをスキップ
            if file.startswith('._'):
                continue
            if file.endswith(".txt"):
                file_path = os.path.join(root, file)
                success = False
                for enc in encodings:
                    try:
                        with open(file_path, "r", encoding=enc) as f:
                            content = f.read()
                            all_texts += content + "\n"
                        file_count += 1
                        success = True
                        st.write(f"ファイル {file_path} を {enc} エンコーディングで読み込みました。")
                        break  # 読み込みに成功したら次のファイルへ
                    except UnicodeDecodeError as e:
                        st.warning(f"ファイル {file_path} の {enc} エンコーディングでの読み込みに失敗しました。次のエンコーディングを試みます。")
                    except Exception as e:
                        st.warning(f"ファイル {file_path} の読み込み中に予期せぬエラーが発生しました: {e}")
                        break  # その他のエラーが発生した場合は次のファイルへ
                if not success:
                    failed_files.append(file_path)
    
    if failed_files:
        st.error("以下のファイルの読み込みに失敗しました：")
        for f in failed_files:
            st.error(f)
    st.write(f"読み込んだファイル数: {file_count}個")
    return all_texts

# 前処理後のテキストファイルを読み込む関数
@st.cache_data
def load_processed_texts(processed_files):
    processed_texts = {}
    for file_path in processed_files:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                processed_texts[file_path.name] = f.read()
        except UnicodeDecodeError as e:
            st.warning(f"ファイル {file_path} の読み込みに失敗しました。エンコーディングエラー: {e}")
        except Exception as e:
            st.warning(f"ファイル {file_path} の読み込みに予期せぬエラーが発生しました: {e}")
    return processed_texts

# テキストデータを処理する関数
def process_text_files(directory):
    processed_texts = []  # 処理後のテキストを格納するリスト
    text_files = list(Path(directory).glob('**/*.txt'))  # サブフォルダも含む
    for text_file in text_files:
        try:
            save_cleanse_text(text_file)  # 前処理関数を呼び出し
            # 前処理後のファイル名を生成
            processed_file_name = f"{text_file.stem}_clns_utf-8.txt"
            processed_file_path = Path(directory) / processed_file_name
            if processed_file_path.exists():
                processed_texts.append(processed_file_path)
                st.write(f"処理後のファイル {processed_file_path} を生成しました。")
            else:
                st.warning(f"処理後のファイル {processed_file_path} が見つかりません。")
        except Exception as e:
            st.warning(f"ファイル {text_file} の前処理中にエラーが発生しました: {e}")
    return processed_texts

# チャットボットとやりとりする関数
def communicate():
    messages = st.session_state["messages"]
    user_message = {"role": "user", "content": st.session_state["user_input"]}
    messages.append(user_message)

    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=messages
        )
    except Exception as e:
        st.error(f"OpenAI API エラー: {e}")
        return

    bot_message = response["choices"][0]["message"]
    messages.append(bot_message)
    st.session_state["user_input"] = ""  # 入力欄を消去

# Streamlitアプリケーションの実行部分
def main():
    st.title("芥川龍之介AIアシスタント")
    st.write("芥川龍之介の作品に基づくチャットボットです。")

    # ZIPファイルのアップロード
    uploaded_file = st.file_uploader("ZIPファイルをアップロードしてください。", type="zip")

    if uploaded_file is not None:
        # ZIPファイルを一時ファイルとして保存
        with tempfile.NamedTemporaryFile(delete=False, suffix=".zip") as tmp_file:
            tmp_file.write(uploaded_file.read())
            tmp_zip_path = tmp_file.name

        # ZIPファイルを解凍
        txtfile_879_directory = extract_zip(tmp_zip_path)

        # 解凍後のファイル一覧を表示（デバッグ用）
        st.write("解凍されたディレクトリ内のファイル一覧:")
        for path in Path(txtfile_879_directory).rglob('*'):
            st.write(path)

        # 全テキストデータを読み込む
        all_akutagawa_texts = load_all_texts_from_directory(txtfile_879_directory)

        # デバッグ用: 読み込んだテキストの長さを表示
        st.write(f"読み込んだテキストの長さ: {len(all_akutagawa_texts)}文字")

        # 読み込んだテキストを確認
        st.text_area("テキストデータ", all_akutagawa_texts, height=300)

        # テキストファイルを処理するボタン
        if st.button("テキストファイルを処理する"):
            processed_text_files = process_text_files(txtfile_879_directory)  # テキストファイルの処理を実行
            if processed_text_files:
                st.success("テキストファイルの処理が完了しました。")

                # 前処理後のテキストを読み込む
                processed_texts = load_processed_texts(processed_text_files)

                # 処理後のテキストを表示
                st.subheader("処理後のテキスト")
                for file_name, content in processed_texts.items():
                    with st.expander(f"ファイル: {file_name}"):
                        st.text_area(file_name, content, height=200)
            else:
                st.warning("処理後のテキストファイルが見つかりませんでした。")

        # Streamlit Community Cloudの「Secrets」からOpenAI API keyを取得
        try:
            openai.api_key = st.secrets["OpenAIAPI"]["openai_api_key"]
        except KeyError as e:
            st.error(f"シークレットの設定に問題があります: {e}")
            st.stop()

        # st.session_stateを使いメッセージのやりとりを保存
        if "messages" not in st.session_state:
            try:
                chatbot_setting = st.secrets["AppSettings"]["chatbot_setting"]
            except KeyError as e:
                st.error(f"シークレットの設定に問題があります: {e}")
                st.stop()
            st.session_state["messages"] = [
                {"role": "system", "content": chatbot_setting} 
            ]

        # ユーザーのメッセージ入力
        user_input = st.text_input("メッセージを入力してください。", key="user_input", on_change=communicate)

        if st.session_state["messages"]:
            messages = st.session_state["messages"]
            for message in reversed(messages[1:]):  # 直近のメッセージを上に
                speaker = "🙂" if message["role"] == "user" else "🤖"
                st.write(speaker + ": " + message["content"])

        # 一時ファイルの削除
        os.remove(tmp_zip_path)

if __name__ == "__main__":
    main()

