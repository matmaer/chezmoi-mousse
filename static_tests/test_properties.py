"""Test all classes to ensure that all properties are being accessed at least once,
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
    class_name: str  # the ast.ClassDef.name containing an unused property
    property_name: str  # the ast.FunctionDef.name of the property not in use
    property_lineno: int  # line number where the property is defined
    should_be_private: bool


class PropertyData(NamedTuple):
    name: str
    lineno: int


class ClassData(NamedTuple):
    module_path: str  # the module path for error reporting
    class_name: str  # the ast.ClassDef.name
    class_lineno: int  # line number where the class is defined
    class_nodes: list[ast.AST]  # the ast nodes within the class (materialized)
    properties: list[PropertyData]  # all @property functions defined on class


def _get_decorator_name(decorator: ast.expr) -> str | None:
    if isinstance(decorator, ast.Name):
        return decorator.id
    if isinstance(decorator, ast.Attribute):
        return decorator.attr
    if isinstance(decorator, ast.Call):
        return _get_decorator_name(decorator.func)
    return None


module_data_list: list[ModuleData] = get_all_module_data()

all_class_data: list[ClassData] = []
for file_path in MODULE_PATHS:
    class_defs: AstClassDefs = get_module_ast_class_defs(file_path)
    for class_def in class_defs:
        properties: list[PropertyData] = []
        for item in class_def.body:
            if isinstance(item, ast.FunctionDef):
                if any(
                    _get_decorator_name(decorator) == "property"
                    for decorator in item.decorator_list
                ):
                    properties.append(PropertyData(name=item.name, lineno=item.lineno))
        if properties:
            all_class_data.append(
                ClassData(
                    module_path=str(file_path),
                    class_name=class_def.name,
                    class_lineno=class_def.lineno,
                    class_nodes=list(ast.walk(class_def)),
                    properties=properties,
                )
            )


@pytest.mark.parametrize(
    "class_data",
    all_class_data,
    ids=lambda x: f"{x.class_name} ({x.module_path}:{x.class_lineno})",
)
def test_properties_in_use(class_data: ClassData) -> None:
    results: list[TestResults] = []
    class_node_set = set(class_data.class_nodes)

    for prop in class_data.properties:
        if prop.name.startswith("_"):
            in_use = False
            for node in class_data.class_nodes:
                if (
                    isinstance(node, ast.Attribute)
                    and node.attr == prop.name
                    and isinstance(node.ctx, ast.Load)
                ):
                    in_use = True
                    break
            if not in_use:
                results.append(
                    TestResults(
                        module_path=class_data.module_path,
                        class_name=class_data.class_name,
                        property_name=prop.name,
                        property_lineno=prop.lineno,
                        should_be_private=False,
                    )
                )
        else:
            in_use_in_class = False
            for node in class_data.class_nodes:
                if (
                    isinstance(node, ast.Attribute)
                    and node.attr == prop.name
                    and isinstance(node.ctx, ast.Load)
                ):
                    in_use_in_class = True
                    break
            in_use = False
            for module_data in module_data_list:
                if in_use:
                    break
                for node in module_data.module_nodes:
                    if isinstance(node, ast.Attribute) and node.attr == prop.name:
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
                        property_name=prop.name,
                        property_lineno=prop.lineno,
                        should_be_private=in_use_in_class,
                    )
                )

    if results:
        pytest.fail(
            "\n"
            + "\n".join(
                f"{result.class_name}.{result.property_name} "
                f"(in {result.module_path}:{result.property_lineno})"
                + (" (should be private)" if result.should_be_private else "")
                for result in results
            )
        )
