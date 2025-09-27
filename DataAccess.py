import pandas as pd
from supabase import create_client, Client
import os

# --- Supabaseの接続情報 ---
# 環境変数から取得するか、直接指定してください。
# 例: SUPABASE_URL = "https://your-project-id.supabase.co"
# 例: SUPABASE_KEY = "your-anon-key"
SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://whnoqtixmzshxxygvinu.supabase.co")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "sb_publishable_c_i4JhAt-ahbsa9mqV-5cQ_fGchLncp")

################################
## タスク一覧を取得する関数
################################
def get_tasks_by_login_id_from_supabase() -> pd.DataFrame:
    """
    Supabaseからデータを取得し、タスク一覧を返します。
    """
    try:
        # Supabaseクライアントを初期化
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        
        # データを取得
        task_table_data = supabase.from_('タスクテーブル').select('*').execute()
        task_master_data = supabase.from_('タスクマスターテーブル').select('*').execute()
        university_master_data = supabase.from_('大学名マスターテーブル').select('*').execute()
        due_date_master_data = supabase.from_('日付マスターテーブル').select('*').execute()
        
        # データをpandas DataFrameに変換
        # DB側のカラム名が小文字であれば、Pandasも小文字で読み込みます
        user_tasks = pd.DataFrame(task_table_data.data)
        task_master = pd.DataFrame(task_master_data.data)
        university_master = pd.DataFrame(university_master_data.data)
        due_date_master = pd.DataFrame(due_date_master_data.data)

        # user_tasksが空の場合の早期リターン
        if user_tasks.empty:
            return pd.DataFrame(columns=[
                '大学学部名', 'タスク名', '実施日/期日', '完了ステータス', 'お気に入り'
            ])
        
        # すべてのカラムが小文字であることを前提とし、変換処理は削除
        
    except Exception as e:
        print(f"データの取得中にエラーが発生しました: {e}")
        return pd.DataFrame() # エラー時は空のDataFrameを返す

    # 各テーブルと結合して必要な情報を取得します (すべて小文字で統一)
    # 1. 大学名マスターテーブルと結合
    df = pd.merge(user_tasks, university_master, on='universityid', how='left')

    # 2. タスクマスターテーブルと結合
    df = pd.merge(df, task_master, on='taskid', how='left')

    # 3. 日付マスターテーブルと結合
    # DB側で日付マスターテーブルの主キーも小文字 (universityid, taskid) になっていることを前提とします
    df = pd.merge(df, due_date_master, on=['universityid', 'taskid'], how='left')

    # 必要な列だけを抽出します
    result_df = df[['universityname', 'taskname', 'duedate', 'statusflag', 'favoriteflag']]

    # DataFrameの列名を日本語化
    result_df.columns = ['大学学部名', 'タスク名', '実施日/期日', '完了ステータス', 'お気に入り']

    return result_df

################################
## タスクのステータスを変更する関数
################################
def update_task_status(university_id: int, task_id: int, new_status: bool) -> dict:
    """
    タスクテーブルの指定されたタスクのStatus Flagを更新します。
    """
    try:
        # Supabaseクライアントを初期化
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        
        # データベースを更新
        # カラム名が小文字であることを前提
        response = supabase.from_('タスクテーブル').update(
            {'statusflag': new_status}
        ).eq('universityid', university_id
        ).eq('taskid', task_id
        ).execute()

        # 更新が成功したか確認
        if response.data:
            print(f"タスク (universityid: {university_id}, Task ID: {task_id}) のステータスを {new_status} に更新しました。")
            return {"status": "success", "data": response.data}
        else:
            print(f"指定されたタスクが見つからないか、更新に失敗しました。")
            return {"status": "failure", "error": "No matching task found or update failed."}
            
    except Exception as e:
        print(f"タスクの更新中にエラーが発生しました: {e}")
        return {"status": "error", "error": str(e)}


################################
## タスクのお気に入りを変更する関数
################################
def update_favorite_status(university_id: int, task_id: int, new_favorite: bool) -> dict:
    """
    タスクテーブルの指定されたタスクのfavorite Flagを更新します。
    """
    try:
        # Supabaseクライアントを初期化
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        
        # データベースを更新
        # カラム名が小文字であることを前提
        response = supabase.from_('タスクテーブル').update(
            {'favoriteflag': new_favorite}
        ).eq('universityid', university_id
        ).eq('taskid', task_id
        ).execute()

        # 更新が成功したか確認
        if response.data:
            print(f"タスク (universityid: {university_id}, Task ID: {task_id}) のステータスを {new_favorite} に更新しました。")
            return {"favorite": "success", "data": response.data}
        else:
            print(f"指定されたタスクが見つからないか、更新に失敗しました。")
            return {"favorite": "failure", "error": "No matching task found or update failed."}
            
    except Exception as e:
        print(f"タスクの更新中にエラーが発生しました: {e}")
        return {"favorite": "error", "error": str(e)}


################################
## タスクを新規登録する関数
################################
def add_tasks_for_user(university_id: int) -> dict:
    """
    指定された大学の全タスクをユーザーのタスクテーブルに追加します。
    """
    try:
        # Supabaseクライアントを初期化
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        
        # 1. タスクマスターテーブルから全てのTask IDを取得
        # カラム名が小文字であることを前提
        task_master_data = supabase.from_('タスクマスターテーブル').select('taskid').execute()
        if not task_master_data.data:
            return {"status": "failure", "error": "タスクマスターテーブルにデータがありません。"}

        task_ids_to_add = [task['taskid'] for task in task_master_data.data]

        # 2. タスクテーブルに挿入するデータを準備
        # カラム名が小文字であることを前提
        tasks_to_insert = []
        for task_id in task_ids_to_add:
            tasks_to_insert.append({
                "universityid": university_id,
                "taskid": task_id,
                "statusflag": False,
                "favoriteflag": False
            })

        # 3. データベースに一括挿入
        response = supabase.from_('タスクテーブル').insert(tasks_to_insert).execute()

        # 挿入が成功したか確認
        if response.data:
            print(f"universityid: {university_id} のタスクを {len(response.data)} 件追加しました。")
            return {"status": "success", "data": response.data}
        else:
            print(f"タスクの追加に失敗しました。")
            return {"status": "failure", "error": "Insertion failed."}
            
    except Exception as e:
        print(f"タスクの追加中にエラーが発生しました: {e}")
        return {"status": "error", "error": str(e)}



################################
## 未登録の大学名を取得する関数
################################

def get_unregistered_universities() -> list:
    """
    タスクテーブルにまだタスクが登録されていない大学名とIDの一覧を取得します。
    """
    try:
        # Supabaseクライアントを初期化
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        
        # 1. タスクテーブルから登録済みのUniversity IDのユニークなリストを取得
        registered_ids_response = supabase.from_('タスクテーブル').select('universityid').execute()
        registered_ids = [item['universityid'] for item in registered_ids_response.data]

        # 2. 大学名マスターテーブルの全データを取得
        university_master_response = supabase.from_('大学名マスターテーブル').select('universityid, universityname').execute()

        # .dataからDataFrameを作成
        university_master_df = pd.DataFrame(university_master_response.data)

        # 3. 登録済みIDのセットを作成して比較を効率化
        registered_id_set = set(registered_ids)
        
        # 4. 未登録のUniversity IDを特定
        unregistered_universities_df = university_master_df[
            ~university_master_df['universityid'].isin(registered_id_set)
        ]
        
        # 5. 未登録の大学名リストを抽出して返す
        unregistered_list = unregistered_universities_df[['universityid', 'universityname']].to_dict('records')
        
        # 戻り値のチェック
        if not unregistered_list:
            print("未登録の大学は見つかりませんでした。")
        # else:
            # print(f"未登録の大学名が {len(unregistered_list)} 件見つかりました。")

        return unregistered_list
            
    except Exception as e:
        print(f"データの取得中にエラーが発生しました: {e}")
        return []
    