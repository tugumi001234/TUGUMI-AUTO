# TUGUMI セットアップガイド

Android Termux環境での完全セットアップ手順

## 📱 前提条件

- Android デバイス
- Termux アプリケーション（F-DroidまたはGoogle Playから入手）
- インターネット接続
- 最低 2GB の空き容量

---

## 🚀 ステップ1: Termux環境のセットアップ

### 1.1 Termuxを起動して初期化

```bash
# パッケージリストを更新
apt update

# パッケージをアップグレード
apt upgrade -y

# ストレージアクセス許可を設定
termux-setup-storage
```

**重要**: `termux-setup-storage` を実行して、`Storage` フォルダへのアクセス許可が必要です。

### 1.2 必須パッケージをインストール

```bash
# 基本開発ツール
apt install -y python python-pip git curl

# ビルドツール（一部のPythonパッケージ用）
apt install -y build-essential clang

# オプション: nano エディタ
apt install -y nano
```

---

## 🐍 ステップ2: Pythonの確認

```bash
# Pythonバージョン確認（3.8以上必須）
python --version
python3 --version

# pipバージョン確認
pip --version
```

**トラブル**: `python` コマンドがない場合
```bash
apt install -y python
```

---

## 📥 ステップ3: TUGUMIのクローンと依存関係のインストール

### 3.1 リポジトリをクローン

```bash
# ホームディレクトリに移動
cd ~

# リポジトリをクローン
git clone https://github.com/tugumi001234/TUGUMI-AUTO.git

# ディレクトリに移動
cd TUGUMI-AUTO
```

### 3.2 依存ライブラリをインストール

```bash
# 依存パッケージをインストール
pip install -r requirements.txt

# または個別にインストール
pip install requests
pip install duckduckgo-search
```

**トラブル**: インストール失敗時
```bash
# pipをアップグレード
pip install --upgrade pip

# キャッシュをクリアして再試行
pip install --no-cache-dir -r requirements.txt
```

---

## 🦙 ステップ4: llama.cpp サーバーの構築と起動

### 4.1 llama.cppのビルド（オプション）

別のTermuxセッションで以下を実行:

```bash
# llama.cppリポジトリをクローン
cd ~
git clone https://github.com/ggerganov/llama.cpp
cd llama.cpp

# ビルド（最初のビルドには数分かかります）
make

# GPU アクセラレーション対応版（Adreno GPU）
LLAMA_CUDA=1 make
```

### 4.2 モデルファイルの入手

llama.cpp で使用するモデルファイルが必要です:

**方法1: Hugging Face から直接ダウンロード**

```bash
# モデルディレクトリを作成
mkdir -p ~/models

# cd するはしなくてもいいが、スクリプトで用いる場合のため作成
cd ~/models

# GGUF形式のモデルをダウンロード（例: Mistral 7B）
# 注: モデルサイズは 4GB-13GB 程度
curl -L https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.1-GGUF/resolve/main/Mistral-7B-Instruct-v0.1.Q4_K_M.gguf -o mistral-7b.gguf

# または wget を使用
wget https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.1-GGUF/resolve/main/Mistral-7B-Instruct-v0.1.Q4_K_M.gguf -O mistral-7b.gguf
```

**方法2: Ollama を使用する場合**

```bash
# Ollama をインストール
# https://ollama.ai から Android 版をダウンロード

# モデルをプル
ollama pull mistral
```

### 4.3 llama.cpp サーバーを起動

**新しいTermuxセッションで実行**:

```bash
cd ~/llama.cpp

# 基本的な起動
./llama-server -m ~/models/mistral-7b.gguf -c 2048 --port 8080

# GPU アクセラレーション付き起動
./llama-server -m ~/models/mistral-7b.gguf -c 2048 --port 8080 -ngl 99

# コンテキスト長を小さくする場合（メモリ節約）
./llama-server -m ~/models/mistral-7b.gguf -c 1024 --port 8080

# スレッド数を指定
./llama-server -m ~/models/mistral-7b.gguf -c 2048 --port 8080 -t 4
```

**起動オプション説明**:
- `-m`: モデルファイルパス
- `-c`: コンテキスト長（バッチサイズ）
- `--port`: リスニングポート
- `-ngl`: GPU層の数（99=すべてGPUで実行）
- `-t`: スレッド数

**確認**: llama.cpp が起動しているか確認

別のTermuxセッションで:
```bash
curl http://localhost:8080/slots
```

成功時の応答:
```json
[{"id":0,"state":0,"...":...}]
```

---

## 🤖 ステップ5: TUGUMI の起動

**TUGUMI用の新しいTermuxセッション** を開いて:

```bash
cd ~/TUGUMI-AUTO

# TUGUMIを起動
python tugumi_agent.py
```

**期待される出力**:
```
============================================================
TUGUMI - Autonomous AI Agent
Local LLM (llama.cpp) powered
============================================================

LLM Status: ✓ Connected

Commands:
  'task <description>' - Execute a task
  'status' - Show current status
  'logs' - Show recent logs
  'history' - Show task history
  'quit' - Exit

TUGUMI>
```

---

## 📝 使用例

### 例1: 簡単なテスト

```
TUGUMI> task ホームディレクトリのファイル数を数えてください
```

### 例2: ウェブ検索

```
TUGUMI> task 最新のPythonデータ処理ライブラリについて調べてください
```

### 例3: ライブラリインストール

```
TUGUMI> task Pandasライブラリをインストールして、バージョンを確認してください
```

---

## 🛠️ Termuxセッション管理

### マルチセッション実行推奨構成

```
セッション1: llama.cpp サーバー
セッション2: TUGUMI エージェント
セッション3: ログ/モニタリング
```

**セッション切り替え**: Termuxで `Ctrl + Space` または `Ctrl + 0` (Settings)

---

## 📊 ログとメモリの位置確認

```bash
# ログディレクトリ
ls -la ~/Documents/TUGUMI_LOGS/

# メモリディレクトリ
ls -la ~/Documents/TUGUMI_MEMORY/

# ツールディレクトリ
ls -la ~/Documents/TUGUMI_TOOLS/
```

---

## 🐛 トラブルシューティング

### 問題1: "ModuleNotFoundError: No module named 'requests'"

```bash
pip install requests
# または
pip install -r requirements.txt
```

### 問題2: LLMに接続できない

1. llama.cpp が起動しているか確認:
```bash
curl http://localhost:8080/slots
```

2. ポート 8080 が使用可能か確認:
```bash
netstat -an | grep 8080
```

3. llama.cpp を再起動:
```bash
# 前のプロセスを終了 (Ctrl + C)
# 再度起動
./llama-server -m ~/models/mistral-7b.gguf -c 2048 --port 8080
```

### 問題3: メモリ不足エラー

```bash
# モデルのコンテキスト長を削減
./llama-server -m ~/models/mistral-7b.gguf -c 512 --port 8080

# または、より小さいモデルを使用
./llama-server -m ~/models/smaller-model.gguf -c 2048 --port 8080
```

### 問題4: Pythonスクリプト実行時にエラー

```bash
# Pythonのディレクトリ権限を確認
ls -la ~/TUGUMI-AUTO/

# スクリプトに実行権限を付与
chmod +x ~/TUGUMI-AUTO/tugumi_agent.py

# 実行
python ~/TUGUMI-AUTO/tugumi_agent.py
```

### 問題5: ストレージアクセス拒否

```bash
# ストレージアクセス許可を再設定
termux-setup-storage

# 許可を求めるダイアログが表示されるので、許可を選択
```

---

## 🔧 詳細設定

### 推論パラメータの調整

`tugumi_agent.py` の `TugumiConfig` クラスを編集:

```python
class TugumiConfig:
    # LLM設定
    LLM_TIMEOUT = 600          # 推論のタイムアウト（秒）
    INFERENCE_TIMEOUT = 300    # 単一推論のタイムアウト
    ALIVE_CHECK_INTERVAL = 10  # アライブチェック間隔（秒）
    
    # 推論パラメータ
    MAX_TOKENS = 2048          # 最大トークン数
    TEMPERATURE = 0.7          # 創造性（0-1）
    TOP_P = 0.9                # サンプリング多様性（0-1）
```

### ログレベルの変更

`tugumi_agent.py` 内の `logger.log()` 呼び出しで:

```python
logger.log("message", level="DEBUG")    # デバッグログ
logger.log("message", level="INFO")     # 情報ログ
logger.log("message", level="WARN")     # 警告ログ
logger.log("message", level="ERROR")    # エラーログ
```

---

## ✅ セットアップ完了チェックリスト

- [ ] Termux がインストール済み
- [ ] Python 3.8+ がインストール済み
- [ ] TUGUMI-AUTO がクローン済み
- [ ] 依存ライブラリがインストール済み
- [ ] llama.cpp がビルド済み（またはバイナリ入手）
- [ ] モデルファイル（.gguf）が ~/models に配置済み
- [ ] llama.cpp サーバーが起動可能
- [ ] TUGUMI が起動可能
- [ ] ログ/メモリディレクトリが作成可能

---

## 📚 次のステップ

1. **簡単なタスクから始める**
   - ファイル操作タスク
   - ウェブ検索タスク

2. **カスタムツールを作成**
   - `tugumi_examples.py` を参照
   - 独自のツールを動的に生成

3. **高度なタスクに挑戦**
   - データ分析
   - 自動スクリプト生成
   - ログ分析

4. **ドキュメント確認**
   - README.md
   - tugumi_examples.py

---

## 📞 ヘルプが必要な場合

- Issues: https://github.com/tugumi001234/TUGUMI-AUTO/issues
- Discussions: https://github.com/tugumi001234/TUGUMI-AUTO/discussions

---

**最後更新**: 2024-06-01

**バージョン**: TUGUMI 1.0
