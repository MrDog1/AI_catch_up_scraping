# 🔑 認証設定完全ガイド

## 🚀 自動認証セットアップ（推奨）

**最も簡単な方法：**
```bash
START.bat → モード5（Setup Authentication）を選択
```

このツールが以下を自動で行います：
- Gemini API キーの設定
- Google Sheets API認証の設定
- 設定ファイルの自動生成
- 接続テストの実行

## 📋 手動設定ガイド

### Step 1: Gemini API キー取得

1. **Google AI Studio** にアクセス：https://aistudio.google.com/
2. Googleアカウントでログイン
3. 「Get API key」をクリック
4. 新しいAPIキーを作成
5. APIキーをコピー

### Step 2: Google Sheets API 設定

1. **Google Cloud Console** にアクセス：https://console.cloud.google.com/
2. 新しいプロジェクトを作成（または既存を選択）
3. **Google Sheets APIを有効化**：
   - 「APIs & Services」→「Library」
   - 「Google Sheets API」を検索
   - 「Enable」をクリック

4. **サービスアカウント作成**：
   - 「APIs & Services」→「Credentials」
   - 「Create Credentials」→「Service Account」
   - サービスアカウント詳細を入力
   - 「Create and Continue」

5. **認証キーの生成**：
   - 作成されたサービスアカウントをクリック
   - 「Keys」タブ
   - 「Add Key」→「Create new key」
   - 「JSON」形式を選択
   - ダウンロード

6. **ファイルの配置**：
   - ダウンロードしたJSONファイルを`Credential_ver2.json`にリネーム
   - プロジェクトルートに配置

### Step 3: Google Sheetの共有設定

1. **Google Sheets** でスプレッドシートを開く
2. **共有**ボタンをクリック
3. **サービスアカウントのメールアドレス**を追加
   - JSONファイル内の `client_email` の値
   - 編集権限を付与
4. 共有

### Step 4: 設定ファイル作成

`config.json` ファイルを作成：

```json
{
  "google_sheets": {
    "sheet_id": "YOUR_GOOGLE_SHEET_ID",
    "credentials_path": "Credential_ver2.json"
  },
  "api_keys": {
    "gemini_api_key": "YOUR_GEMINI_API_KEY"
  },
  "processing": {
    "max_urls_per_batch": 5,
    "request_delay": 2,
    "timeout_seconds": 30,
    "max_execution_time_minutes": 4,
    "rows_per_exec": 15
  }
}
```

**Sheet IDの取得方法：**
Google SheetsのURLから抽出：
```
https://docs.google.com/spreadsheets/d/[SHEET_ID]/edit
```

## 🔒 セキュリティ設定（推奨）

### 環境変数の使用

認証情報をファイルに保存せず、環境変数で管理：

```bash
# Windows
set GOOGLE_SHEET_ID=your_sheet_id
set GEMINI_API_KEY=your_api_key

# Linux/Mac
export GOOGLE_SHEET_ID=your_sheet_id
export GEMINI_API_KEY=your_api_key
```

### .gitignoreの確認

機密情報がGitにコミットされないよう確認：

```
config.json
Credential*.json
*.log
```

## 🧪 接続テスト

設定完了後、接続をテスト：

```bash
# 設定状態確認
python src/config.py status

# 接続テスト
python verify_auth.py

# 簡単なテスト実行
python minimal_test.py
```

## ❓ トラブルシューティング

### よくある問題

**1. "Google Sheets service not available"**
- `Credential_ver2.json` が正しく配置されているか確認
- Google Sheetがサービスアカウントと共有されているか確認
- サービスアカウントに編集権限があるか確認

**2. "Gemini API key not configured"**
- APIキーが正しく設定されているか確認
- APIキーに有効期限がないか確認
- Gemini APIの利用制限に達していないか確認

**3. "No URLs found in Error sheet"**
- ErrorシートがGoogle Sheetに存在するか確認
- B列（FINAL_URL）にURLが入力されているか確認
- D列（STATUS）が空白またはERRORになっているか確認

**4. "Permission denied" エラー**
- Google Cloud Consoleでプロジェクトが有効か確認
- Google Sheets APIが有効化されているか確認
- サービスアカウントの権限設定を確認

### デバッグ用コマンド

```bash
# 詳細ログ付きでテスト
python standalone_processor.py

# 設定検証
python src/config.py validate

# 認証テスト
python working_auth_test.py
```

## 📞 サポート

問題が解決しない場合：

1. `logs/` ディレクトリのログファイルを確認
2. `python src/config.py status` の出力を確認
3. エラーメッセージの詳細を記録

認証が正常に設定されれば、フル機能でシステムを利用できます！