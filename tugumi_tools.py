#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TUGUMI Tools Extension Module
動的にツール・ライブラリを拡張できるモジュール

改善内容：
- 完全なエラーハンドリング
- ファイルI/O安全化
- tugumi_agentとの完全互換性
"""

import os
import sys
import json
import importlib.util
import traceback
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional


class ToolRegistry:
    """ツール登録システム"""
    
    def __init__(self, tools_dir: Path):
        try:
            self.tools_dir = Path(tools_dir)
            self.tools_dir.mkdir(parents=True, exist_ok=True)
            self.registered_tools: Dict[str, Callable] = {}
            self.tool_metadata: Dict[str, Dict[str, Any]] = {}
        except Exception as e:
            print(f"Error initializing ToolRegistry: {e}")
            raise
    
    def register_tool(self, name: str, func: Callable, metadata: Dict[str, Any] = None):
        """ツールを登録"""
        try:
            self.registered_tools[name] = func
            self.tool_metadata[name] = metadata or {
                "description": f"Tool: {name}",
                "parameters": {},
                "return_type": "Any"
            }
        except Exception as e:
            print(f"Error registering tool {name}: {e}")
    
    def get_tool(self, name: str) -> Optional[Callable]:
        """ツールを取得"""
        try:
            return self.registered_tools.get(name)
        except Exception as e:
            print(f"Error getting tool {name}: {e}")
            return None
    
    def list_tools(self) -> List[str]:
        """登録されているツール一覧"""
        try:
            return list(self.registered_tools.keys())
        except Exception as e:
            print(f"Error listing tools: {e}")
            return []
    
    def get_tool_info(self, name: str) -> Dict[str, Any]:
        """ツール情報を取得"""
        try:
            return self.tool_metadata.get(name, {})
        except Exception as e:
            print(f"Error getting tool info for {name}: {e}")
            return {}
    
    def load_custom_tool(self, tool_file: Path) -> bool:
        """カスタムツールを動的に読み込み"""
        try:
            if not tool_file.exists():
                print(f"Tool file not found: {tool_file}")
                return False
            
            spec = importlib.util.spec_from_file_location("custom_tool", tool_file)
            if spec is None or spec.loader is None:
                print(f"Could not load spec from {tool_file}")
                return False
            
            module = importlib.util.module_from_spec(spec)
            if module is None:
                print(f"Could not create module from spec for {tool_file}")
                return False
            
            spec.loader.exec_module(module)
            
            # ツール関数を登録
            if hasattr(module, 'register_tools'):
                module.register_tools(self)
                return True
            
            return False
        
        except Exception as e:
            print(f"Failed to load custom tool from {tool_file}: {e}")
            traceback.print_exc()
            return False


class ExtensionManager:
    """拡張マネージャー"""
    
    def __init__(self, tools_dir: Path):
        try:
            self.tools_dir = Path(tools_dir)
            self.registry = ToolRegistry(self.tools_dir)
            self._load_builtin_tools()
        except Exception as e:
            print(f"Error initializing ExtensionManager: {e}")
            raise
    
    def _load_builtin_tools(self):
        """組み込みツールを読み込み"""
        try:
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
        except Exception as e:
            print(f"Error loading builtin tools: {e}")
    
    def execute_python_code(self, code: str) -> str:
        """Pythonコードを実行"""
        try:
            exec_globals = {}
            exec(code, exec_globals)
            return "Code executed successfully"
        except SyntaxError as e:
            return f"Syntax error: {str(e)}"
        except Exception as e:
            return f"Error executing code: {str(e)}"
    
    def install_pip_package(self, package_name: str) -> bool:
        """pipパッケージをインストール"""
        try:
            import subprocess
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", package_name],
                check=True,
                capture_output=True,
                timeout=120
            )
            return True
        except subprocess.TimeoutExpired:
            print(f"Installation timeout for {package_name}")
            return False
        except subprocess.CalledProcessError as e:
            print(f"Installation failed for {package_name}: {e}")
            return False
        except Exception as e:
            print(f"Error installing package: {e}")
            return False
    
    def import_module(self, module_name: str):
        """モジュールを動的にインポート"""
        try:
            return __import__(module_name)
        except ImportError as e:
            print(f"Failed to import {module_name}: {e}")
            return None
        except Exception as e:
            print(f"Error importing {module_name}: {e}")
            return None
    
    def create_custom_tool_template(self, tool_name: str) -> Path:
        """カスタムツールのテンプレートを作成"""
        try:
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
    try:
        result = args[0] if args else "No input"
        return f"Tool {tool_name} executed with: {{result}}"
    except Exception as e:
        return f"Error in {tool_name}: {{str(e)}}"
'''
            
            tool_file = self.tools_dir / f"{tool_name}.py"
            with open(tool_file, 'w', encoding='utf-8') as f:
                f.write(template_code)
            
            return tool_file
        except Exception as e:
            print(f"Error creating tool template: {e}")
            raise
    
    def list_available_tools(self) -> Dict[str, Any]:
        """利用可能なツール一覧"""
        try:
            tools = {}
            for tool_name in self.registry.list_tools():
                tools[tool_name] = self.registry.get_tool_info(tool_name)
            return tools
        except Exception as e:
            print(f"Error listing available tools: {e}")
            return {}


class DynamicCodeGenerator:
    """動的コード生成器"""
    
    @staticmethod
    def generate_tool_code(tool_name: str, description: str, implementation: str) -> str:
        """ツールコードを生成"""
        try:
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
    try:
{implementation}
    except Exception as e:
        return f"Error in {tool_name}: {{str(e)}}"
'''
            return code
        except Exception as e:
            print(f"Error generating tool code: {e}")
            return ""
    
    @staticmethod
    def generate_extension_pack(pack_name: str, tools: List[Dict[str, str]]) -> str:
        """複数ツールを含む拡張パックを生成"""
        try:
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
    try:
{implementation}
    except Exception as e:
        return f"Error in {tool_name}: {{str(e)}}"
'''
            
            return pack_code
        except Exception as e:
            print(f"Error generating extension pack: {e}")
            return ""


class ToolManager:
    """統合ツールマネージャー"""
    
    def __init__(self, tools_dir: Path):
        try:
            self.extension_manager = ExtensionManager(tools_dir)
            self.code_generator = DynamicCodeGenerator()
        except Exception as e:
            print(f"Error initializing ToolManager: {e}")
            raise
    
    def create_and_load_tool(self, tool_name: str, description: str, implementation: str) -> bool:
        """ツールを生成して読み込み"""
        try:
            # コード生成
            code = self.code_generator.generate_tool_code(
                tool_name,
                description,
                implementation
            )
            
            if not code:
                return False
            
            # ファイルに保存
            tool_file = self.extension_manager.tools_dir / f"{tool_name}.py"
            with open(tool_file, 'w', encoding='utf-8') as f:
                f.write(code)
            
            # 読み込み
            return self.extension_manager.registry.load_custom_tool(tool_file)
        
        except Exception as e:
            print(f"Failed to create and load tool: {e}")
            traceback.print_exc()
            return False
    
    def create_tool_pack(self, pack_name: str, tools: List[Dict[str, str]]) -> bool:
        """ツールパックを生成して読み込み"""
        try:
            # コード生成
            code = self.code_generator.generate_extension_pack(pack_name, tools)
            
            if not code:
                return False
            
            # ファイルに保存
            pack_file = self.extension_manager.tools_dir / f"{pack_name}_pack.py"
            with open(pack_file, 'w', encoding='utf-8') as f:
                f.write(code)
            
            # 読み込み
            return self.extension_manager.registry.load_custom_tool(pack_file)
        
        except Exception as e:
            print(f"Failed to create tool pack: {e}")
            traceback.print_exc()
            return False
    
    def get_available_tools(self) -> Dict[str, Any]:
        """利用可能なツール一覧"""
        try:
            return self.extension_manager.list_available_tools()
        except Exception as e:
            print(f"Error getting available tools: {e}")
            return {}
    
    def call_tool(self, tool_name: str, *args, **kwargs) -> Any:
        """ツールを呼び出し"""
        try:
            tool = self.extension_manager.registry.get_tool(tool_name)
            if tool:
                return tool(*args, **kwargs)
            else:
                return f"Tool '{tool_name}' not found"
        except Exception as e:
            print(f"Error calling tool {tool_name}: {e}")
            traceback.print_exc()
            return f"Error: {str(e)}"


# グローバルツールマネージャーインスタンス
_global_tool_manager = None

def get_tool_manager(tools_dir: Path = None) -> ToolManager:
    """グローバルツールマネージャーを取得"""
    global _global_tool_manager
    
    try:
        if _global_tool_manager is None:
            try:
                from tugumi_agent import TugumiConfig
                tools_dir = tools_dir or TugumiConfig.TOOLS_DIR
            except ImportError:
                # tugumi_agentが利用できない場合
                if tools_dir is None:
                    tools_dir = Path.home() / "Documents" / "TUGUMI_TOOLS"
            
            _global_tool_manager = ToolManager(tools_dir)
        
        return _global_tool_manager
    
    except Exception as e:
        print(f"Error getting tool manager: {e}")
        traceback.print_exc()
        raise
