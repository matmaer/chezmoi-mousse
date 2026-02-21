import ast
from typing import NamedTuple

import pytest
from _test_utils import get_module_ast_class_defs, get_module_paths

type AstClassDefs = list[ast.ClassDef]

MODULE_PATHS = get_module_paths()


class ClassData(NamedTuple):
    module_path: str
    class_name: str
    class_lineno: int
    query_one_nodes: list[ast.Call]


CLASSES_WITH_THEIR_QUERY_ONE_NODES: list[ClassData] = []

for file_path in MODULE_PATHS:
    class_defs: AstClassDefs = get_module_ast_class_defs(file_path)
    for class_def in class_defs:
        query_one_nodes: list[ast.Call] = []
        # Collect classes calling query_one
        for node in ast.walk(class_def):
            if isinstance(node, ast.Call):
                # Check if the function being called is named 'query_one'
                if (
                    isinstance(node.func, ast.Attribute)
                    and node.func.attr == "query_one"
                ):
                    query_one_nodes.append(node)
        if query_one_nodes:
            CLASSES_WITH_THEIR_QUERY_ONE_NODES.append(
                ClassData(
                    module_path=str(file_path),
                    class_name=class_def.name,
                    class_lineno=class_def.lineno,
                    query_one_nodes=query_one_nodes,
                )
            )


@pytest.mark.parametrize(
    "class_data",
    CLASSES_WITH_THEIR_QUERY_ONE_NODES,
    ids=lambda x: f"{x.class_name} ({x.module_path}:{x.class_lineno})",
)
def test_query_one_calls(class_data: ClassData) -> None:
    issues: list[str] = []
    for call_node in class_data.query_one_nodes:
        # Check if first argument of the call ends with '_q'
        first_arg = call_node.args[0]
        first_arg_str: str = ""
        if isinstance(first_arg, ast.Constant):
            # String literal like "MyClass"
            if isinstance(first_arg.value, str):
                first_arg_str = first_arg.value
            else:
                first_arg_str = str(first_arg.value)
        elif isinstance(first_arg, ast.Name):
            # Variable/class name like my_var
            first_arg_str = first_arg.id
        elif isinstance(first_arg, ast.Attribute):
            # Attribute like ids.container.pre_operate
            first_arg_str = first_arg.attr
        else:
            issues.append(
                f"Cannot determine first argument type at line {call_node.lineno}."
            )
            continue
        if not first_arg_str.endswith("_q"):
            issues.append(
                f"'{first_arg_str}' not ending with '_q' at line {call_node.lineno}."
            )
    if issues:
        pytest.fail(
            f"Class {class_data.class_name} in {class_data.module_path}:{class_data.class_lineno} has query_one calls with issues:\n"
            + "\n".join(issues)
        )
