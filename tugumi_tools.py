#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TUGUMI Tools Extension Module
動的にツール・ライブラリを拡張できるモジュール
"""

import os
import sys
import json
import importlib.util
from pathlib import Path
from typing import Any, Callable, Dict, List


class ToolRegistry:
    """ツール登録システム"""
    
    def __init__(self, tools_dir: Path):
        self.tools_dir = Path(tools_dir)
        self.tools_dir.mkdir(parents=True, exist_ok=True)
        self.registered_tools: Dict[str, Callable] = {}
        self.tool_metadata: Dict[str, Dict[str, Any]] = {}
    
    def register_tool(self, name: str, func: Callable, metadata: Dict[str, Any] = None):
        """ツールを登録"""
        self.registered_tools[name] = func
        self.tool_metadata[name] = metadata or {
            "description": f"Tool: {name}",
            "parameters": {},
            "return_type": "Any"
        }
    
    def get_tool(self, name: str) -> Callable:
        """ツールを取得"""
        return self.registered_tools.get(name)
    
    def list_tools(self) -> List[str]:
        """登録されているツール一覧"""
        return list(self.registered_tools.keys())
    
    def get_tool_info(self, name: str) -> Dict[str, Any]:
        """ツール情報を取得"""
        return self.tool_metadata.get(name, {})
    
    def load_custom_tool(self, tool_file: Path) -> bool:
        """カスタムツールを動的に読み込み"""
        try:
            spec = importlib.util.spec_from_file_location("custom_tool", tool_file)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # ツール関数を登録
            if hasattr(module, 'register_tools'):
                module.register_tools(self)
                return True
            
            return False
        
        except Exception as e:
            print(f"Failed to load custom tool: {e}")
            return False


class ExtensionManager:
    """拡張マネージャー"""
    
    def __init__(self, tools_dir: Path):
        self.tools_dir = Path(tools_dir)
        self.registry = ToolRegistry(self.tools_dir)
        self._load_builtin_tools()
    
    def _load_builtin_tools(self):
        """組み込みツールを読み込み"""
        self.registry.register_tool(
            "python_exec",
            self.execute_python_code,
            {
                "description": "Execute Python code",
                "parameters": {"code": "Python code string"},
                "return_type": "str"
            }
        )
        
        self.registry.register_tool(
            "install_package",
            self.install_pip_package,
            {
                "description": "Install package from PyPI",
                "parameters": {"package_name": "Package name"},
                "return_type": "bool"
            }
        )
        
        self.registry.register_tool(
            "import_module",
            self.import_module,
            {
                "description": "Dynamically import Python module",
                "parameters": {"module_name": "Module name"},
                "return_type": "module"
            }
        )
    
    def execute_python_code(self, code: str) -> str:
        """Pythonコードを実行"""
        try:
            exec_globals = {}
            exec(code, exec_globals)
            return "Code executed successfully"
        except Exception as e:
            return f"Error executing code: {str(e)}"
    
    def install_pip_package(self, package_name: str) -> bool:
        """pipパッケージをインストール"""
        import subprocess
        try:
            subprocess.run(
                [sys.executable, "-m", "pip", "install", package_name],
                check=True,
                capture_output=True
            )
            return True
        except subprocess.CalledProcessError:
            return False
    
    def import_module(self, module_name: str):
        """モジュールを動的にインポート"""
        try:
            return __import__(module_name)
        except ImportError as e:
            print(f"Failed to import {module_name}: {e}")
            return None
    
    def create_custom_tool_template(self, tool_name: str) -> Path:
        """カスタムツールのテンプレートを作成"""
        template_code = f'''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Custom Tool: {tool_name}
"""

def register_tools(registry):
    """
    ツールを登録する関数
    registry: ToolRegistry インスタンス
    """
    registry.register_tool(
        "{tool_name}",
        execute_{tool_name},
        {{
            "description": "Custom tool: {tool_name}",
            "parameters": {{}},
            "return_type": "str"
        }}
    )

def execute_{tool_name}(*args, **kwargs):
    """
    {tool_name} の実装
    """
    return f"Tool {tool_name} executed with args: {{args}}, kwargs: {{kwargs}}"
'''
        
        tool_file = self.tools_dir / f"{tool_name}.py"
        with open(tool_file, 'w', encoding='utf-8') as f:
            f.write(template_code)
        
        return tool_file
    
    def list_available_tools(self) -> Dict[str, Any]:
        """利用可能なツール一覧"""
        tools = {}
        for tool_name in self.registry.list_tools():
            tools[tool_name] = self.registry.get_tool_info(tool_name)
        return tools


class DynamicCodeGenerator:
    """動的コード生成器"""
    
    @staticmethod
    def generate_tool_code(tool_name: str, description: str, implementation: str) -> str:
        """ツールコードを生成"""
        code = f'''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
{description}
"""

def register_tools(registry):
    registry.register_tool(
        "{tool_name}",
        {tool_name}_impl,
        {{
            "description": "{description}",
            "parameters": {{}},
            "return_type": "Any"
        }}
    )

def {tool_name}_impl(*args, **kwargs):
    """{description}"""
{implementation}
'''
        return code
    
    @staticmethod
    def generate_extension_pack(pack_name: str, tools: List[Dict[str, str]]) -> str:
        """複数ツールを含む拡張パックを生成"""
        pack_code = f'''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Extension Pack: {pack_name}
Auto-generated tool collection
"""

def register_tools(registry):
    """All tools in this pack"""
'''
        
        for tool in tools:
            tool_name = tool.get('name', 'tool')
            description = tool.get('description', '')
            pack_code += f'''
    registry.register_tool(
        "{tool_name}",
        {tool_name}_impl,
        {{
            "description": "{description}",
            "parameters": {{}},
            "return_type": "Any"
        }}
    )
'''
        
        for tool in tools:
            tool_name = tool.get('name', 'tool')
            implementation = tool.get('implementation', 'return "Not implemented"')
            pack_code += f'''

def {tool_name}_impl(*args, **kwargs):
    """{tool.get('description', '')}"""
    {implementation}
'''
        
        return pack_code


class ToolManager:
    """統合ツールマネージャー"""
    
    def __init__(self, tools_dir: Path):
        self.extension_manager = ExtensionManager(tools_dir)
        self.code_generator = DynamicCodeGenerator()
    
    def create_and_load_tool(self, tool_name: str, description: str, implementation: str) -> bool:
        """ツールを生成して読み込み"""
        try:
            # コード生成
            code = self.code_generator.generate_tool_code(
                tool_name,
                description,
                implementation
            )
            
            # ファイルに保存
            tool_file = self.extension_manager.tools_dir / f"{tool_name}.py"
            with open(tool_file, 'w', encoding='utf-8') as f:
                f.write(code)
            
            # 読み込み
            return self.extension_manager.registry.load_custom_tool(tool_file)
        
        except Exception as e:
            print(f"Failed to create and load tool: {e}")
            return False
    
    def create_tool_pack(self, pack_name: str, tools: List[Dict[str, str]]) -> bool:
        """ツールパックを生成して読み込み"""
        try:
            # コード生成
            code = self.code_generator.generate_extension_pack(pack_name, tools)
            
            # ファイルに保存
            pack_file = self.extension_manager.tools_dir / f"{pack_name}_pack.py"
            with open(pack_file, 'w', encoding='utf-8') as f:
                f.write(code)
            
            # 読み込み
            return self.extension_manager.registry.load_custom_tool(pack_file)
        
        except Exception as e:
            print(f"Failed to create tool pack: {e}")
            return False
    
    def get_available_tools(self) -> Dict[str, Any]:
        """利用可能なツール一覧"""
        return self.extension_manager.list_available_tools()
    
    def call_tool(self, tool_name: str, *args, **kwargs) -> Any:
        """ツールを呼び出し"""
        tool = self.extension_manager.registry.get_tool(tool_name)
        if tool:
            return tool(*args, **kwargs)
        return None


# グローバルツールマネージャーインスタンス
_global_tool_manager = None

def get_tool_manager(tools_dir: Path = None) -> ToolManager:
    """グローバルツールマネージャーを取得"""
    global _global_tool_manager
    
    if _global_tool_manager is None:
        from tugumi_agent import TugumiConfig
        tools_dir = tools_dir or TugumiConfig.TOOLS_DIR
        _global_tool_manager = ToolManager(tools_dir)
    
    return _global_tool_manager
