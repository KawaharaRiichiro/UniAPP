import streamlit as st
import pandas as pd # DataFrameを扱うため追加
from streamlit_calendar import calendar
from datetime import timedelta

# DataAccess.pyから必要な関数をインポート
from DataAccess import (
    get_tasks_by_login_id_from_supabase, 
    get_unregistered_universities, 
    add_tasks_for_user,
    update_task_status,
    update_favorite_status 
)


# --- 画面設定 ---
st.set_page_config(
    page_title="大学受験出願補助アプリ",
    layout="wide"
)

# --- Streamlitのデータキャッシュ機能を使って、Supabaseからのデータ取得関数を定義 ---
@st.cache_data
def load_tasks_data():
    """DataAccessからタスク一覧を取得し、キャッシュする関数"""
    return get_tasks_by_login_id_from_supabase()

# --- メイン画面 ---
st.title("大学受験出願補助アプリ")
st.caption("あなたの大学受験をサポートします。")

# --- ページ管理のためのセッション状態を初期化 ---
if 'page' not in st.session_state:
    st.session_state.page = "タスク一覧"
if 'add_success_message' not in st.session_state:
    st.session_state.add_success_message = None
# スケジュール用のサイドバー表示状態を管理
if 'sidebar_date' not in st.session_state:
    st.session_state.sidebar_date = None


# --- ナビゲーションボタン ---
col1, col2, col3 = st.columns(3)

with col1:
    if st.button("✅ タスク一覧", use_container_width=True, type="primary" if st.session_state.page == "タスク一覧" else "secondary"):
        st.session_state.page = "タスク一覧"

with col2:
    if st.button("🗓️ スケジュール", use_container_width=True, type="primary" if st.session_state.page == "スケジュール" else "secondary"):
        st.session_state.page = "スケジュール"

with col3:
    if st.button("➕ 大学追加", use_container_width=True, type="primary" if st.session_state.page == "大学追加" else "secondary"):
        st.session_state.page = "大学追加"

st.divider()

# --- 選択されたページに応じてコンテンツを表示 ---
if st.session_state.page == "タスク一覧":
    st.header("✅ タスク一覧")
    st.write("ここでは、出願に必要なタスクを一覧で確認・管理できます。**完了ステータス**やお気に入りをチェックして進捗を管理しましょう。")
    
    # データをロード
    with st.spinner('タスクデータをロード中...'):
        tasks_df = load_tasks_data() 
    
    # データの表示と編集ロジック
    if not tasks_df.empty:
        
        # ----------------------------------------
        # 1. フィルタリング機能
        # ----------------------------------------
        with st.container(border=True):
            st.markdown("##### 表示フィルター")
            filter_col1, filter_col2, _ = st.columns([1, 1, 3])
            
            status_options = ["すべて", "未完了のみ", "完了済みのみ"]
            with filter_col1:
                st.caption("完了ステータス") 
                selected_status_filter = st.selectbox(
                    "完了ステータス", options=status_options, key="status_filter",
                    label_visibility="collapsed"
                )
            
            favorite_options = ["すべて", "お気に入りのみ"]
            with filter_col2:
                st.caption("お気に入り") 
                selected_favorite_filter = st.selectbox(
                    "お気に入り", options=favorite_options, key="favorite_filter",
                    label_visibility="collapsed"
                )
        
        # フィルタリングの実行
        filtered_df = tasks_df.copy()
        if selected_status_filter == "未完了のみ":
            filtered_df = filtered_df[filtered_df['完了ステータス'] == False]
        elif selected_status_filter == "完了済みのみ":
            filtered_df = filtered_df[filtered_df['完了ステータス'] == True]

        if selected_favorite_filter == "お気に入りのみ":
            filtered_df = filtered_df[filtered_df['お気に入り'] == True]

        # st.divider() # コンテナで囲んだため、dividerは不要に
        
        # ----------------------------------------
        # 2. データエディタの表示とDB更新ロジック
        # ----------------------------------------
        if filtered_df.empty:
            st.info("現在のフィルター条件に一致するタスクはありません。")
        else:
            column_config = {
                "universityid": None, 
                "taskid": None,
                "完了ステータス": st.column_config.CheckboxColumn(default=False),
                "お気に入り": st.column_config.CheckboxColumn(default=False),
            }

            st.data_editor(
                filtered_df,
                column_config=column_config,
                hide_index=True,
                use_container_width=True,
                key="tasks_data_editor"
            )

            if 'edited_rows' in st.session_state.tasks_data_editor:
                edited_rows = st.session_state.tasks_data_editor['edited_rows']
                if edited_rows:
                    st.toast("タスク情報を更新しています...")
                    
                    for row_index, changes in edited_rows.items():
                        original_row = filtered_df.iloc[row_index]
                        university_id = int(original_row['universityid'])
                        task_id = int(original_row['taskid'])
                        
                        if '完了ステータス' in changes:
                            update_task_status(university_id, task_id, changes['完了ステータス'])
                        if 'お気に入り' in changes:
                            update_favorite_status(university_id, task_id, changes['お気に入り'])
                    
                    st.cache_data.clear()
                    st.toast("タスク情報が正常に更新されました！", icon="✅")
                    st.rerun() 
            
    else:
        st.info("現在登録されているタスクはありません。「大学追加」ページから大学を登録してください。")


elif st.session_state.page == "スケジュール":
    st.header("🗓️ スケジュール")
    st.write("出願関連のスケジュールをカレンダー形式で確認できます。日付をクリックすると、サイドバーにその日のタスクが表示されます。")

    with st.spinner('スケジュールデータをロード中...'):
        tasks_df = load_tasks_data()

    if tasks_df.empty:
        st.info("カレンダーに表示するタスクがありません。")
    else:
        # --- データ準備 (変更なし) ---
        color_palette = [
            "#FFADAD", "#FFD6A5", "#FDFFB6", "#CAFFBF", "#9BF6FF", 
            "#A0C4FF", "#BDB2FF", "#FFC6FF", "#FFFFFC", "#DDDDDD"
        ]
        unique_universities = tasks_df['大学学部名'].unique()
        university_colors = {
            uni: color_palette[i % len(color_palette)] 
            for i, uni in enumerate(unique_universities)
        }
        calendar_events = []
        valid_tasks_df = tasks_df[
            (tasks_df['完了ステータス'] == False) & 
            (pd.to_datetime(tasks_df['実施日/期日'], errors='coerce').notna())
        ].copy()
        valid_tasks_df['parsed_date'] = pd.to_datetime(valid_tasks_df['実施日/期日'], errors='coerce').dt.date

        for index, row in valid_tasks_df.iterrows():
            event_title = f"【{row['大学学部名']}】{row['タスク名']}"
            calendar_events.append({
                "title": event_title, "start": row['実施日/期日'], "allDay": True,
                "backgroundColor": university_colors.get(row['大学学部名'], "#DDDDDD"),
                "borderColor": university_colors.get(row['大学学部名'], "#DDDDDD"),
                "textColor": "#000000",
            })
        
        calendar_options = {
            "headerToolbar": {"left": "today,prev,next", "center": "title", "right": "dayGridMonth,timeGridWeek,timeGridDay"},
            "initialView": "dayGridMonth", "locale": "ja", "selectable": True,
        }

        # --- カレンダーの表示とクリック処理 ---
        clicked_info = calendar(events=calendar_events, options=calendar_options, key="schedule_calendar")

        if clicked_info and clicked_info.get("dateClick"):
            clicked_date_str = clicked_info["dateClick"]["date"]
            original_date = pd.to_datetime(clicked_date_str).date()
            # サイドバーに表示する日付をセッションに保存
            st.session_state.sidebar_date = original_date + timedelta(days=1)
            # st.rerun() # rerunは不要。セッション更新で再描画される

    # サイドバーに表示する日付がセッションに保存されている場合のみ、サイドバーを表示
    if st.session_state.sidebar_date:
        with st.sidebar:
            # 閉じるボタンのコールバック関数
            def close_sidebar():
                st.session_state.sidebar_date = None

            st.header(f"{st.session_state.sidebar_date.strftime('%Y-%m-%d')} のタスク")
            st.button("✖️ 閉じる", on_click=close_sidebar, use_container_width=True)
            st.divider()

            # サイドバーに表示するタスクをフィルタリング
            tasks_on_date = valid_tasks_df[valid_tasks_df['parsed_date'] == st.session_state.sidebar_date]

            if not tasks_on_date.empty:
                for index, row in tasks_on_date.iterrows():
                    university_id = int(row['universityid'])
                    task_id = int(row['taskid'])
                    
                    st.markdown(f"**{row['大学学部名']}**")
                    
                    checkbox_key = f"sidebar_task_{university_id}_{task_id}"
                    if st.checkbox(row['タスク名'], key=checkbox_key):
                        update_task_status(university_id, task_id, True)
                        st.toast(f"タスク「{row['タスク名']}」を完了しました！", icon="🎉")
                        st.cache_data.clear()
                        close_sidebar() # 完了したらサイドバーを閉じる
                        st.rerun()
            else:
                st.info("この日には未完了のタスクはありません。")


elif st.session_state.page == "大学追加":
    st.header("➕ 大学追加")
    st.write("受験する大学や学部を追加登録します。")

    if st.session_state.add_success_message:
        st.success(st.session_state.add_success_message)
        st.session_state.add_success_message = None

    unregistered_universities_data = get_unregistered_universities()
    
    if unregistered_universities_data:
        university_names = [d['universityname'] for d in unregistered_universities_data]
        
        selected_university_name = st.selectbox(
            "追加する大学を選択してください:",
            university_names,
            index=None,
            placeholder="大学名を選択..."
        )

        if selected_university_name:
            selected_university_id = next(
                (d['universityid'] for d in unregistered_universities_data if d['universityname'] == selected_university_name), 
                None
            )
            
            if st.button(f"**{selected_university_name}** のタスクを追加", type="primary"):
                
                if selected_university_id is not None:
                    with st.spinner(f'{selected_university_name}のタスクを登録中...'):
                        result = add_tasks_for_user(selected_university_id)
                    
                    if result.get("status") == "success":
                        st.session_state.add_success_message = f"**{selected_university_name}** の出願タスクを正常に追加しました！"
                        st.cache_data.clear()
                        st.rerun()
                    else:
                        st.error(f"タスクの追加に失敗しました。エラー: {result.get('error')}")
                else:
                    st.error("エラー：選択された大学のIDが見つかりませんでした。")
    else:
        st.success("すべての大学のタスクが登録済みです！")

