"""
Blender Unified MCP Utilities
ユーティリティ関数とヘルパーを提供
"""

import bpy
import os
import sys
import json
import logging
import traceback
from typing import Dict, List, Any, Optional, Union, Callable, TypeVar, cast
import functools

# エラーハンドラーモジュールをインポート
try:
    from .error_handler import (
        format_error_response, format_success_response,
        handle_exceptions, log_and_handle_exceptions,
        configure_logging, DEBUG_MODE
    )
    ERROR_HANDLER_AVAILABLE = True
except ImportError:
    ERROR_HANDLER_AVAILABLE = False

# ロギング設定
def setup_logging():
    """ロギングのセットアップ"""
    log_file = os.path.expanduser("~/.blender_json_mcp.log")
    
    # ルートロガーの設定
    logger = logging.getLogger("blender_json_mcp")
    logger.setLevel(logging.INFO)
    
    # ハンドラが既に追加されていない場合のみ追加
    if not logger.handlers:
        # ファイルハンドラ
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.INFO)
        
        # フォーマッタ
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        
        # ハンドラをロガーに追加
        logger.addHandler(file_handler)
    
    return logger

# グローバルロガーの初期化
logger = setup_logging()

# 簡略化されたログ関数
def log_info(message: str, *args, **kwargs):
    """情報メッセージをログに記録する"""
    logger.info(message, *args, **kwargs)
    # デバッグモードだけ出力
    if ERROR_HANDLER_AVAILABLE and DEBUG_MODE:
        print(f"[INFO] {message}")

def log_warning(message: str, *args, **kwargs):
    """警告メッセージをログに記録する"""
    logger.warning(message, *args, **kwargs)
    print(f"[WARNING] {message}")

def log_error(message: str, *args, **kwargs):
    """エラーメッセージをログに記録する"""
    logger.error(message, *args, **kwargs)
    print(f"[ERROR] {message}")
    if ERROR_HANDLER_AVAILABLE and DEBUG_MODE:
        traceback.print_exc()

# ユーティリティ関数
def safe_execute_code(code_string: str) -> Dict[str, Any]:
    """
    安全にPythonコードを実行する

    Args:
        code_string: 実行するコード文字列

    Returns:
        実行結果とステータスを含む辞書
    """
    import io
    from contextlib import redirect_stdout, redirect_stderr

    # 成功/失敗フラグ
    success = False
    # 出力をキャプチャ
    stdout = io.StringIO()
    stderr = io.StringIO()
    # 結果オブジェクト
    result = None
    # エラーメッセージ
    error_msg = ""

    try:
        # 安全なスクリプト実行ユーティリティを利用
        try:
            # まずcore/utilsからのインポートを試みる
            try:
                from ..core.utils.safe_script_executor import SafeScriptExecutor
                SAFE_EXECUTOR_AVAILABLE = True
            except ImportError:
                # 相対パスが異なる場合があるため、絶対パスも試みる
                module_path = os.path.join(os.path.dirname(os.path.dirname(__file__)),
                                         'core', 'utils', 'safe_script_executor.py')
                if os.path.exists(module_path):
                    # 動的インポート
                    import importlib.util
                    spec = importlib.util.spec_from_file_location("safe_script_executor", module_path)
                    safe_script_executor = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(safe_script_executor)
                    SafeScriptExecutor = safe_script_executor.SafeScriptExecutor
                    SAFE_EXECUTOR_AVAILABLE = True
                else:
                    SAFE_EXECUTOR_AVAILABLE = False

            # 安全な実行機能が利用可能な場合
            if SAFE_EXECUTOR_AVAILABLE:
                # 出力をキャプチャするための設定
                with redirect_stdout(stdout), redirect_stderr(stderr):
                    # 安全なスクリプト実行
                    executor = SafeScriptExecutor()
                    safe_result = executor.execute_script(code_string, "<utils>")

                    # 実行結果を処理
                    success = safe_result.get("success", False)
                    result = safe_result.get("result", None)
                    if not success:
                        error_msg = safe_result.get("error", "Unknown error")
                        details = safe_result.get("details", {})
                        if details and "traceback" in details:
                            print(details["traceback"], file=stderr)
            else:
                # フォールバックの実装（警告を出す）
                log_warning("安全なスクリプト実行機能が利用できません。利用できません。")
                error_msg = "Safe script execution is not available"
                success = False
                return {
                    'success': success,
                    'stdout': stdout.getvalue(),
                    'stderr': stderr.getvalue(),
                    'result': None,
                    'error': error_msg
                }

        except Exception as e:
            # スクリプト実行モジュールのインポートエラー
            error_msg = f"安全なスクリプト実行機能のロードエラー: {str(e)}"
            log_error(error_msg)
            success = False
            print(error_msg, file=stderr)
            print(traceback.format_exc(), file=stderr)

    except Exception as e:
        error_msg = f"{type(e).__name__}: {str(e)}"
        log_error(f"コード実行エラー: {error_msg}")
        traceback.print_exc()
        print(traceback.format_exc(), file=stderr)

    # 戻り値の作成
    return {
        'success': success,
        'stdout': stdout.getvalue(),
        'stderr': stderr.getvalue(),
        'result': result,
        'error': error_msg
    }

def get_object_info(obj_name: str) -> Optional[Dict[str, Any]]:
    """
    指定されたオブジェクトの詳細情報を取得
    (共通モジュールのget_object_dataに置き換えられました)
    
    Args:
        obj: Blenderオブジェクト
        
    Returns:
        オブジェクト情報を含む辞書
    """
    if COMMON_UTILS_AVAILABLE:
        return get_object_data(obj)
    
    # 共通モジュールが利用できない場合のフォールバック
    info = {
        'name': obj.name,
        'type': obj.type,
        'location': {
            'x': obj.location.x,
            'y': obj.location.y,
            'z': obj.location.z
        },
        'rotation': {
            'x': obj.rotation_euler.x,
            'y': obj.rotation_euler.y,
            'z': obj.rotation_euler.z
        },
        'scale': {
            'x': obj.scale.x,
            'y': obj.scale.y,
            'z': obj.scale.z
        },
        'dimensions': {
            'x': obj.dimensions.x,
            'y': obj.dimensions.y,
            'z': obj.dimensions.z
        },
        'visible': obj.visible_get(),
        'materials': [mat.material.name for mat in obj.material_slots if mat.material]
    }
    return info

def get_scene_summary() -> Dict[str, Any]:
    """
    現在のシーンの要約情報を取得
    (共通モジュールのget_scene_infoに置き換えられました)
    
    Returns:
        シーン情報を含む辞書
    """
    if COMMON_UTILS_AVAILABLE:
        base_info = get_scene_info()
        # 拡張情報を追加
        scene = bpy.context.scene
        object_counts = {}
        for obj in scene.objects:
            obj_type = obj.type
            if obj_type not in object_counts:
                object_counts[obj_type] = 0
            object_counts[obj_type] += 1

        # 基本情報を拡張
        base_info.update({
            'fps': scene.render.fps,
            'objects_total': len(scene.objects),
            'object_counts': object_counts,
            'render_engine': scene.render.engine,
            'use_nodes': scene.use_nodes
        })
        return base_info
    
    # 共通モジュールが利用できない場合のフォールバック
    scene = bpy.context.scene
    
    # オブジェクト数をタイプ別に集計
    object_counts = {}
    for obj in scene.objects:
        obj_type = obj.type
        if obj_type not in object_counts:
            object_counts[obj_type] = 0
        object_counts[obj_type] += 1
    
    # 選択オブジェクト
    selected_objects = [obj.name for obj in bpy.context.selected_objects]
    
    # アクティブオブジェクト
    active_object = bpy.context.active_object.name if bpy.context.active_object else None
    
    # シーン情報
    return {
        'name': scene.name,
        'frame_current': scene.frame_current,
        'frame_start': scene.frame_start,
        'frame_end': scene.frame_end,
        'fps': scene.render.fps,
        'objects_total': len(scene.objects),
        'object_counts': object_counts,
        'selected_objects': selected_objects,
        'active_object': active_object,
        'render_engine': scene.render.engine,
        'use_nodes': scene.use_nodes
    }

# モジュール登録関数
# エラーハンドラーモジュールをインポート
try:
    from . import error_handler
    ERROR_HANDLER_AVAILABLE = True
    log_info("エラーハンドラーモジュールを読み込みました")
except ImportError as e:
    ERROR_HANDLER_AVAILABLE = False
    log_warning(f"エラーハンドラーモジュールの読み込みに失敗しました: {e}")

# 高度なユーティリティモジュールをインポート
try:
    from . import advanced
    ADVANCED_UTILS_AVAILABLE = True
    log_info("高度なユーティリティ機能が利用可能です")
except ImportError as e:
    ADVANCED_UTILS_AVAILABLE = False
    log_warning(f"高度なユーティリティモジュールが読み込めません: {e}")

# 初期化モジュールをインポート
try:
    from . import initialize_utils
    INITIALIZE_UTILS_AVAILABLE = True
    log_info("ユーティリティ初期化モジュールが利用可能です")
except ImportError as e:
    INITIALIZE_UTILS_AVAILABLE = False
    log_warning(f"ユーティリティ初期化モジュールが読み込めません: {e}")

# ファイルユーティリティモジュールをインポート
try:
    from . import fileutils
    FILE_UTILS_AVAILABLE = True
    log_info("ファイルユーティリティモジュールを読み込みました")
except ImportError as e:
    FILE_UTILS_AVAILABLE = False
    log_warning(f"ファイルユーティリティモジュールの読み込みに失敗しました: {e}")

# UIエラーハンドラーモジュールをインポート
try:
    from . import ui_error_handler
    UI_ERROR_HANDLER_AVAILABLE = True
    log_info("UIエラーハンドラーモジュールを読み込みました")
except ImportError as e:
    UI_ERROR_HANDLER_AVAILABLE = False
    log_warning(f"UIエラーハンドラーモジュールの読み込みに失敗しました: {e}")

# 非同期ファイル操作モジュールをインポート
try:
    from . import async_file_handler
    ASYNC_FILE_HANDLER_AVAILABLE = True
    log_info("非同期ファイル操作モジュールを読み込みました")
except ImportError as e:
    ASYNC_FILE_HANDLER_AVAILABLE = False
    log_warning(f"非同期ファイル操作モジュールの読み込みに失敗しました: {e}")

# グローバルに公開する高度な機能
if ADVANCED_UTILS_AVAILABLE:
    # パフォーマンス追跡
    # パフォーマンスモジュールを直接利用
    try:
        from .performance import track_time as track_performance
        from .performance import time_operation as timed_operation
        from .performance import print_stats, get_stats, enable_tracking, disable_tracking, reset_stats
        log_info("パフォーマンスモジュールを直接インポートしました")
    except ImportError as e:
        # 旧式の実装
        track_performance = advanced.track_performance
        timed_operation = advanced.timed_operation
        log_warning(f"パフォーマンスモジュールの読み込みに失敗しました: {e}")
    
    # エラーハンドリング
    error_handling = advanced.error_handling
    
    # キャッシュ
    cached = advanced.cached
    clear_all_caches = advanced.clear_all_caches
    
    # ファイル操作
    safe_read_json = advanced.safe_read_json
    safe_write_json = advanced.safe_write_json
    
    # 幾何学ユーティリティ
    calculate_distance = advanced.calculate_distance
    calculate_object_center = advanced.calculate_object_center
    align_objects = advanced.align_objects
    
    # シーン分析
    analyze_scene_complexity = advanced.analyze_scene_complexity

def register():
    """ユーティリティモジュールを登録"""
    log_info("ユーティリティモジュールを登録中")
    
    # エラーハンドラーを登録
    if ERROR_HANDLER_AVAILABLE:
        try:
            error_handler.register()
        except Exception as e:
            log_error(f"エラーハンドラーモジュールの登録に失敗: {e}")
    
    # 高度なユーティリティの登録
    if ADVANCED_UTILS_AVAILABLE:
        try:
            advanced.register()
        except Exception as e:
            log_error(f"高度なユーティリティモジュールの登録に失敗: {e}")
    
    # ファイルユーティリティを登録
    if FILE_UTILS_AVAILABLE:
        try:
            fileutils.register()
        except Exception as e:
            log_error(f"ファイルユーティリティモジュールの登録に失敗: {e}")
    
    # UIエラーハンドラーを登録
    if UI_ERROR_HANDLER_AVAILABLE:
        try:
            ui_error_handler.register()
        except Exception as e:
            log_error(f"UIエラーハンドラーモジュールの登録に失敗: {e}")
    
    # 非同期ファイルハンドラーを登録
    if ASYNC_FILE_HANDLER_AVAILABLE:
        try:
            async_file_handler.register()
        except Exception as e:
            log_error(f"非同期ファイルハンドラーモジュールの登録に失敗: {e}")

def unregister():
    """ユーティリティモジュールの登録解除"""
    log_info("ユーティリティモジュールを登録解除中")
    
    # 逆順で登録解除
    
    # 非同期ファイルハンドラーの登録解除
    if ASYNC_FILE_HANDLER_AVAILABLE:
        try:
            async_file_handler.unregister()
        except Exception as e:
            log_error(f"非同期ファイルハンドラーモジュールの登録解除に失敗: {e}")
    
    # UIエラーハンドラーの登録解除
    if UI_ERROR_HANDLER_AVAILABLE:
        try:
            ui_error_handler.unregister()
        except Exception as e:
            log_error(f"UIエラーハンドラーモジュールの登録解除に失敗: {e}")
    
    # ファイルユーティリティの登録解除
    if FILE_UTILS_AVAILABLE:
        try:
            fileutils.unregister()
        except Exception as e:
            log_error(f"ファイルユーティリティモジュールの登録解除に失敗: {e}")
    
    # 高度なユーティリティの登録解除
    if ADVANCED_UTILS_AVAILABLE:
        try:
            advanced.unregister()
        except Exception as e:
            log_error(f"高度なユーティリティモジュールの登録解除に失敗: {e}")
    
    # エラーハンドラーの登録解除
    if ERROR_HANDLER_AVAILABLE:
        try:
            error_handler.unregister()
        except Exception as e:
            log_error(f"エラーハンドラーモジュールの登録解除に失敗: {e}")
