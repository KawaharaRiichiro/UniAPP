import streamlit as st
import pandas as pd # DataFrameを扱うため追加

# DataAccess.pyから必要な関数をインポート
from DataAccess import (
    get_tasks_by_login_id_from_supabase, 
    get_unregistered_universities, 
    add_tasks_for_user,
    update_favorite_status,
    update_task_status
)


# --- 画面設定 ---
st.set_page_config(
    page_title="大学受験出願補助アプリ",
    layout="wide"
)

# --- Streamlitのデータキャッシュ機能を使って、Supabaseからのデータ取得関数を定義 ---
# アプリの再実行時にデータベースからデータを再取得するのを防ぎ、パフォーマンスを向上させます。
@st.cache_data
def load_tasks_data():
    """DataAccessからタスク一覧を取得し、キャッシュする関数"""
    # DataAccess.pyで定義された関数を呼び出す
    return get_tasks_by_login_id_from_supabase()

# --- メイン画面 ---
st.title("大学受験出願補助アプリ")
st.caption("あなたの大学受験をサポートします。")

# --- ページ管理のためのセッション状態を初期化 ---
if 'page' not in st.session_state:
    st.session_state.page = "タスク一覧"

# --- ナビゲーションボタン ---
col1, col2, col3 = st.columns(3)

with col1:
    if st.button("タスク一覧", use_container_width=True, type="primary" if st.session_state.page == "タスク一覧" else "secondary"):
        st.session_state.page = "タスク一覧"

with col2:
    if st.button("スケジュール", use_container_width=True, type="primary" if st.session_state.page == "スケジュール" else "secondary"):
        st.session_state.page = "スケジュール"

with col3:
    if st.button("大学追加", use_container_width=True, type="primary" if st.session_state.page == "大学追加" else "secondary"):
        st.session_state.page = "大学追加"

st.divider()

# --- 選択されたページに応じてコンテンツを表示 ---
if st.session_state.page == "タスク一覧":
    st.header("タスク一覧")
    st.cache_data.clear() 
    st.write("ここでは、出願に必要なタスクを一覧で確認・管理できます。")
    
    # データをロードし、進捗状況を表示
    with st.spinner('タスクデータをロード中...'):
        tasks_df = load_tasks_data() # キャッシュされた関数を呼び出し、タスク一覧を取得
    
    # データの表示
    if not tasks_df.empty:
        # 取得したDataFrameをStreamlitに表示
        st.dataframe(tasks_df, use_container_width=True)
    else:
        # データが空の場合のメッセージ
        st.warning("タスクデータが見つからないか、データベースからのロード中にエラーが発生しました。")


elif st.session_state.page == "スケジュール":
    st.header("スケジュール")
    st.write("出願関連のスケジュールをカレンダー形式で確認できます。")
    # 今後のステップで、ここにカレンダー機能を追加していきます。
    st.info("（ここにスケジュールカレンダーが表示される予定です）")

# main.py の該当箇所

elif st.session_state.page == "大学追加":
    st.header("大学追加")
    st.write("受験する大学や学部を追加登録します。")

    # 1. 未登録の大学名とIDのリストを取得
    unregistered_universities_data = get_unregistered_universities()
    
    if unregistered_universities_data:
        # 選択肢として表示するための大学名リストを作成
        university_names = [d['universityname'] for d in unregistered_universities_data]
        
        # 2. ドロップダウンリストを表示
        selected_university_name = st.selectbox(
            "追加する大学を選択してください:",
            university_names,
            index=None, # 初期値はなし
            placeholder="大学名を選択..."
        )

        # 3. 追加ボタンの配置と処理
        if selected_university_name:
            # 選択された大学名から対応する University ID を検索
            selected_university_id = next(
                (d['universityid'] for d in unregistered_universities_data if d['universityname'] == selected_university_name), 
                None
            )
            
            if st.button(f"**{selected_university_name}** のタスクを追加", type="primary"):
                
                if selected_university_id is not None:
                    with st.spinner(f'{selected_university_name}のタスクを登録中...'):
                        result = add_tasks_for_user(selected_university_id)
                    
                    if result.get("status") == "success":
                        st.success(f"**{selected_university_name}** の出願タスクを正常に追加しました！")
                        # タスク一覧ページを最新の状態にするため、キャッシュをクリア
                        st.cache_data.clear()
                        # 成功後、タスク一覧ページに遷移
                        st.session_state.page = "タスク一覧"
                        st.rerun()
                    else:
                        st.error(f"タスクの追加に失敗しました。エラー: {result.get('error')}")
                else:
                    st.error("エラー：選択された大学のIDが見つかりませんでした。")
    else:
        st.success("すべての大学のタスクが登録済みです！")
