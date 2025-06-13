import os
import json
import datetime
from flask import Flask, request, redirect, url_for, session, jsonify
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import psycopg2
from psycopg2.extras import Json
from dotenv import load_dotenv

# 開発環境ではOAuth2のHTTPSチェックを無効化
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

# 環境変数の読み込み
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY')

# Google OAuth設定
CLIENT_CONFIG = {
    "web": {
        "client_id": os.getenv("GOOGLE_CLIENT_ID"),
        "client_secret": os.getenv("GOOGLE_CLIENT_SECRET"),
        "redirect_uris": [os.getenv("GOOGLE_REDIRECT_URI")],
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token"
    }
}

# スコープの設定
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']

# PostgreSQLへの接続
def get_db_connection():
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        raise ValueError("DATABASE_URL environment variable is not set or is empty. Please check Heroku Config Vars.")
    conn = psycopg2.connect(database_url)
    conn.autocommit = True
    return conn

# データベースの初期化
def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # credentialsテーブルが存在しない場合は作成
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS credentials (
        id SERIAL PRIMARY KEY,
        user_id VARCHAR(255) NOT NULL UNIQUE,
        token_json TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # インデックスの作成
    cursor.execute('''
    CREATE INDEX IF NOT EXISTS idx_credentials_user_id ON credentials(user_id)
    ''')
    
    cursor.close()
    conn.close()

# データベース初期化フラグ
db_initialized = False

# リクエスト前にDBを初期化
@app.before_request
def before_request():
    global db_initialized
    if not db_initialized:
        init_db()
        db_initialized = True

# トップページ
@app.route('/')
def index():
    redirect_url = os.getenv("GOOGLE_REDIRECT_URI")
    return f'''
    <h1>Google Calendar OAuth認証</h1>
    <p>リダイレクトURL: {redirect_url}</p>
    <a href="/authorize">Google Calendarと連携する</a>
    '''

# 認証開始
@app.route('/authorize')
def authorize():
    # OAuth2認証フローの作成
    flow = Flow.from_client_config(
        CLIENT_CONFIG,
        scopes=SCOPES
    )
    flow.redirect_uri = os.getenv('GOOGLE_REDIRECT_URI')
    
    # 認証URLの生成
    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true',
        prompt='consent'
    )
    
    # 状態をセッションに保存
    session['state'] = state
    
    # ユーザーをGoogle認証ページにリダイレクト
    return redirect(authorization_url)

# コールバック処理
@app.route('/oauth2callback')
def oauth2callback():
    # 状態の検証
    state = session.get('state')
    if state is None:
        return redirect(url_for('index'))
    
    # OAuth2認証フローの作成
    flow = Flow.from_client_config(
        CLIENT_CONFIG,
        scopes=SCOPES,
        state=state
    )
    flow.redirect_uri = os.getenv('GOOGLE_REDIRECT_URI')
    
    # 認証コードの取得と交換
    # 完全なURLを構築
    scheme = request.headers.get('X-Forwarded-Proto', request.scheme)
    host = request.headers.get('X-Forwarded-Host', request.host)
    authorization_response = f"{scheme}://{host}{request.full_path}"
    print(f"Authorization Response URL: {authorization_response}")
    
    flow.fetch_token(authorization_response=authorization_response)
    
    # 認証情報の取得
    credentials = flow.credentials
    print(f"Credentials obtained: {credentials.valid}")
    print(f"Token: {credentials.token[:10]}...")
    print(f"Has refresh token: {bool(credentials.refresh_token)}")
    print(f"Scopes: {credentials.scopes}")
    print(f"Expiry: {credentials.expiry}")
    
    
    # ユーザー情報の取得
    # ユーザーIDを固定値にしておきます
    # 本番環境では適切な方法でユーザーIDを取得する必要があります
    user_id = "Ud4cc4c3b7e9ec9875f9951d1d0352a7a"  # デモ用に固定値を使用
    
    # 認証情報をJSONに変換
    credentials_json = {
        'token': credentials.token,
        'refresh_token': credentials.refresh_token,
        'token_uri': credentials.token_uri,
        'client_id': credentials.client_id,
        'client_secret': credentials.client_secret,
        'scopes': credentials.scopes
    }
    
    # データベースに保存
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # UPSERTクエリ（存在すれば更新、なければ挿入）
    cursor.execute('''
    INSERT INTO credentials (user_id, token_json)
    VALUES (%s, %s)
    ON CONFLICT (user_id) 
    DO UPDATE SET 
        token_json = %s,
        updated_at = CURRENT_TIMESTAMP
    ''', (user_id, json.dumps(credentials_json), json.dumps(credentials_json)))
    
    cursor.close()
    conn.close()
    
    return '''
    <h1>認証成功</h1>
    <p>Google Calendarとの連携が完了しました。</p>
    <a href="/calendar">カレンダー情報を表示</a>
    '''

# カレンダー情報の取得と表示
@app.route('/calendar')
def get_calendar():
    # ユーザーIDの取得（本来はセッションや認証から取得）
    # デモ用に簡易実装
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 最新の認証情報を取得
    cursor.execute('SELECT user_id, token_json FROM credentials ORDER BY updated_at DESC LIMIT 1')
    result = cursor.fetchone()
    
    if not result:
        cursor.close()
        conn.close()
        return '認証情報がありません。<a href="/authorize">認証する</a>'
    
    user_id, token_json = result
    credentials_dict = json.loads(token_json)
    
    # 認証情報の復元
    credentials = Credentials(
        token=credentials_dict['token'],
        refresh_token=credentials_dict['refresh_token'],
        token_uri=credentials_dict['token_uri'],
        client_id=credentials_dict['client_id'],
        client_secret=credentials_dict['client_secret'],
        scopes=credentials_dict['scopes']
    )
    
    cursor.close()
    conn.close()
    
    # Google Calendar APIの呼び出し
    service = build('calendar', 'v3', credentials=credentials)
    
    # カレンダーイベントの取得
    now = datetime.datetime.utcnow().isoformat() + 'Z'  # 'Z' は UTC
    events_result = service.events().list(
        calendarId='primary',
        timeMin=now,
        maxResults=10,
        singleEvents=True,
        orderBy='startTime'
    ).execute()
    events = events_result.get('items', [])
    
    if not events:
        return '<h1>今後の予定はありません</h1>'
    
    # イベント一覧の表示
    output = '<h1>今後の予定</h1><ul>'
    for event in events:
        start = event['start'].get('dateTime', event['start'].get('date'))
        output += f'<li>{start} - {event["summary"]}</li>'
    output += '</ul>'
    
    return output

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8000))
    app.run(debug=True, port=port, host="0.0.0.0")
