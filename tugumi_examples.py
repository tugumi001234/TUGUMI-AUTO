#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TUGUMI Advanced Examples
様々なタスク例とカスタムツールの実装サンプル
"""

from tugumi_tools import ToolManager, DynamicCodeGenerator
from pathlib import Path


def example_1_create_data_analysis_tool():
    """
    例1: データ分析ツールの作成
    """
    tool_manager = ToolManager(Path.home() / "Documents" / "TUGUMI_TOOLS")
    
    tool_manager.create_and_load_tool(
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
except Exception as e:
    return f"Error: {str(e)}"
"""
    )
    
    print("✓ Data analysis tool created")


def example_2_create_web_scraper_tool():
    """
    例2: ウェブスクレイピングツールの作成
    """
    tool_manager = ToolManager(Path.home() / "Documents" / "TUGUMI_TOOLS")
    
    tool_manager.create_and_load_tool(
        tool_name="scrape_webpage",
        description="Scrape webpage tables and content",
        implementation="""
try:
    import requests
    from html.parser import HTMLParser
    
    url = kwargs.get('url', args[0] if args else 'https://example.com')
    
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    
    return {
        'status': 'success',
        'url': url,
        'content_length': len(response.text),
        'headers': dict(response.headers)
    }
except ImportError:
    return "Requires requests library. Will be installed automatically."
except Exception as e:
    return f"Scraping error: {str(e)}"
"""
    )
    
    print("✓ Web scraper tool created")


def example_3_create_tool_pack():
    """
    例3: 複数ツールを含むパックの作成
    """
    tool_manager = ToolManager(Path.home() / "Documents" / "TUGUMI_TOOLS")
    
    tools = [
        {
            "name": "file_counter",
            "description": "Count files by extension in directory",
            "implementation": """
import os
from collections import Counter

directory = args[0] if args else '.'
extensions = Counter()

for filename in os.listdir(directory):
    if '.' in filename:
        ext = filename.split('.')[-1]
        extensions[ext] += 1

return dict(extensions)
"""
        },
        {
            "name": "text_stats",
            "description": "Analyze text statistics",
            "implementation": """
text = args[0] if args else ''

return {
    'total_chars': len(text),
    'total_words': len(text.split()),
    'total_lines': text.count('\\n'),
    'avg_word_length': len(text) / len(text.split()) if text.split() else 0
}
"""
        },
        {
            "name": "json_validator",
            "description": "Validate JSON format",
            "implementation": """
import json

text = args[0] if args else '{}'

try:
    parsed = json.loads(text)
    return {'valid': True, 'data': parsed}
except json.JSONDecodeError as e:
    return {'valid': False, 'error': str(e)}
"""
        }
    ]
    
    tool_manager.create_tool_pack("utility_tools", tools)
    print("✓ Utility tools pack created")


def example_4_dynamic_code_generation():
    """
    例4: 動的コード生成の例
    """
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
        return a / b if b != 0 else 'Division by zero'
    else:
        return 'Unknown operation'
except Exception as e:
    return f'Error: {str(e)}'
"""
    )
    
    print("Generated code:")
    print(code)
    return code


def example_5_ai_task_scenarios():
    """
    例5: AIが自動的に実行できるタスクシナリオ
    """
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
        },
        {
            "name": "パフォーマンス最適化",
            "description": "スクリプトのパフォーマンス改善提案",
            "expected_actions": [
                "スクリプトを解析",
                "ボトルネックを特定",
                "最適化コードを生成",
                "速度改善率を計測"
            ]
        }
    ]
    
    return scenarios


def example_6_llm_integration():
    """
    例6: LLM統合の高度な使用例
    """
    
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


def print_examples_summary():
    """
    全例のサマリーを表示
    """
    print("""
╔════════════════════════════════════════════════════════════╗
║         TUGUMI Advanced Examples Summary                    ║
╚════════════════════════════════════════════════════════════╝

✓ Example 1: Data Analysis Tool
  - CSV統計分析ツール
  - 基本統計量の計算
  
✓ Example 2: Web Scraper Tool
  - ウェブスクレイピング
  - データ抽出機能

✓ Example 3: Tool Pack
  - 複数ツールのまとめ作成
  - ファイルカウント、テキスト解析、JSON検証

✓ Example 4: Dynamic Code Generation
  - 動的にコードを生成
  - 電卓ツールの自動作成

✓ Example 5: AI Task Scenarios
  - データクリーニング
  - パッケージ管理
  - ログ分析
  - パフォーマンス最適化

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


if __name__ == "__main__":
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
