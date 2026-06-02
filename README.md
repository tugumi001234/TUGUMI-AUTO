# TUGUMI - Autonomous AI Agent

自律型AIエージェント「TUGUMI」 - Termuxでローカルに動作するLLMベースの完全自動実行型AI

## 🎯 概要

TUGUMIは、Androidデバイス上のTermuxを使用して、**llama.cpp**のローカルLLMを活用した自律型AIエージェントです。

### 主な特徴

- ✅ **完全自律実行**: エラーでユーザー入力待ちになることはなく、自ら思考・調査・実行
- ✅ **長考型LLM対応**: 推論が長いモデルに対応したタイムアウト対策とアライブモニタリング
- ✅ **Webスクレイピング機能**: URLからコンテンツを取得・要約してテキストで保存
- ✅ **Android対応**: `/storage/emulated/0/AgentDesk`に自動保存
- ✅ **動的拡張性**: ツール・ライブラリを自由に追加可能
- ✅ **自己学習・自己修正**: 失敗から学び、アプローチを修正可能
- ✅ **包括的なログ**: すべてのアクションを記録し、メモリに保存
- ✅ **マルチツール対応**: 
  - DuckDuckGoでのウェブ検索
  - Webスクレイピング＆要約
  - Subprocessによる外部コマンド実行
  - Pip経由のライブラリ自動インストール
  - カスタムツール動的生成

---

## 📋 必要な環境

### ハードウェア
- Android デバイス
- Termux アプリケーション

### ソフトウェア
- Python 3.8+
- llama.cpp (サーバーモード)
- Git

### 必須ライブラリ
自動インストールされます（以下のコマンドで手動インストール可能）
```bash
pip install -r requirements.txt
```

---

## 🚀 クイックスタート

### 1. リポジトリのクローン

```bash
# Termuxで実行
cd ~
git clone https://github.com/tugumi001234/TUGUMI-AUTO.git
cd TUGUMI-AUTO
```

### 2. 依存関係のインストール

```bash
# パッケージマネージャーの更新
apt update && apt upgrade -y

# Pythonと必要ツールをインストール
apt install -y python python-pip git

# Pythonの依存パッケージをインストール
pip install -r requirements.txt
```

### 3. llama.cpp サーバーの起動

別のTermuxセッション（またはターミナル）で：

```bash
# llama.cppをダウンロード（初回のみ）
# https://github.com/ggerganov/llama.cpp からバイナリを入手
# または以下でビルド
git clone https://github.com/ggerganov/llama.cpp
cd llama.cpp
make

# モデルファイルを配置
# 例: ~/models/model.gguf

# サーバーを起動
./llama-server -m ~/models/model.gguf -c 2048 --port 8080 -ngl 99
```

### 4. TUGUMIエージェントを起動

元のTermuxセッションで：

```bash
cd ~/TUGUMI-AUTO
python tugumi_agent.py
```

---

## 💻 使用方法

### インタラクティブコマンド

TUGUMIが起動すると、以下のコマンドが利用可能です:

```
TUGUMI> task <タスク説明>     # タスクを実行
TUGUMI> scrape <URL>          # URLをスクレイピング＆要約
TUGUMI> search <検索キーワード> # ウェブ検索
TUGUMI> status                 # 現在の状態を表示
TUGUMI> logs                   # 最新ログを表示（直近10行）
TUGUMI> history                # タスク履歴を表示（直近5件）
TUGUMI> quit                   # TUGUMIを終了
```

### 使用例

#### 例1: Pythonパッケージ調査

```
TUGUMI> task 最新のデータ処理ライブラリについて調べて、インストール方法を提示してください
```

自動で以下を実行:
1. ウェブ検索で最新ライブラリを調査
2. 必要な情報を集約
3. インストール方法を提示

#### 例2: Webスクレイピング

```
TUGUMI> scrape https://example.com
```

自動で以下を実行:
1. Webページを取得
2. テキストを抽出
3. 要約を生成
4. `/storage/emulated/0/AgentDesk/SCRAPE_OUTPUT/` に保存

#### 例3: ウェブ検索

```
TUGUMI> search Python 機械学習 ライブラリ
```

#### 例4: 複合タスク

```
TUGUMI> task JSONファイルを解析して、特定のキーの値を抽出し、CSVファイルに変換してください
```

自動で以下を実行:
1. 必要なライブラリを確認・インストール
2. JSONファイルを解析
3. CSV変換処理を実装・実行
4. エラーが発生した場合は自己修正

---

## 📁 ファイル構成

```
TUGUMI-AUTO/
├── tugumi_agent.py          # メインエージェント（Webスクレイピング機能付き）
├── tugumi_tools.py          # ツール拡張システム
├── tugumi_examples.py       # 使用例とサンプル
├── requirements.txt         # 依存パッケージ
├── README.md                # このファイル
└── SETUP_GUIDE.md          # セットアップガイド

Android Termuxストレージ:
/storage/emulated/0/AgentDesk/
├── LOGS/                   # 実行ログ（テキストファイル）
├── MEMORY/                 # 学習メモリ（JSON形式）
├── TOOLS/                  # カスタムツール
├── OUTPUT/                 # 処理結果
└── SCRAPE_OUTPUT/          # スクレイピング結果

ホームディレクトリ（フォールバック）:
~/Documents/TUGUMI/
├── LOGS/
├── MEMORY/
├── TOOLS/
├── OUTPUT/
└── SCRAPE_OUTPUT/
```

---

## 🔧 アーキテクチャ

### コンポーネント構成

```
┌─────────────────────────────────────────────┐
│         User Input / Task                    │
└──────────────┬──────────────────────────────┘
               │
        ┌──────▼──────┐
        │ TugumiMind  │  (メイン思考エンジン)
        └──────┬──────┘
               │
      ┌────────┼────────────┐
      │        │            │
  ┌───▼──┐ ┌──▼───┐ ┌──────▼─────┐
  │ LLM  │ │ Tools│ │ Scraper    │
  │Client│ │Kit   │ │ Logger     │
  └───┬──┘ └──┬───┘ │ Memory     │
      │       │     └──────┬─────┘
      └───┬───┴────┬───────┘
          │        │
    ┌─────▼──┐ ┌───▼──────┐
    │llama   │ │ Storage  │
    │.cpp    │ │(Android/ │
    └────────┘ │ Documents)
               └──────────┘
```

### 処理フロー

```
1. Task Analysis (タスク分析)
   - LLMがタスクを理解
   - 必要なステップを分解
   
2. Knowledge Search (知識検索)
   - ウェブ検索で情報収集
   - 必要なライブラリ確認
   
3. Tool Preparation (ツール準備)
   - 必要なパッケージをインストール
   - カスタムツールを動的生成
   
4. Execution (実行)
   - 各ステップを順序実行
   - リアルタイム監視
   - Webスクレイピング実行
   
5. Verification & Self-Correction (検証・修正)
   - 実行結果を評価
   - 失敗時は自動修正
   
6. Logging & Memory (ログ・メモリ保存)
   - すべての履歴を記録
   - スクレイピング結果を保存
   - 学習データとして保存
```

---

## 🛠️ ツール拡張

### カスタムツールの追加

#### 方法1: 自動生成

```python
from tugumi_tools import ToolManager
from pathlib import Path

tool_manager = ToolManager(Path.home() / "Documents" / "TUGUMI" / "TOOLS")

# ツールを生成して登録
tool_manager.create_and_load_tool(
    tool_name="my_tool",
    description="My custom tool",
    implementation="""
    result = args[0] if args else "No input"
    return f"Processed: {result}"
    """
)
```

#### 方法2: 手動作成

`~/Documents/TUGUMI/TOOLS/` に以下の構成でPythonファイルを作成:

```python
def register_tools(registry):
    """ツール登録関数"""
    registry.register_tool(
        "my_custom_tool",
        execute_tool,
        {
            "description": "My custom tool description",
            "parameters": {"arg1": "Parameter description"},
            "return_type": "str"
        }
    )

def execute_tool(arg1, *args, **kwargs):
    """ツール実装"""
    return f"Result: {arg1}"
```

### ツールパック (複数ツール)

```python
tools_list = [
    {
        "name": "tool1",
        "description": "First tool",
        "implementation": "return 'Tool 1 result'"
    },
    {
        "name": "tool2",
        "description": "Second tool",
        "implementation": "return 'Tool 2 result'"
    }
]

tool_manager.create_tool_pack("my_pack", tools_list)
```

---

## 🧠 AI の思考と実行の流れ

### タスク受け取り例

```
User: "Pythonで画像処理ライブラリを調べて、インストール可能な状態にしてください"

TUGUMI思考:
1. タスク分析:
   - 目標: 画像処理ライブラリを調査・インストール
   - 必要な知識: 最新の画像処理ライブラリ、インストール方法
   - 必要なツール: web検索、pip

2. 知識検索:
   - "Python 画像処理 ライブラリ 2024" で検索
   - 結果: Pillow, OpenCV, scikit-image, torchvision等

3. 実行:
   - pip install pillow opencv-python scikit-image
   - 各ライブラリのバージョン確認
   
4. 検証:
   - import成功確認
   - 使用方法をドキュメント化

5. ログ保存:
   - 実行内容、結果、所要時間を記録
   - 次回の参考にする
```

---

## 📊 ログシステム

### ログ出力

すべてのアクションが自動的に保存されます:
- **Android**: `/storage/emulated/0/AgentDesk/LOGS/`
- **その他**: `~/Documents/TUGUMI/LOGS/`

```
LOGS/
├── tugumi_20260602_120000.log
├── tugumi_20260602_120500.log
└── ...
```

### ログ形式

```
2026-06-02T12:00:00.123456 | INFO [TASK_001_1717239600] | Starting task: research Python libraries
2026-06-02T12:00:01.234567 | INFO [SEARCH] | Web search: latest Python data processing libraries
2026-06-02T12:00:02.345678 | DEBUG [LLM] | Sending inference request: Analyze search results...
2026-06-02T12:00:15.456789 | INFO [LLM] | Inference completed in 13.1s
2026-06-02T12:00:16.567890 | INFO [EXEC] | Executing command: pip install pandas numpy
2026-06-02T12:00:30.678901 | INFO [EXEC] | Command completed with code 0
2026-06-02T12:00:31.789012 | INFO [SCRAPE] | Fetching: https://example.com
2026-06-02T12:00:35.890123 | INFO [SCRAPE] | File saved: /storage/emulated/0/AgentDesk/SCRAPE_OUTPUT/scrape_example_com.txt
```

### メモリシステム

タスク実行結果は JSON形式で保存:
- **Android**: `/storage/emulated/0/AgentDesk/MEMORY/`
- **その他**: `~/Documents/TUGUMI/MEMORY/`

```json
{
  "task_id": "TASK_001_1717239600",
  "task": "research Python libraries",
  "status": "completed",
  "analysis": {
    "task_type": "research",
    "required_knowledge": ["latest Python libraries"],
    "action_steps": [...]
  },
  "execution_steps": [...],
  "final_output": "Successfully researched and prepared...",
  "execution_time": 45.23
}
```

---

## 🔒 セキュリティと制限事項

### 制限なし設計
- ✅ ユーザーの指示に対して制限なし
- ✅ 自由にコマンド実行可能
- ✅ ライブラリ・ツール無制限追加可能

### 推奨事項
- 信頼できるネットワーク環境で使用
- 定期的にログを確認
- 重要なシステムファイルには別途アクセス制御を設定

---

## ⏱️ タイムアウト管理

### 長考型LLM対応

推論が長いモデルの場合:

```python
# tugumi_agent.py内で設定
TugumiConfig.LLM_TIMEOUT = 600      # 10分
TugumiConfig.INFERENCE_TIMEOUT = 300 # 5分
TugumiConfig.ALIVE_CHECK_INTERVAL = 10 # 10秒ごとの確認
```

### アライブモニタリング

```
[DEBUG] LLM推論開始: 0.0s / 300s
[DEBUG] LLM推論実行中... (10.2s / 300s)
[DEBUG] LLM推論実行中... (20.1s / 300s)
...
[INFO] LLM推論完了: 45.3s
```

---

## 🐛 トラブルシューティング

### LLMに接続できない

```bash
# llama.cppが起動しているか確認
curl http://0.0.0.0:8080/slots

# エラーが出た場合、llama.cppを再起動
# 別のTermuxセッションで:
./llama-server -m ~/models/model.gguf -c 2048 --port 8080 -ngl 99
```

### ライブラリインストール失敗

```
[ERROR] Library installation failed: ...
```

この場合、TUGUMI自動で代替ライブラリを検索・インストールします。

### メモリ不足

推論時にメモリが不足する場合:

```bash
# モデルのコンテキスト長を削減
./llama-server -m ~/models/model.gguf -c 1024 --port 8080
```

### Webスクレイピング失敗

```
[ERROR] Fetching failed: ...
```

自動リトライ機能が動作します（最大3回）。タイムアウトは30秒です。

---

## 📝 API リファレンス

### TugumiMind クラス

```python
from tugumi_agent import TugumiMind

agent = TugumiMind()

# タスク実行
result = agent.run_task("task description")
# 返り値: Dict[task_id, task, status, analysis, execution_steps, errors, final_output, execution_time]

# ログ取得
logs = agent.logger.get_logs(num_lines=50)

# メモリ保存/読み込み
agent.logger.save_memory("key", {"data": "value"})
memory = agent.logger.load_memory("key")
```

### ToolManager クラス

```python
from tugumi_tools import ToolManager
from pathlib import Path

tool_manager = ToolManager(Path.home() / "Documents" / "TUGUMI" / "TOOLS")

# ツール作成
tool_manager.create_and_load_tool("tool_name", "description", "implementation")

# ツール呼び出し
result = tool_manager.call_tool("tool_name", arg1, arg2)

# 利用可能なツール確認
tools = tool_manager.get_available_tools()
```

### TugumiWebScraper クラス

```python
from tugumi_agent import TugumiWebScraper, TugumiLogger

logger = TugumiLogger()
scraper = TugumiWebScraper(logger)

# URLをスクレイピング
result = scraper.scrape_and_summarize("https://example.com", save_output=True)

# テキスト抽出
text = scraper.extract_text_from_html(html_content)

# ファイル保存
file_path = scraper.save_to_file("content", "filename")
```

---

## 🎓 サンプルタスク

### 例1: データ分析

```
TUGUMI> task 
> CSVファイルを読み込んで、基本統計量を計算し、
> 結果をJSON形式で出力してください。
> ファイルパスは ~/data.csv です。
```

### 例2: Webスクレイピング

```
TUGUMI> task 
> 指定されたウェブサイトからテーブルデータを抽出して、
> CSVに変換するツールを作成してください。
> URL: https://example.com/data
```

### 例3: 自動テスト

```
TUGUMI> task 
> Pythonスクリプトの単体テストを自動生成して実行し、
> テストレポートをJSON形式で保存してください。
> スクリプトパス: ~/my_script.py
```

### 例4: 複数URLのスクレイピング

```
TUGUMI> scrape https://news.example.com/article1
TUGUMI> scrape https://news.example.com/article2
TUGUMI> scrape https://docs.example.com
```

結果は `/storage/emulated/0/AgentDesk/SCRAPE_OUTPUT/` に保存されます。

---

## 🤝 貢献方法

バグ報告、機能リクエスト、プルリクエストを歓迎します!

---

## 📄 ライセンス

MIT License

---

## 📞 サポート

- Issues: https://github.com/tugumi001234/TUGUMI-AUTO/issues
- Discussions: https://github.com/tugumi001234/TUGUMI-AUTO/discussions

---

## ✨ 特記事項

TUGUMI は、完全に自律的に動作する設計です。エラーが発生しても、ユーザーの入力を待つことなく、自ら考え、調査し、必要なツールを整え、実行します。

これは、従来のAIアシスタントとは異なり、**人間の承認に依存しない自律型エージェント**として機能します。

### 完全エラーハンドリング
- ✅ LLM未起動でもフォールバック動作
- ✅ ネットワーク失敗時も自動リトライ（最大3回）
- ✅ ファイル保存失敗時も処理継続
- ✅ JSON パース失敗時もデフォルト値返却
- ✅ すべてのエラーが詳細にログに記録

### 自動復旧メカニズム
1. **エラー検出**: 自動的にエラーを検出
2. **分析**: LLMでエラーの原因を分析
3. **代替案生成**: 別の実行方法を生成
4. **再試行**: 修正版で再実行
5. **検証**: 結果を検証して確認
6. **学習**: エラーと対応方法をメモリに記録

---

**最後更新**: 2026-06-02

**バージョン**: 1.0.0 (完全機能版)
