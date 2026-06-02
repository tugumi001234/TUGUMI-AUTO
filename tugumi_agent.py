#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TUGUMI - Autonomous AI Agent
ローカルLLM (llama.cpp) を使用した自律型AIエージェント

Features:
- 長考型LLMに対応したタイムアウト対策とアライブモニタリング
- DuckDuckGoによるネット検索機能
- Webスクレイピング機能（記事取得・要約・テキスト保存）
- ログメモリ管理システム
- 自己学習・自己修正能力
- 動的ツール・ライブラリ拡張
- Subprocessを使用したタスク実行
- Android Termux対応（/storage/emulated/0/AgentDeskに保存）
"""

import os
import sys
import json
import time
import subprocess
import threading
import traceback
import re
from datetime import datetime
from typing import Optional, Dict, List, Any, Tuple
from pathlib import Path
from urllib.parse import urljoin, urlparse

# Core dependencies
try:
    import requests
except ImportError:
    subprocess.run([sys.executable, "-m", "pip", "install", "requests"], check=True)
    import requests

try:
    from duckduckgo_search import DDGS
except ImportError:
    subprocess.run([sys.executable, "-m", "pip", "install", "duckduckgo_search"], check=True)
    from duckduckgo_search import DDGS

try:
    import feedparser
except ImportError:
    subprocess.run([sys.executable, "-m", "pip", "install", "feedparser"], check=True)
    import feedparser


class TugumiConfig:
    """TUGUMI設定クラス"""
    
    LLM_HOST = "0.0.0.0"
    LLM_PORT = 8080
    LLM_URL = f"http://{LLM_HOST}:{LLM_PORT}/completion"
    
    # ストレージパス（Android Termux対応）
    ANDROID_STORAGE = Path("/storage/emulated/0/AgentDesk")
    DOCUMENTS_DIR = Path.home() / "Documents" / "TUGUMI"
    
    # 優先的にAndroidストレージを使用、なければDocuments
    if ANDROID_STORAGE.exists():
        BASE_DIR = ANDROID_STORAGE
    else:
        BASE_DIR = DOCUMENTS_DIR
    
    LOG_DIR = BASE_DIR / "LOGS"
    MEMORY_DIR = BASE_DIR / "MEMORY"
    TOOLS_DIR = BASE_DIR / "TOOLS"
    OUTPUT_DIR = BASE_DIR / "OUTPUT"
    SCRAPE_DIR = BASE_DIR / "SCRAPE_OUTPUT"
    
    # タイムアウト設定
    LLM_TIMEOUT = 600  # 10分
    INFERENCE_TIMEOUT = 300  # 5分
    ALIVE_CHECK_INTERVAL = 10  # 10秒ごとにアライブ確認
    
    # LLM推論パラメータ
    MAX_TOKENS = 2048
    TEMPERATURE = 0.2
    TOP_P = 0.9
    
    # ウェブスクレイピング設定
    WEB_TIMEOUT = 300
    MAX_RETRIES = 3
    DEFAULT_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"


class TugumiLogger:
    """ログ管理システム"""
    
    def __init__(self, log_dir: Path = None):
        if log_dir is None:
            log_dir = TugumiConfig.LOG_DIR
        
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        self.current_log_file = None
        self.log_buffer = []
        self._create_new_log()
    
    def _create_new_log(self):
        """新規ログファイルを作成"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.current_log_file = self.log_dir / f"tugumi_{timestamp}.log"
        self.log(f"=== TUGUMI Agent Started: {datetime.now().isoformat()} ===")
    
    def log(self, message: str, level: str = "INFO", task_context: Optional[str] = None):
        """ログを記録"""
        try:
            timestamp = datetime.now().isoformat()
            context_str = f" [{task_context}]" if task_context else ""
            log_entry = f"{timestamp} | {level}{context_str} | {message}"
            
            self.log_buffer.append(log_entry)
            print(log_entry)
            
            # ファイルに書き込み
            if self.current_log_file:
                try:
                    with open(self.current_log_file, 'a', encoding='utf-8') as f:
                        f.write(log_entry + "\n")
                except Exception as e:
                    print(f"Warning: Could not write to log file: {e}")
        except Exception as e:
            print(f"Logging error: {e}")
    
    def get_logs(self, num_lines: int = 50) -> List[str]:
        """最新のログを取得"""
        return self.log_buffer[-num_lines:]
    
    def save_memory(self, memory_key: str, memory_data: Dict[str, Any]):
        """メモリをJSON形式で保存"""
        try:
            memory_dir = TugumiConfig.MEMORY_DIR
            memory_dir.mkdir(parents=True, exist_ok=True)
            memory_file = memory_dir / f"{memory_key}.json"
            
            with open(memory_file, 'w', encoding='utf-8') as f:
                json.dump(memory_data, f, ensure_ascii=False, indent=2)
            
            self.log(f"Memory saved: {memory_key}", task_context="MEMORY")
        except Exception as e:
            self.log(f"Failed to save memory: {e}", level="ERROR", task_context="MEMORY")
    
    def load_memory(self, memory_key: str) -> Optional[Dict[str, Any]]:
        """メモリをJSON形式で読み込み"""
        try:
            memory_file = TugumiConfig.MEMORY_DIR / f"{memory_key}.json"
            
            if memory_file.exists():
                with open(memory_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            self.log(f"Failed to load memory: {e}", level="ERROR", task_context="MEMORY")
        
        return None


class TugumiLLMClient:
    """llama.cpp クライアント"""
    
    def __init__(self, logger: TugumiLogger):
        self.logger = logger
        self.url = TugumiConfig.LLM_URL
        self.timeout = TugumiConfig.LLM_TIMEOUT
        self.response = None
        self.is_running = False
        self.inference_thread = None
    
    def check_llm_alive(self) -> bool:
        """LLMが起動しているか確認"""
        try:
            response = requests.get(
                f"http://{TugumiConfig.LLM_HOST}:{TugumiConfig.LLM_PORT}/slots",
                timeout=5
            )
            self.logger.log(f"LLM Health: {response.status_code}", level="DEBUG")
            return response.status_code == 200
        except Exception as e:
            self.logger.log(f"LLM Connection Failed: {str(e)}", level="WARN")
            return False
    
    def monitor_inference(self, start_time: float, timeout: float):
        """推論の進行状況をモニタリング（別スレッド）"""
        check_interval = TugumiConfig.ALIVE_CHECK_INTERVAL
        last_check = time.time()
        
        while self.is_running:
            elapsed = time.time() - start_time
            
            # タイムアウトチェック
            if elapsed > timeout:
                self.logger.log(
                    f"Inference timeout after {elapsed:.1f}s",
                    level="WARN"
                )
                self.is_running = False
                break
            
            # アライブチェック
            current_time = time.time()
            if current_time - last_check >= check_interval:
                self.logger.log(
                    f"Inference running... ({elapsed:.1f}s / {timeout}s)",
                    level="DEBUG"
                )
                last_check = current_time
            
            time.sleep(1)
    
    def infer(self, prompt: str, system_prompt: Optional[str] = None) -> Optional[str]:
        """LLMで推論を実行"""
        try:
            if not self.check_llm_alive():
                self.logger.log("LLM is not responding. Starting fallback mode.", level="ERROR")
                return self._fallback_response(prompt)
            
            full_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
            
            payload = {
                "prompt": full_prompt,
                "n_predict": TugumiConfig.MAX_TOKENS,
                "temperature": TugumiConfig.TEMPERATURE,
                "top_p": TugumiConfig.TOP_P,
            }
            
            self.logger.log(f"Sending inference request: {prompt[:100]}...", task_context="LLM")
            
            self.is_running = True
            start_time = time.time()
            
            # モニタリングスレッド開始
            monitor_thread = threading.Thread(
                target=self.monitor_inference,
                args=(start_time, TugumiConfig.INFERENCE_TIMEOUT),
                daemon=True
            )
            monitor_thread.start()
            
            try:
                response = requests.post(
                    self.url,
                    json=payload,
                    timeout=TugumiConfig.LLM_TIMEOUT
                )
                
                elapsed = time.time() - start_time
                self.logger.log(
                    f"Inference completed in {elapsed:.1f}s",
                    level="INFO",
                    task_context="LLM"
                )
                
                if response.status_code == 200:
                    result = response.json().get("content", "")
                    self.is_running = False
                    return result.strip()
                else:
                    self.logger.log(
                        f"LLM error: {response.status_code}",
                        level="ERROR"
                    )
                    return None
            
            except requests.exceptions.Timeout:
                self.logger.log(
                    "LLM inference timeout",
                    level="ERROR",
                    task_context="LLM"
                )
                return None
            
            except Exception as e:
                self.logger.log(
                    f"LLM inference failed: {str(e)}",
                    level="ERROR"
                )
                return None
            
            finally:
                self.is_running = False
        
        except Exception as e:
            self.logger.log(f"LLM client error: {str(e)}", level="ERROR")
            return None
    
    def _fallback_response(self, prompt: str) -> str:
        """LLM応答不可時のフォールバック"""
        return f"[FALLBACK] LLM is unavailable. Processing: {prompt[:50]}..."


class TugumiWebScraper:
    """Webスクレイピング・要約モジュール"""
    
    def __init__(self, logger: TugumiLogger):
        self.logger = logger
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': TugumiConfig.DEFAULT_USER_AGENT
        })
    
    def fetch_url_content(self, url: str, timeout: int = TugumiConfig.WEB_TIMEOUT) -> Optional[str]:
        """URLからコンテンツを取得"""
        retry_count = 0
        
        while retry_count < TugumiConfig.MAX_RETRIES:
            try:
                self.logger.log(f"Fetching: {url}", task_context="SCRAPE")
                response = self.session.get(url, timeout=timeout)
                response.raise_for_status()
                
                # エンコーディング自動検出
                response.encoding = response.apparent_encoding or 'utf-8'
                
                self.logger.log(f"Successfully fetched {len(response.text)} bytes", 
                              task_context="SCRAPE")
                return response.text
            
            except requests.exceptions.Timeout:
                retry_count += 1
                if retry_count < TugumiConfig.MAX_RETRIES:
                    self.logger.log(f"Timeout, retrying... ({retry_count}/{TugumiConfig.MAX_RETRIES})",
                                  level="WARN", task_context="SCRAPE")
                    time.sleep(2)
                else:
                    self.logger.log("Max retries exceeded for URL fetch", level="ERROR", 
                                  task_context="SCRAPE")
                    return None
            
            except requests.exceptions.RequestException as e:
                self.logger.log(f"Request error: {str(e)}", level="ERROR", task_context="SCRAPE")
                return None
            
            except Exception as e:
                self.logger.log(f"Error fetching URL: {str(e)}", level="ERROR", task_context="SCRAPE")
                return None
        
        return None
    
    def extract_text_from_html(self, html: str) -> str:
        """HTMLからテキストを抽出（シンプル版）"""
        try:
            # スクリプトとスタイルを削除
            html_clean = re.sub(r'<script.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
            html_clean = re.sub(r'<style.*?</style>', '', html_clean, flags=re.DOTALL | re.IGNORECASE)
            
            # HTMLタグを削除
            text = re.sub(r'<[^>]+>', '\n', html_clean)
            
            # 空白を整理
            text = re.sub(r'\n\s*\n', '\n', text)
            text = re.sub(r'[ \t]+', ' ', text)
            
            return text.strip()
        
        except Exception as e:
            self.logger.log(f"Error extracting text: {str(e)}", level="ERROR", task_context="SCRAPE")
            return ""
    
    def extract_sentences(self, text: str, max_sentences: int = 10) -> List[str]:
        """テキストから文を抽出"""
        try:
            # 句読点で分割
            sentences = re.split(r'[。.!！?？\n]+', text)
            sentences = [s.strip() for s in sentences if len(s.strip()) > 10]
            return sentences[:max_sentences]
        except Exception as e:
            self.logger.log(f"Error extracting sentences: {str(e)}", level="ERROR", task_context="SCRAPE")
            return []
    
    def save_to_file(self, content: str, filename: str, output_dir: Path = None) -> Optional[Path]:
        """コンテンツをテキストファイルに保存"""
        try:
            if output_dir is None:
                output_dir = TugumiConfig.SCRAPE_DIR
            
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # ファイル名を安全にする
            safe_filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
            output_file = output_dir / f"{safe_filename}.txt"
            
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            self.logger.log(f"File saved: {output_file}", task_context="SCRAPE")
            return output_file
        
        except Exception as e:
            self.logger.log(f"Error saving file: {str(e)}", level="ERROR", task_context="SCRAPE")
            return None
    
    def scrape_and_summarize(self, url: str, save_output: bool = True) -> Optional[Dict[str, Any]]:
        """URLをスクレイピングして要約し、ファイルに保存"""
        try:
            # コンテンツを取得
            html = self.fetch_url_content(url)
            if not html:
                return None
            
            # テキストを抽出
            text = self.extract_text_from_html(html)
            if not text:
                self.logger.log("No text content extracted", level="WARN", task_context="SCRAPE")
                return None
            
            # 文を抽出
            sentences = self.extract_sentences(text, max_sentences=15)
            
            # 結果を作成
            result = {
                "url": url,
                "timestamp": datetime.now().isoformat(),
                "full_text": text[:2000],  # 最初の2000文字
                "summary_sentences": sentences,
                "total_chars": len(text),
                "total_sentences": len(sentences)
            }
            
            if save_output:
                # ファイル名を作成
                domain = urlparse(url).netloc.replace('.', '_')
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"scrape_{domain}_{timestamp}"
                
                # 要約をファイルに保存
                summary_content = f"""【Web スクレイピング結果】
==================================================
URL: {url}
取得日時: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
==================================================

【抽出テキスト】
{text}

【要約（主要文）】
{chr(10).join(['- ' + s for s in sentences])}

==================================================
文字数: {len(text)} / 文の数: {len(sentences)}
==================================================
"""
                
                saved_path = self.save_to_file(summary_content, filename)
                if saved_path:
                    result["saved_file"] = str(saved_path)
            
            return result
        
        except Exception as e:
            self.logger.log(f"Scraping and summarization error: {str(e)}", 
                          level="ERROR", task_context="SCRAPE")
            traceback.print_exc()
            return None


class TugumiToolKit:
    """ツールキット"""
    
    def __init__(self, logger: TugumiLogger):
        self.logger = logger
        self.scraper = TugumiWebScraper(logger)
    
    def search_web(self, query: str, max_results: int = 5) -> List[Dict[str, str]]:
        """DuckDuckGoでウェブ検索"""
        self.logger.log(f"Web search: {query}", task_context="SEARCH")
        
        try:
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=max_results))
            
            self.logger.log(f"Found {len(results)} results", task_context="SEARCH")
            return results
        
        except Exception as e:
            self.logger.log(
                f"Search failed: {str(e)}",
                level="ERROR",
                task_context="SEARCH"
            )
            return []
    
    def scrape_url(self, url: str) -> Optional[Dict[str, Any]]:
        """URLをスクレイピングして要約"""
        return self.scraper.scrape_and_summarize(url, save_output=True)
    
    def scrape_urls_batch(self, urls: List[str]) -> List[Dict[str, Any]]:
        """複数のURLをバッチスクレイピング"""
        results = []
        
        for url in urls:
            try:
                result = self.scrape_url(url)
                if result:
                    results.append(result)
            except Exception as e:
                self.logger.log(f"Error scraping {url}: {str(e)}", level="ERROR", task_context="SCRAPE")
        
        return results
    
    def execute_command(self, command: str, shell: bool = True) -> Dict[str, Any]:
        """シェルコマンドを実行"""
        self.logger.log(f"Executing command: {command}", task_context="EXEC")
        
        try:
            result = subprocess.run(
                command,
                shell=shell,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            output = {
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr
            }
            
            self.logger.log(
                f"Command completed with code {result.returncode}",
                task_context="EXEC"
            )
            
            return output
        
        except subprocess.TimeoutExpired:
            self.logger.log(
                f"Command timeout",
                level="ERROR",
                task_context="EXEC"
            )
            return {"returncode": -1, "stdout": "", "stderr": "Command timeout"}
        
        except Exception as e:
            self.logger.log(
                f"Command execution failed: {str(e)}",
                level="ERROR",
                task_context="EXEC"
            )
            return {"returncode": -1, "stdout": "", "stderr": str(e)}
    
    def install_library(self, library_name: str) -> bool:
        """pipでライブラリをインストール"""
        self.logger.log(f"Installing library: {library_name}", task_context="INSTALL")
        
        try:
            result = self.execute_command(
                f"{sys.executable} -m pip install {library_name}"
            )
            
            if result["returncode"] == 0:
                self.logger.log(
                    f"Library installed successfully: {library_name}",
                    task_context="INSTALL"
                )
                return True
            else:
                self.logger.log(
                    f"Library installation failed: {result['stderr']}",
                    level="ERROR",
                    task_context="INSTALL"
                )
                return False
        
        except Exception as e:
            self.logger.log(f"Error installing library: {str(e)}", level="ERROR", task_context="INSTALL")
            return False


class TugumiMind:
    """TUGUMI エージェントの思考エンジン"""
    
    def __init__(self):
        try:
            self.logger = TugumiLogger()
            self.llm_client = TugumiLLMClient(self.logger)
            self.toolkit = TugumiToolKit(self.logger)
            self.task_history = []
            self.execution_count = 0
            
            self.logger.log("TugumiMind initialized successfully", task_context="INIT")
        
        except Exception as e:
            print(f"Fatal error initializing TugumiMind: {e}")
            traceback.print_exc()
            raise
    
    def system_prompt(self) -> str:
        """システムプロンプト"""
        return """You are TUGUMI, an autonomous AI agent running on Android Termux with local LLM (llama.cpp).

Your capabilities:
- Understand user tasks and break them into actionable steps
- Use web search (DuckDuckGo) to find information
- Scrape and summarize web content, saving to text files
- Execute shell commands via subprocess
- Install Python libraries when needed
- Learn from errors and self-correct
- Log all actions for memory and debugging
- Make decisions autonomously without waiting for user input
- Save scraped content to /storage/emulated/0/AgentDesk (Android) or ~/Documents/TUGUMI (other systems)

Your approach:
1. Analyze the task thoroughly
2. Search for required knowledge if needed
3. Install necessary tools/libraries autonomously
4. Execute the task step by step
5. Scrape web content when needed and save results
6. Verify results and self-correct if needed
7. Log everything for future reference

You are NOT limited by user confirmation. Execute tasks autonomously.
You MUST think step-by-step and provide clear reasoning before executing."""
    
    def analyze_task(self, task: str) -> Dict[str, Any]:
        """タスクを分析してアクションプランを生成"""
        prompt = f"""Analyze this task and create an action plan:

Task: {task}

Provide your analysis in JSON format with:
- task_type: (search/execute/research/problem_solving/scraping)
- required_knowledge: list of things to research
- required_tools: list of tools/libraries needed
- action_steps: numbered steps to complete the task
- potential_issues: possible obstacles
- self_correction_strategy: how to handle failures"""
        
        try:
            response = self.llm_client.infer(prompt, self.system_prompt())
            
            if response:
                try:
                    # JSONを抽出
                    json_match = re.search(r'\{.*\}', response, re.DOTALL)
                    if json_match:
                        return json.loads(json_match.group())
                except Exception as e:
                    self.logger.log(f"Error parsing task analysis JSON: {e}", level="WARN", task_context="ANALYZE")
            
            # デフォルト返却
            return {
                "task_type": "general",
                "required_knowledge": [],
                "required_tools": [],
                "action_steps": ["Execute task"],
                "potential_issues": [],
                "self_correction_strategy": "Log errors and retry with different approach"
            }
        
        except Exception as e:
            self.logger.log(f"Error in task analysis: {e}", level="ERROR", task_context="ANALYZE")
            return {
                "task_type": "general",
                "required_knowledge": [],
                "required_tools": [],
                "action_steps": ["Execute task"],
                "potential_issues": [str(e)],
                "self_correction_strategy": "Fallback: direct execution"
            }
    
    def execute_action(self, action: str, context: str = "") -> str:
        """アクションを実行"""
        prompt = f"""Execute this action autonomously:

Action: {action}
Context: {context}

If you need to:
- Search information: Use web search
- Scrape web content: Use web scraping
- Install packages: Use pip
- Run commands: Use subprocess
- Fix errors: Self-correct and retry

Provide clear output of what was done."""
        
        try:
            response = self.llm_client.infer(prompt, self.system_prompt())
            return response if response else "Action execution failed"
        
        except Exception as e:
            self.logger.log(f"Error executing action: {e}", level="ERROR", task_context="ACTION")
            return f"Error: {str(e)}"
    
    def run_task(self, task: str, auto_correct: bool = True) -> Dict[str, Any]:
        """タスクを実行"""
        self.execution_count += 1
        task_id = f"TASK_{self.execution_count}_{int(time.time())}"
        
        self.logger.log(f"Starting task: {task}", task_context=task_id)
        
        result = {
            "task_id": task_id,
            "task": task,
            "status": "running",
            "analysis": {},
            "execution_steps": [],
            "errors": [],
            "final_output": "",
            "execution_time": 0
        }
        
        start_time = time.time()
        
        try:
            # タスク分析
            self.logger.log("Analyzing task...", task_context=task_id)
            analysis = self.analyze_task(task)
            result["analysis"] = analysis
            self.logger.log(f"Analysis: {json.dumps(analysis, ensure_ascii=False)}", task_context=task_id)
            
            # 必要なツールをインストール
            for tool in analysis.get("required_tools", []):
                try:
                    self.logger.log(f"Checking tool: {tool}", task_context=task_id)
                    self.toolkit.install_library(tool)
                except Exception as e:
                    self.logger.log(f"Tool install warning: {e}", level="WARN", task_context=task_id)
            
            # 必要な知識を検索
            search_context = ""
            for knowledge in analysis.get("required_knowledge", []):
                try:
                    self.logger.log(f"Searching knowledge: {knowledge}", task_context=task_id)
                    search_results = self.toolkit.search_web(knowledge)
                    search_context += f"\n{knowledge}:\n"
                    for res in search_results:
                        search_context += f"- {res.get('title', 'N/A')}: {res.get('body', 'N/A')[:100]}\n"
                except Exception as e:
                    self.logger.log(f"Search error: {e}", level="WARN", task_context=task_id)
            
            # アクションステップを実行
            for i, step in enumerate(analysis.get("action_steps", []), 1):
                self.logger.log(f"Step {i}: {step}", task_context=task_id)
                
                try:
                    output = self.execute_action(step, search_context)
                    result["execution_steps"].append({
                        "step": i,
                        "action": step,
                        "output": output
                    })
                
                except Exception as e:
                    error_msg = str(e)
                    self.logger.log(f"Step {i} error: {error_msg}", level="ERROR", task_context=task_id)
                    result["errors"].append({"step": i, "error": error_msg})
                    
                    if auto_correct:
                        try:
                            self.logger.log(f"Attempting auto-correction for step {i}", task_context=task_id)
                            retry_output = self.execute_action(f"Fix and retry: {step}", search_context)
                            result["execution_steps"].append({
                                "step": f"{i}_retry",
                                "action": step,
                                "output": retry_output
                            })
                        except Exception as retry_error:
                            self.logger.log(f"Auto-correction failed: {retry_error}", 
                                          level="ERROR", task_context=task_id)
            
            result["status"] = "completed"
            
            try:
                result["final_output"] = self.llm_client.infer(
                    f"Summarize the task results:\n{json.dumps(result, ensure_ascii=False)}",
                    self.system_prompt()
                ) or "Task completed"
            except Exception as e:
                self.logger.log(f"Error generating final output: {e}", level="WARN", task_context=task_id)
                result["final_output"] = "Task completed with warnings"
        
        except Exception as e:
            self.logger.log(f"Task failed: {str(e)}", level="ERROR", task_context=task_id)
            result["status"] = "failed"
            result["final_output"] = str(e)
            result["errors"].append({"general": str(e)})
        
        finally:
            result["execution_time"] = time.time() - start_time
            self.logger.log(
                f"Task completed in {result['execution_time']:.2f}s. Status: {result['status']}",
                task_context=task_id
            )
            
            # 結果をメモリに保存
            try:
                self.logger.save_memory(task_id, result)
            except Exception as e:
                self.logger.log(f"Failed to save task memory: {e}", level="WARN", task_context=task_id)
            
            self.task_history.append(task_id)
        
        return result


def main():
    """メイン関数"""
    try:
        print("\n" + "="*60)
        print("TUGUMI - Autonomous AI Agent")
        print("Local LLM (llama.cpp) powered")
        print("="*60 + "\n")
        
        agent = TugumiMind()
        
        # LLMが起動しているか確認
        if not agent.llm_client.check_llm_alive():
            print("ERROR: LLM (llama.cpp) is not running at http://0.0.0.0:8080")
            print("Please start llama.cpp server with: llama-server -m model.gguf")
            return
        
        print("LLM Status: ✓ Connected\n")
        
        # ストレージ情報を表示
        print(f"Storage Location: {TugumiConfig.BASE_DIR}")
        print(f"Output Directory: {TugumiConfig.SCRAPE_DIR}\n")
        
        # インタラクティブループ
        print("Commands:")
        print("  'task <description>' - Execute a task")
        print("  'scrape <url>' - Scrape and summarize a URL")
        print("  'search <query>' - Search the web")
        print("  'status' - Show current status")
        print("  'logs' - Show recent logs")
        print("  'history' - Show task history")
        print("  'quit' - Exit\n")
        
        while True:
            try:
                user_input = input("\nTUGUMI> ").strip()
                
                if not user_input:
                    continue
                
                if user_input.lower() == "quit":
                    print("Shutting down TUGUMI...")
                    break
                
                elif user_input.lower() == "status":
                    print(f"Execution count: {agent.execution_count}")
                    print(f"Task history: {len(agent.task_history)}")
                    print(f"Output directory: {TugumiConfig.SCRAPE_DIR}")
                
                elif user_input.lower() == "logs":
                    for log in agent.logger.get_logs(10):
                        print(log)
                
                elif user_input.lower() == "history":
                    for task_id in agent.task_history[-5:]:
                        print(f"- {task_id}")
                
                elif user_input.startswith("scrape "):
                    url = user_input[7:].strip()
                    if url:
                        print(f"\nScraping URL: {url}")
                        result = agent.toolkit.scrape_url(url)
                        if result:
                            print(f"✓ Scraping completed")
                            print(f"  Saved to: {result.get('saved_file', 'N/A')}")
                            print(f"  Characters: {result.get('total_chars', 0)}")
                            print(f"  Sentences: {result.get('total_sentences', 0)}")
                        else:
                            print("✗ Scraping failed")
                
                elif user_input.startswith("search "):
                    query = user_input[7:].strip()
                    if query:
                        print(f"\nSearching: {query}")
                        results = agent.toolkit.search_web(query, max_results=5)
                        for i, result in enumerate(results, 1):
                            print(f"\n{i}. {result.get('title', 'N/A')}")
                            print(f"   {result.get('body', 'N/A')[:100]}...")
                
                elif user_input.startswith("task "):
                    task = user_input[5:].strip()
                    if task:
                        print(f"\nExecuting task: {task}")
                        result = agent.run_task(task)
                        print(f"\nTask Result:")
                        print(json.dumps(result, ensure_ascii=False, indent=2))
                
                else:
                    print("Unknown command. Type 'task <description>' to run a task.")
            
            except KeyboardInterrupt:
                print("\n\nShutting down...")
                break
            
            except Exception as e:
                print(f"Error: {str(e)}")
                traceback.print_exc()
    
    except Exception as e:
        print(f"Fatal error in main: {e}")
        traceback.print_exc()


if __name__ == "__main__":
    main()
