#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TUGUMI - Autonomous AI Agent
ローカルLLM (llama.cpp) を使用した自律型AIエージェント

Features:
- 長考型LLMに対応したタイムアウト対策とアライブモニタリング
- DuckDuckGoによるネット検索機能
- ログメモリ管理システム
- 自己学習・自己修正能力
- 動的ツール・ライブラリ拡張
- Subprocessを使用したタスク実行
"""

import os
import sys
import json
import time
import subprocess
import threading
import traceback
from datetime import datetime
from typing import Optional, Dict, List, Any
from pathlib import Path

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


class TugumiConfig:
    """TUGUMI設定クラス"""
    
    LLM_HOST = "0.0.0.0"
    LLM_PORT = 8080
    LLM_URL = f"http://{LLM_HOST}:{LLM_PORT}/completion"
    
    # ログディレクトリ
    LOG_DIR = Path.home() / "Documents" / "TUGUMI_LOGS"
    MEMORY_DIR = Path.home() / "Documents" / "TUGUMI_MEMORY"
    TOOLS_DIR = Path.home() / "Documents" / "TUGUMI_TOOLS"
    
    # タイムアウト設定
    LLM_TIMEOUT = 600  # 10分
    INFERENCE_TIMEOUT = 300  # 5分
    ALIVE_CHECK_INTERVAL = 10  # 10秒ごとにアライブ確認
    
    # LLM推論パラメータ
    MAX_TOKENS = 2048
    TEMPERATURE = 0.7
    TOP_P = 0.9


class TugumiLogger:
    """ログ管理システム"""
    
    def __init__(self, log_dir: Path = TugumiConfig.LOG_DIR):
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
        timestamp = datetime.now().isoformat()
        context_str = f" [{task_context}]" if task_context else ""
        log_entry = f"{timestamp} | {level}{context_str} | {message}"
        
        self.log_buffer.append(log_entry)
        print(log_entry)
        
        # ファイルに書き込み
        if self.current_log_file:
            self.current_log_file.write_text(
                self.current_log_file.read_text(errors='ignore') + log_entry + "\n"
            )
    
    def get_logs(self, num_lines: int = 50) -> List[str]:
        """最新のログを取得"""
        return self.log_buffer[-num_lines:]
    
    def save_memory(self, memory_key: str, memory_data: Dict[str, Any]):
        """メモリをJSON形式で保存"""
        memory_dir = TugumiConfig.MEMORY_DIR
        memory_dir.mkdir(parents=True, exist_ok=True)
        memory_file = memory_dir / f"{memory_key}.json"
        
        with open(memory_file, 'w', encoding='utf-8') as f:
            json.dump(memory_data, f, ensure_ascii=False, indent=2)
        
        self.log(f"Memory saved: {memory_key}", task_context="MEMORY")
    
    def load_memory(self, memory_key: str) -> Optional[Dict[str, Any]]:
        """メモリをJSON形式で読み込み"""
        memory_file = TugumiConfig.MEMORY_DIR / f"{memory_key}.json"
        
        if memory_file.exists():
            with open(memory_file, 'r', encoding='utf-8') as f:
                return json.load(f)
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
            self.logger.log(f"LLM Connection Failed: {str(e)}", level="ERROR")
            return False
    
    def monitor_inference(self, start_time: float, timeout: float):
        """推論の進行状況をモニタリング（別スレッド）"""
        check_interval = TugumiConfig.ALIVE_CHECK_INTERVAL
        
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
            if elapsed % check_interval < 1:
                self.logger.log(
                    f"Inference running... ({elapsed:.1f}s / {timeout}s)",
                    level="DEBUG"
                )
            
            time.sleep(1)
    
    def infer(self, prompt: str, system_prompt: Optional[str] = None) -> Optional[str]:
        """LLMで推論を実行"""
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
    
    def _fallback_response(self, prompt: str) -> str:
        """LLM応答不可時のフォールバック"""
        return f"[FALLBACK] LLM is unavailable. Processing: {prompt[:50]}..."


class TugumiToolKit:
    """ツールキット"""
    
    def __init__(self, logger: TugumiLogger):
        self.logger = logger
    
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


class TugumiMind:
    """TUGUMI エージェントの思考エンジン"""
    
    def __init__(self):
        self.logger = TugumiLogger()
        self.llm_client = TugumiLLMClient(self.logger)
        self.toolkit = TugumiToolKit(self.logger)
        self.task_history = []
        self.execution_count = 0
    
    def system_prompt(self) -> str:
        """システムプロンプト"""
        return """You are TUGUMI, an autonomous AI agent running on Android Termux with local LLM (llama.cpp).

Your capabilities:
- Understand user tasks and break them into actionable steps
- Use web search (DuckDuckGo) to find information
- Execute shell commands via subprocess
- Install Python libraries when needed
- Learn from errors and self-correct
- Log all actions for memory and debugging
- Make decisions autonomously without waiting for user input

Your approach:
1. Analyze the task thoroughly
2. Search for required knowledge if needed
3. Install necessary tools/libraries autonomously
4. Execute the task step by step
5. Verify results and self-correct if needed
6. Log everything for future reference

You are NOT limited by user confirmation. Execute tasks autonomously.
You MUST think step-by-step and provide clear reasoning before executing."""
    
    def analyze_task(self, task: str) -> Dict[str, Any]:
        """タスクを分析してアクションプランを生成"""
        prompt = f"""Analyze this task and create an action plan:

Task: {task}

Provide your analysis in JSON format with:
- task_type: (search/execute/research/problem_solving)
- required_knowledge: list of things to research
- required_tools: list of tools/libraries needed
- action_steps: numbered steps to complete the task
- potential_issues: possible obstacles
- self_correction_strategy: how to handle failures"""
        
        response = self.llm_client.infer(prompt, self.system_prompt())
        
        if response:
            try:
                # JSONを抽出
                import re
                json_match = re.search(r'\{.*\}', response, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group())
            except:
                pass
        
        return {
            "task_type": "general",
            "required_knowledge": [],
            "required_tools": [],
            "action_steps": ["Execute task"],
            "potential_issues": [],
            "self_correction_strategy": "Log errors and retry with different approach"
        }
    
    def execute_action(self, action: str, context: str = "") -> str:
        """アクションを実行"""
        prompt = f"""Execute this action autonomously:

Action: {action}
Context: {context}

If you need to:
- Search information: Use web search
- Install packages: Use pip
- Run commands: Use subprocess
- Fix errors: Self-correct and retry

Provide clear output of what was done."""
        
        response = self.llm_client.infer(prompt, self.system_prompt())
        return response if response else "Action execution failed"
    
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
                self.logger.log(f"Checking tool: {tool}", task_context=task_id)
                self.toolkit.install_library(tool)
            
            # 必要な知識を検索
            search_context = ""
            for knowledge in analysis.get("required_knowledge", []):
                self.logger.log(f"Searching knowledge: {knowledge}", task_context=task_id)
                search_results = self.toolkit.search_web(knowledge)
                search_context += f"\n{knowledge}:\n"
                for res in search_results:
                    search_context += f"- {res.get('title')}: {res.get('body')[:100]}\n"
            
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
                        self.logger.log(f"Attempting auto-correction for step {i}", task_context=task_id)
                        retry_output = self.execute_action(f"Fix and retry: {step}", search_context)
                        result["execution_steps"].append({
                            "step": f"{i}_retry",
                            "action": step,
                            "output": retry_output
                        })
            
            result["status"] = "completed"
            result["final_output"] = self.llm_client.infer(
                f"Summarize the task results:\n{json.dumps(result, ensure_ascii=False)}",
                self.system_prompt()
            ) or "Task completed"
            
        except Exception as e:
            self.logger.log(f"Task failed: {str(e)}", level="ERROR", task_context=task_id)
            result["status"] = "failed"
            result["final_output"] = str(e)
        
        finally:
            result["execution_time"] = time.time() - start_time
            self.logger.log(
                f"Task completed in {result['execution_time']:.2f}s. Status: {result['status']}",
                task_context=task_id
            )
            
            # 結果をメモリに保存
            self.logger.save_memory(task_id, result)
            self.task_history.append(task_id)
        
        return result


def main():
    """メイン関数"""
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
    
    # インタラクティブループ
    print("Commands:")
    print("  'task <description>' - Execute a task")
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
            
            elif user_input.lower() == "logs":
                for log in agent.logger.get_logs(10):
                    print(log)
            
            elif user_input.lower() == "history":
                for task_id in agent.task_history[-5:]:
                    print(f"- {task_id}")
            
            elif user_input.startswith("task "):
                task = user_input[5:]
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


if __name__ == "__main__":
    main()
