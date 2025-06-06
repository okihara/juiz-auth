# Google Calendar OAuth認証サーバー

このプロジェクトは、Google CalendarのOAuth認証を行い、取得したクレデンシャルをPostgreSQLデータベースに保存するWebサーバーです。

## 機能

- Google Calendar APIのOAuth認証フロー
- 認証情報のPostgreSQLへの保存
- 保存した認証情報を使用してGoogle Calendarのイベント取得

## 必要条件

- Python 3.8以上
- PostgreSQLデータベース
- Google Cloud Platformのプロジェクト（OAuth認証情報）

## セットアップ

1. リポジトリをクローン
```
git clone <リポジトリURL>
cd line-juiz
```

2. 仮想環境を作成して有効化
```
python -m venv venv
source venv/bin/activate  # Linuxまたは macOS の場合
venv\Scripts\activate     # Windowsの場合
```

   **仮想環境（venv）についての補足情報：**
   - 仮想環境は、プロジェクト固有の依存関係を他のプロジェクトから分離するために使用します
   - 新しいターミナルセッションを開始するたびに、仮想環境を再度有効化する必要があります
   - 仮想環境を終了するには、`deactivate` コマンドを使用します
   - 新しいパッケージをインストールした後は、`pip freeze > requirements.txt` を実行して依存関係を更新することをお勧めします

3. 依存パッケージのインストール
```
pip install -r requirements.txt
```

4. 環境変数の設定
`.env`ファイルを編集して、以下の変数を設定します：
- `GOOGLE_CLIENT_ID`: Google Cloud PlatformのクライアントID
- `GOOGLE_CLIENT_SECRET`: Google Cloud Platformのクライアントシークレット
- `GOOGLE_REDIRECT_URI`: リダイレクトURI（デフォルト: http://localhost:5000/oauth2callback）
- `DATABASE_URL`: PostgreSQLの接続URL
- `SECRET_KEY`: Flaskセッション用の秘密鍵

5. データベースの準備
PostgreSQLにデータベースを作成し、スキーマを適用します：
```
psql -U <ユーザー名> -d <データベース名> -f schema.sql
```

## 使い方

1. サーバーを起動
```
python app.py
```

2. ブラウザで http://localhost:5000 にアクセス

3. 「Google Calendarと連携する」リンクをクリックして認証フローを開始

4. 認証が完了すると、カレンダー情報を表示できます

## 注意事項

- 本番環境では、適切なセキュリティ対策を施してください
- `.env`ファイルは`.gitignore`に追加して、機密情報が公開されないようにしてください
