import streamlit as st
import openai
import os
import zipfile
import tempfile
from pathlib import Path
from text_preprocessing import save_cleanse_text  # 前処理の関数をインポート

# ZIPファイルを解凍する関数
@st.cache_resource
def extract_zip(zip_path, last_modified):
    temp_dir = tempfile.mkdtemp()
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(temp_dir)
        st.write(f"ZIPファイルを {temp_dir} に解凍しました。")
    except zipfile.BadZipFile:
        st.error("ZIPファイルが壊れています。正しいZIPファイルをアップロードしてください。")
        st.stop()
    except FileNotFoundError:
        st.error("指定されたZIPファイルが見つかりません。パスを確認してください。")
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

    for root, dirs, files in os.walk(directory):
        # __MACOSXディレクトリをスキップ
        if "__MACOSX" in root:
            continue

        for file in files:
            # ._で始まるファイルをスキップ
            if file.startswith("._"):
                continue

            if file.endswith(".txt"):
                file_path = os.path.join(root, file)
                try:
                    # まずはutf-8で試す
                    with open(file_path, "r", encoding="utf-8") as f:
                        all_texts += f.read() + "\n"
                    file_count += 1
                except UnicodeDecodeError as e1:
                    try:
                        # 次にshift_jisで試す
                        with open(file_path, "r", encoding="shift_jis") as f:
                            all_texts += f.read() + "\n"
                        file_count += 1
                    except UnicodeDecodeError as e2:
                        # それでも失敗した場合はスキップ
                        st.warning(f"ファイル {file_path} の読み込みに失敗しました。エンコーディングエラー: {e2}")
                    except Exception as e:
                        st.warning(f"ファイル {file_path} の読み込みに予期せぬエラーが発生しました: {e}")
                except Exception as e:
                    st.warning(f"ファイル {file_path} の読み込みに予期せぬエラーが発生しました: {e}")

    st.write(f"読み込んだファイル数: {file_count}個")
    return all_texts

# テキストデータを処理する関数
def process_text_files():
    processed_texts = []  # 処理後のテキストを格納するリスト
    text_files = list(txtfile_879_directory.glob('**/*.txt'))  # サブフォルダも含む
    for text_file in text_files:
        save_cleanse_text(text_file)  # 前処理関数を呼び出し
        # 前処理後の結果をリストに追加（保存場所に応じて変更）
        # ここでは仮にファイル名に基づいて読み込んでいますが、実際には適切な処理が必要です。
        processed_texts.append(f"{text_file.stem}_clns_utf-8.txt")  # 仮の処理

    return processed_texts

# Streamlitアプリケーションの実行部分
def main():
    st.title("芥川龍之介AIアシスタント")
    st.write("芥川龍之介の作品に基づくチャットボットです。")

    # ZIPファイルのパスを指定
    zip_file_path = Path("txtfile_879.zip")  # 実際のZIPファイル名に合わせて変更してください

    # ZIPファイルの最終更新日時を取得
    try:
        last_modified = os.path.getmtime(zip_file_path)
    except FileNotFoundError:
        st.error("指定されたZIPファイルが見つかりません。パスを確認してください。")
        st.stop()

    # ZIPファイルを解凍
    txtfile_879_directory = Path(extract_zip(zip_file_path, last_modified))

    # 解凍後のファイル一覧を表示（デバッグ用）
    st.write("解凍されたディレクトリ内のファイル一覧:")
    for path in txtfile_879_directory.rglob('*'):
        st.write(path)

    # 全テキストデータを読み込む
    all_akutagawa_texts = load_all_texts_from_directory(txtfile_879_directory)

    # デバッグ用: 読み込んだテキストの長さを表示
    st.write(f"読み込んだテキストの長さ: {len(all_akutagawa_texts)}文字")

    # 読み込んだテキストを確認
    st.text_area("テキストデータ", all_akutagawa_texts, height=300)

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

    # テキストファイルを処理するボタン
    if st.button("テキストファイルを処理する"):
        processed_texts = process_text_files()  # テキストファイルの処理を実行
        st.success("テキストファイルの処理が完了しました。")

        # 処理後のテキストを表示
        st.subheader("処理後のテキスト")
        for processed_file in processed_texts:
            st.write(processed_file)  # 各処理後のファイル名を表示

    # ユーザーのメッセージ入力
    user_input = st.text_input("メッセージを入力してください。", key="user_input", on_change=communicate)

    if st.session_state["messages"]:
        messages = st.session_state["messages"]
        for message in reversed(messages[1:]):  # 直近のメッセージを上に
            speaker = "🙂" if message["role"] == "user" else "🤖"
            st.write(speaker + ": " + message["content"])

if __name__ == "__main__":
    main()


