# AI Catch-up Scraping

Google Apps Script (GAS)と完全互換性を持つPython版URL処理システム。Google Sheetsからのスクレイピング、AI要約、自動化を実現。

## 🚀 クイックスタート

### Windows Users
```bash
START.bat をダブルクリック
```

### Command Line Users
```bash
python setup_and_run.py
```

### 軽量版（認証不要）
```bash
python lightweight_processor.py
```

## ✨ 主な機能

### 🎯 処理モード
- **完全自動モード**: Google Sheets連携 + AI要約
- **テスト・デモモード**: 認証不要のスクレイピング検証
- **デバッグモード**: 詳細ログ付き処理

### 🔧 技術特徴
- **arXiv特化**: 100%成功率のメタデータ抽出
- **LLM検証**: 偽陽性エラーを66%削減
- **多言語対応**: 日本語・英語・中国語エラー検出
- **GAS互換**: 列構造、ステータス値完全一致

### 📊 対応サイト
- arXiv (論文メタデータ)
- ResearchGate
- 一般Webサイト
- PDF文書（制限付き）

## 🏗️ プロジェクト構造

```
AI_catch_up_scraping/
├── START.bat                 # Windows用起動スクリプト
├── setup_and_run.py         # メインエントリーポイント
├── lightweight_processor.py # 認証不要版
├── config.json              # 設定ファイル
├── Credential_ver3.json     # Google認証情報
├── requirements.txt         # 依存パッケージ
├── src/                     # コアモジュール
│   ├── config.py           # 設定管理
│   ├── processor.py        # メイン処理エンジン
│   ├── scraper_base.py     # スクレイピング基盤
│   ├── sheets_integration.py # Google Sheets連携
│   └── llm_response_validator.py # LLM検証
├── utils/                   # ユーティリティ
│   ├── log_analyzer.py     # ログ分析
│   └── test_all_systems.py # システムテスト
└── test_env/               # テスト環境
    ├── data/               # テストデータ
    └── scripts/            # テストスクリプト
```

## 🔧 認証設定

### 自動認証セットアップ
```bash
python setup_and_run.py
# "y" を選択すると自動的に認証セットアップが開始
```

### 必要な認証情報
1. **Google Sheets ID**: `1Fc7LvgAdqQ9z5ayLej8eI3FFyCCeY7eO-nwVbNus7PU` (設定済み)
2. **Google認証**: `Credential_ver3.json` (設定済み)
3. **Gemini API**: 環境変数 `GEMINI_API_KEY` (オプション)

### 認証状態確認
現在の認証状態:
- ✅ Google Sheets ID: 設定済み
- ✅ 認証ファイル: Credential_ver3.json
- ⚠️ Gemini API: 未設定（オプション）

### テスト実行

```bash
# システムテスト
python utils/test_all_systems.py

# テスト環境でのエラー処理テスト
python test_env/scripts/test_error_processing.py
```

## 🎯 使用方法

### Windows Users
```bash
START.bat
```
自動的に設定チェックし、適切なモードで起動

### Command Line Users
```bash
# フルシステム（Google Sheets + AI要約）
python setup_and_run.py

# 軽量版（認証不要）
python lightweight_processor.py
```

### 処理モード
1. **完全自動**: Google Sheets連携 + AI要約
2. **テスト/デモ**: 認証不要スクレイピング
3. **デバッグ**: 詳細ログ付き処理

## 📈 実績

### パフォーマンス向上
- **arXiv成功率**: 0% → 100%
- **偽陽性削減**: 66%削減
- **処理精度**: LLM検証システム導入

### GAS互換性
- ✅ 列構造完全一致 (A-K列)
- ✅ ステータス値一致
- ✅ バッチ処理制限 (15件)
- ✅ 実行時間制限 (4分)

## ⚙️ 設定

### 現在の設定状況
```json
{
  "google_sheets": {
    "sheet_id": "1Fc7LvgAdqQ9z5ayLej8eI3FFyCCeY7eO-nwVbNus7PU",
    "credentials_path": "Credential_ver3.json"
  },
  "api_keys": {
    "gemini_api_key": ""
  }
}
```

### オプション設定
- **Gemini API**: 環境変数 `GEMINI_API_KEY` でAI要約を有効化
- **デバッグ**: ログレベル調整可能

## 📚 参考情報

### 対応フォーマット
- **arXiv**: 論文メタデータ自動抽出
- **ResearchGate**: 研究論文
- **一般Web**: HTML/テキスト抽出
- **PDF**: 制限付き対応

### 技術仕様
- **Python 3.x**: 互換性
- **Google APIs**: Sheets連携
- **Gemini API**: AI要約
- **LLM検証**: 品質保証

---

**リポジトリ**: https://github.com/MrDog1/AI_catch_up_scraping  
**更新日**: 2025-06-20  
**バージョン**: v2.0 (整理済み)