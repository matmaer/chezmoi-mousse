"""Test all classes to ensure that all methods are being accessed at least once,
either inside the class if it starts with an underscore, outside the class if it does
not.
"""

import ast
from typing import NamedTuple

import pytest
from _test_utils import (
    ModuleData,
    get_all_module_data,
    get_module_ast_class_defs,
    get_module_paths,
)

type AstClassDefs = list[ast.ClassDef]

MODULE_PATHS = get_module_paths()


class TestResults(NamedTuple):
    module_path: str  # the module path for error reporting
    class_name: str  # the ast.ClassDef.name containing an unused method
    method_name: str  # the ast.FunctionDef.name of the method not in use
    method_lineno: int  # line number where the method is defined
    should_be_private: bool


class MethodData(NamedTuple):
    name: str
    lineno: int


class ClassData(NamedTuple):
    module_path: str  # the module path for error reporting
    class_name: str  # the ast.ClassDef.name
    class_lineno: int  # line number where the class is defined
    class_nodes: list[ast.AST]  # the ast nodes within the class (materialized)
    methods: list[MethodData]  # all methods defined on class (excluding dunders)


def _get_decorator_name(decorator: ast.expr) -> str | None:
    if isinstance(decorator, ast.Name):
        return decorator.id
    if isinstance(decorator, ast.Attribute):
        return decorator.attr
    if isinstance(decorator, ast.Call):
        return _get_decorator_name(decorator.func)
    return None


def _is_property(node: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    return any(
        _get_decorator_name(decorator) == "property"
        for decorator in node.decorator_list
    )


def _has_on_decorator(node: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    return any(
        _get_decorator_name(decorator) == "on" for decorator in node.decorator_list
    )


module_data_list: list[ModuleData] = get_all_module_data()

all_class_data: list[ClassData] = []
for file_path in MODULE_PATHS:
    class_defs: AstClassDefs = get_module_ast_class_defs(file_path)
    for class_def in class_defs:
        if class_def.name == "DebugLog":
            continue
        methods: list[MethodData] = []
        for item in class_def.body:
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if _has_on_decorator(item) or _is_property(item):
                    continue
                # dunders to exclude
                if item.name in ("__init__", "__post_init__"):
                    continue
                # textual naming convention and method overrides
                if item.name.startswith(("action_", "on_", "watch_")) or item.name in (
                    "check_action",
                    "compose",
                    "describe_failure",
                    "filter_paths",
                    "filter_paths",
                    "render_bar",
                    "render_line",
                    "render_lines",
                    "validate",
                ):
                    continue
                # debug and methods and overrides in application code
                if item.name in ("notify_not_implemented", "_on_field_change"):
                    continue
                methods.append(MethodData(name=item.name, lineno=item.lineno))
        if methods:
            all_class_data.append(
                ClassData(
                    module_path=str(file_path),
                    class_name=class_def.name,
                    class_lineno=class_def.lineno,
                    class_nodes=list(ast.walk(class_def)),
                    methods=methods,
                )
            )


@pytest.mark.parametrize(
    "class_data",
    all_class_data,
    ids=lambda x: f"{x.class_name} ({x.module_path}:{x.class_lineno})",
)
def test_methods_in_use(class_data: ClassData) -> None:
    results: list[TestResults] = []
    class_node_set = set(class_data.class_nodes)

    for method in class_data.methods:
        if method.name.startswith("_"):
            in_use = False
            for node in class_data.class_nodes:
                if (
                    isinstance(node, ast.Attribute)
                    and node.attr == method.name
                    and isinstance(node.ctx, ast.Load)
                ):
                    in_use = True
                    break
            if not in_use:
                results.append(
                    TestResults(
                        module_path=class_data.module_path,
                        class_name=class_data.class_name,
                        method_name=method.name,
                        method_lineno=method.lineno,
                        should_be_private=False,
                    )
                )
        else:
            in_use_in_class = False
            for node in class_data.class_nodes:
                if (
                    isinstance(node, ast.Attribute)
                    and node.attr == method.name
                    and isinstance(node.ctx, ast.Load)
                ):
                    in_use_in_class = True
                    break
            in_use = False
            for module_data in module_data_list:
                if in_use:
                    break
                for node in module_data.module_nodes:
                    if isinstance(node, ast.Attribute) and node.attr == method.name:
                        if node in class_node_set:
                            continue
                        if isinstance(node.ctx, ast.Load):
                            in_use = True
                            break
            if not in_use:
                results.append(
                    TestResults(
                        module_path=class_data.module_path,
                        class_name=class_data.class_name,
                        method_name=method.name,
                        method_lineno=method.lineno,
                        should_be_private=in_use_in_class,
                    )
                )

    if results:
        pytest.fail(
            "\n"
            + "\n".join(
                (
                    (
                        f"{result.class_name}.{result.method_name} in "
                        f"{result.module_path}:{result.method_lineno}"
                    )
                    + " (should be private)"
                    if result.should_be_private
                    else ""
                )
                for result in results
            )
        )
