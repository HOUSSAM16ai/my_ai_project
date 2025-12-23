"""
Hyper-Unified Agent Tool Registry
=================================
The Facade that exposes all granular tools as a single unified interface.
Maintains 100% backward compatibility with the legacy monolith.

Ultra Structural-Aware Sovereign Edition ++
===========================================
"""

from .cognitive_tools import (
    generic_think,
    refine_text,
    summarize_text,
)
from .core import (
    canonicalize_tool_name,
    get_tool,
    get_tools_schema,
    has_tool,
    list_tools,
    resolve_tool_name,
)
from .definitions import (
    PROJECT_ROOT,
    ToolResult,
    __version__,
)
from .dispatch_tools import (
    dispatch_tool,
    introspect_tools,
)
from .fs_tools import (
    append_file,
    delete_file,
    ensure_directory,
    ensure_file,
    file_exists,
    list_dir,
    read_bulk_files,
    read_file,
    write_file,
    write_file_if_changed,
)
from .globals import (
    _ALIAS_INDEX,
    _CAPABILITIES,
    _LAYER_STATS,
    _TOOL_REGISTRY,
    _TOOL_STATS,
)
from .memory_tools import (
    memory_get,
    memory_put,
)
from .search_tools import (
    code_index_project,
    code_search_lexical,
    code_search_semantic,
)
from .structural_tools import (
    analyze_path_semantics,
    reload_deep_struct_map,
)


def get_registry():
    """
    Returns the tool registry.
    Added to support dependency injection in Overmind Factory.
    """
    # For now, we return a dict or object that represents the registry
    # In the future, this should return a ToolRegistryProtocol implementation
    return _TOOL_REGISTRY


# ======================================================================================
# Backwards Compatibility Function Aliases
# ======================================================================================
def generic_think_tool(**kwargs):
    return generic_think(**kwargs)


def summarize_text_tool(**kwargs):
    return summarize_text(**kwargs)


def refine_text_tool(**kwargs):
    return refine_text(**kwargs)


def write_file_tool(**kwargs):
    return write_file(**kwargs)


def write_file_if_changed_tool(**kwargs):
    return write_file_if_changed(**kwargs)


def append_file_tool(**kwargs):
    return append_file(**kwargs)


def read_file_tool(**kwargs):
    return read_file(**kwargs)


def file_exists_tool(**kwargs):
    return file_exists(**kwargs)


def list_dir_tool(**kwargs):
    return list_dir(**kwargs)


def delete_file_tool(**kwargs):
    return delete_file(**kwargs)


def ensure_file_tool(**kwargs):
    return ensure_file(**kwargs)


def ensure_directory_tool(**kwargs):
    return ensure_directory(**kwargs)


def introspect_tools_tool(**kwargs):
    return introspect_tools(**kwargs)


def memory_put_tool(**kwargs):
    return memory_put(**kwargs)


def memory_get_tool(**kwargs):
    return memory_get(**kwargs)


def dispatch_tool_tool(**kwargs):
    return dispatch_tool(**kwargs)


def analyze_path_semantics_tool(**kwargs):
    return analyze_path_semantics(**kwargs)


def reload_deep_struct_map_tool(**kwargs):
    return reload_deep_struct_map(**kwargs)


def read_bulk_files_tool(**kwargs):
    return read_bulk_files(**kwargs)


def code_index_project_tool(**kwargs):
    return code_index_project(**kwargs)


def code_search_lexical_tool(**kwargs):
    return code_search_lexical(**kwargs)


def code_search_semantic_tool(**kwargs):
    return code_search_semantic(**kwargs)


# ======================================================================================
# __all__
# ======================================================================================
__all__ = [
    "PROJECT_ROOT",
    "_ALIAS_INDEX",
    "_CAPABILITIES",
    "_LAYER_STATS",
    # Registries / Stats
    "_TOOL_REGISTRY",
    "_TOOL_STATS",
    "ToolResult",
    "__version__",
    "analyze_path_semantics",
    "analyze_path_semantics_tool",
    "append_file",
    "append_file_tool",
    "canonicalize_tool_name",
    "code_index_project",
    "code_index_project_tool",
    "code_search_lexical",
    "code_search_lexical_tool",
    "code_search_semantic",
    "code_search_semantic_tool",
    "delete_file",
    "delete_file_tool",
    "dispatch_tool",
    "dispatch_tool_tool",
    "ensure_directory",
    "ensure_directory_tool",
    "ensure_file",
    "ensure_file_tool",
    "file_exists",
    "file_exists_tool",
    "generic_think",
    # Legacy alias wrappers
    "generic_think_tool",
    "get_tool",
    "get_registry",
    "get_tools_schema",
    "has_tool",
    # Core Tools
    "introspect_tools",
    "introspect_tools_tool",
    "list_dir",
    "list_dir_tool",
    "list_tools",
    "memory_get",
    "memory_get_tool",
    "memory_put",
    "memory_put_tool",
    "read_bulk_files",
    "read_bulk_files_tool",
    "read_file",
    "read_file_tool",
    "refine_text",
    "refine_text_tool",
    "reload_deep_struct_map",
    "reload_deep_struct_map_tool",
    "resolve_tool_name",
    "summarize_text",
    "summarize_text_tool",
    "write_file",
    "write_file_if_changed",
    "write_file_if_changed_tool",
    "write_file_tool",
]
