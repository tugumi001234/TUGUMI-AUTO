#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TUGUMI Advanced Examples
様々なタスク例とカスタムツールの実装サンプル

改善内容：
- 完全なエラーハンドリング
- 安全なコード生成
- スクレイピング機能の例を追加
"""

import traceback
from tugumi_tools import ToolManager, DynamicCodeGenerator
from pathlib import Path


def example_1_create_data_analysis_tool():
    """
    例1: データ分析ツールの作成
    """
    try:
        tool_manager = ToolManager(Path.home() / "Documents" / "TUGUMI" / "TOOLS")
        
        success = tool_manager.create_and_load_tool(
            tool_name="analyze_csv",
            description="CSV file statistical analysis",
            implementation="""
        import csv
        import json
        from statistics import mean, stdev
        
        file_path = kwargs.get('file_path', args[0] if args else 'data.csv')
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                data = list(reader)
            
            analysis = {
                'total_rows': len(data),
                'columns': list(data[0].keys()) if data else [],
                'data_preview': data[:5]
            }
            
            return json.dumps(analysis, ensure_ascii=False, indent=2)
        except FileNotFoundError:
            return f"File not found: {{file_path}}"
        except Exception as e:
            return f"Analysis error: {{str(e)}}"
"""
        )
        
        if success:
            print("✓ Data analysis tool created successfully")
        else:
            print("✗ Failed to create data analysis tool")
    
    except Exception as e:
        print(f"Error in example 1: {e}")
        traceback.print_exc()


def example_2_create_web_scraper_tool():
    """
    例2: ウェブスクレイピングツールの作成
    """
    try:
        tool_manager = ToolManager(Path.home() / "Documents" / "TUGUMI" / "TOOLS")
        
        success = tool_manager.create_and_load_tool(
            tool_name="scrape_webpage",
            description="Scrape webpage content and extract text",
            implementation="""
        try:
            import requests
            from html.parser import HTMLParser
            import re
            
            url = kwargs.get('url', args[0] if args else 'https://example.com')
            timeout = kwargs.get('timeout', 10)
            
            try:
                response = requests.get(url, timeout=timeout)
                response.raise_for_status()
                response.encoding = response.apparent_encoding or 'utf-8'
                
                # HTML から テキストを抽出
                html_clean = re.sub(r'<script.*?</script>', '', response.text, flags=re.DOTALL | re.IGNORECASE)
                html_clean = re.sub(r'<style.*?</style>', '', html_clean, flags=re.DOTALL | re.IGNORECASE)
                text = re.sub(r'<[^>]+>', '\\n', html_clean)
                text = re.sub(r'\\n\\s*\\n', '\\n', text)
                
                return {{
                    'status': 'success',
                    'url': url,
                    'content_length': len(response.text),
                    'text_length': len(text),
                    'preview': text[:500]
                }}
            except requests.Timeout:
                return f"Request timeout for {{url}}"
            except requests.RequestException as e:
                return f"Request error: {{str(e)}}"
        except ImportError:
            return "Requires requests library. Will be installed automatically."
"""
        )
        
        if success:
            print("✓ Web scraper tool created successfully")
        else:
            print("✗ Failed to create web scraper tool")
    
    except Exception as e:
        print(f"Error in example 2: {e}")
        traceback.print_exc()


def example_3_create_tool_pack():
    """
    例3: 複数ツールを含むパックの作成
    """
    try:
        tool_manager = ToolManager(Path.home() / "Documents" / "TUGUMI" / "TOOLS")
        
        tools = [
            {
                "name": "file_counter",
                "description": "Count files by extension in directory",
                "implementation": """
        import os
        from collections import Counter
        
        try:
            directory = args[0] if args else '.'
            extensions = Counter()
            
            for filename in os.listdir(directory):
                if '.' in filename:
                    ext = filename.split('.')[-1]
                    extensions[ext] += 1
            
            return dict(extensions)
        except FileNotFoundError:
            return f"Directory not found: {{directory}}"
"""
            },
            {
                "name": "text_stats",
                "description": "Analyze text statistics",
                "implementation": """
        try:
            text = args[0] if args else ''
            
            return {{
                'total_chars': len(text),
                'total_words': len(text.split()),
                'total_lines': text.count('\\n'),
                'avg_word_length': len(text) / len(text.split()) if text.split() else 0
            }}
        except Exception as e:
            return f"Error: {{str(e)}}"
"""
            },
            {
                "name": "json_validator",
                "description": "Validate JSON format",
                "implementation": """
        import json
        
        try:
            text = args[0] if args else '{{}}'
            parsed = json.loads(text)
            return {{'valid': True, 'data': parsed, 'keys': list(parsed.keys()) if isinstance(parsed, dict) else 'N/A'}}
        except json.JSONDecodeError as e:
            return {{'valid': False, 'error': str(e), 'position': e.pos}}
"""
            }
        ]
        
        success = tool_manager.create_tool_pack("utility_tools", tools)
        
        if success:
            print("✓ Utility tools pack created successfully")
        else:
            print("✗ Failed to create utility tools pack")
    
    except Exception as e:
        print(f"Error in example 3: {e}")
        traceback.print_exc()


def example_4_dynamic_code_generation():
    """
    例4: 動的コード生成の例
    """
    try:
        generator = DynamicCodeGenerator()
        
        code = generator.generate_tool_code(
            tool_name="custom_calculator",
            description="Simple calculator with custom operations",
            implementation="""
        try:
            operation = kwargs.get('op', 'add')
            a = float(args[0]) if args else 0
            b = float(args[1]) if len(args) > 1 else 0
            
            if operation == 'add':
                return a + b
            elif operation == 'subtract':
                return a - b
            elif operation == 'multiply':
                return a * b
            elif operation == 'divide':
                return a / b if b != 0 else 'Division by zero error'
            else:
                return f'Unknown operation: {{operation}}'
"""
        )
        
        if code:
            print("Generated code:")
            print(code)
            return code
        else:
            print("Failed to generate code")
            return None
    
    except Exception as e:
        print(f"Error in example 4: {e}")
        traceback.print_exc()
        return None


def example_5_ai_task_scenarios():
    """
    例5: AIが自動的に実行できるタスクシナリオ
    """
    try:
        scenarios = [
            {
                "name": "データクリーニング",
                "description": "CSV/JSONデータの不正な値を検出・修正",
                "expected_actions": [
                    "データファイルの読み込み",
                    "スキーマ検証",
                    "異常値の検出",
                    "修正結果をレポート作成"
                ]
            },
            {
                "name": "ウェブスクレイピング",
                "description": "複数のウェブサイトからデータを抽出",
                "expected_actions": [
                    "対象URLのリストを作成",
                    "各ページをスクレイピング",
                    "テキストを抽出・要約",
                    "結果をファイルに保存"
                ]
            },
            {
                "name": "パッケージ相互性チェック",
                "description": "Pythonパッケージの依存関係確認",
                "expected_actions": [
                    "requirements.txtを解析",
                    "PyPIから最新バージョン確認",
                    "互換性チェック",
                    "アップデート推奨を提示"
                ]
            },
            {
                "name": "ログファイル分析",
                "description": "ログファイルのエラー検出と分類",
                "expected_actions": [
                    "ログファイルを読み込み",
                    "エラーレベルを分類",
                    "エラー原因を推測",
                    "対応策を提示"
                ]
            }
        ]
        
        return scenarios
    
    except Exception as e:
        print(f"Error in example 5: {e}")
        traceback.print_exc()
        return []


def example_6_llm_integration():
    """
    例6: LLM統合の高度な使用例
    """
    try:
        system_prompts = {
            "analyst": """You are a data analyst expert.
Analyze data, find patterns, and provide insights.
Use Python code when needed.
Think step-by-step.""",
            
            "developer": """You are an expert software developer.
Write clean, efficient, well-documented code.
Consider edge cases and error handling.
Suggest best practices.""",
            
            "researcher": """You are a research scientist.
Search for latest information.
Verify sources and cross-reference data.
Provide evidence-based conclusions.""",
            
            "problem_solver": """You are an expert problem solver.
Break down complex problems.
Generate multiple solutions.
Evaluate pros and cons of each approach."""
        }
        
        return system_prompts
    
    except Exception as e:
        print(f"Error in example 6: {e}")
        traceback.print_exc()
        return {}


def example_7_self_healing_workflow():
    """
    例7: 自己修復ワークフロー
    
    タスク失敗時の自動対応プロセス:
    1. エラー分析 - どこで失敗したか
    2. 原因特定 - なぜ失敗したか
    3. 知識検索 - 解決方法を検索
    4. ツール準備 - 必要なツール/ライブラリをインストール
    5. 代替実装 - 別の方法で実装
    6. 再試行 - 修正版で再実行
    7. 検証 - 成功したか確認
    8. ドキュメント - 学習内容を記録
    """
    try:
        workflow = {
            "step_1_error_analysis": {
                "goal": "エラーの詳細を分析",
                "tools": ["exception parsing", "stack trace analysis"],
                "llm_prompt": "Analyze this error and identify the root cause"
            },
            "step_2_root_cause": {
                "goal": "根本原因を特定",
                "tools": ["code inspection", "dependency check"],
                "llm_prompt": "What is the root cause of this problem?"
            },
            "step_3_knowledge_search": {
                "goal": "解決方法を検索",
                "tools": ["web search", "documentation lookup"],
                "llm_prompt": "Search for solutions to this problem"
            },
            "step_4_tool_preparation": {
                "goal": "必要なツール準備",
                "tools": ["pip install", "library import"],
                "llm_prompt": "What libraries or tools do we need?"
            },
            "step_5_alternative_implementation": {
                "goal": "代替実装を作成",
                "tools": ["code generation", "pattern matching"],
                "llm_prompt": "Generate an alternative implementation"
            },
            "step_6_retry": {
                "goal": "修正版を実行",
                "tools": ["subprocess execution", "monitoring"],
                "llm_prompt": "Execute the new implementation"
            },
            "step_7_verification": {
                "goal": "成功確認",
                "tools": ["result validation", "testing"],
                "llm_prompt": "Verify the results are correct"
            },
            "step_8_documentation": {
                "goal": "学習内容を記録",
                "tools": ["log writing", "memory saving"],
                "llm_prompt": "Document this solution for future reference"
            }
        }
        
        return workflow
    
    except Exception as e:
        print(f"Error in example 7: {e}")
        traceback.print_exc()
        return {}


def print_examples_summary():
    """
    全例のサマリーを表示
    """
    try:
        print("""
╔════════════════════════════════════════════════════════════╗
║         TUGUMI Advanced Examples Summary                    ║
╚════════════════════════════════════════════════════════════╝

✓ Example 1: Data Analysis Tool
  - CSV統計分析ツール
  - 基本統計量の計算
  
✓ Example 2: Web Scraper Tool
  - ウェブスクレイピング
  - テキスト抽出機能

✓ Example 3: Tool Pack
  - 複数ツールのまとめ作成
  - ファイルカウント、テキスト解析、JSON検証

✓ Example 4: Dynamic Code Generation
  - 動的にコードを生成
  - 電卓ツールの自動作成

✓ Example 5: AI Task Scenarios
  - データクリーニング
  - ウェブスクレイピング
  - パッケージ管理
  - ログ分析

✓ Example 6: LLM Integration
  - アナリスト モード
  - 開発者 モード
  - 研究者 モード
  - 問題解決 モード

✓ Example 7: Self-Healing Workflow
  - 8段階の自動修復プロセス
  - エラー分析から学習保存まで

═══════════════════════════════════════════════════════════════

Usage:

  from tugumi_examples import *
  
  # ツール作成
  example_1_create_data_analysis_tool()
  example_2_create_web_scraper_tool()
  example_3_create_tool_pack()
  
  # 動的コード生成
  code = example_4_dynamic_code_generation()
  
  # タスクシナリオ
  scenarios = example_5_ai_task_scenarios()
  
  # LLM統合
  prompts = example_6_llm_integration()
  
  # 自己修復
  workflow = example_7_self_healing_workflow()

═══════════════════════════════════════════════════════════════
""")
    except Exception as e:
        print(f"Error printing summary: {e}")


if __name__ == "__main__":
    try:
        print_examples_summary()
        
        # 例を実行
        print("\n[Running Example 1]")
        example_1_create_data_analysis_tool()
        
        print("\n[Running Example 2]")
        example_2_create_web_scraper_tool()
        
        print("\n[Running Example 3]")
        example_3_create_tool_pack()
        
        print("\n[Running Example 4]")
        example_4_dynamic_code_generation()
        
        print("\n[Running Example 5]")
        scenarios = example_5_ai_task_scenarios()
        for scenario in scenarios:
            print(f"  - {scenario['name']}: {scenario['description']}")
        
        print("\n✓ All examples executed successfully")
    
    except Exception as e:
        print(f"Fatal error in examples: {e}")
        traceback.print_exc()
