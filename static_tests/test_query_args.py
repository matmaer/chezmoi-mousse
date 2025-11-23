import ast
from typing import NamedTuple

import pytest
from _test_utils import get_module_ast_class_defs, get_module_paths

type AstClassDefs = list[ast.ClassDef]

MODULE_PATHS = get_module_paths()


class ClassData(NamedTuple):
    # tuple to avoid a flat with possible duplicate nodes
    module_path: str  # the module path for error reporting
    class_name: str  # the ast.ClassDef.name
    query_one_nodes: list[ast.Call]  # the ast.Call nodes calling query_one


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
                    module_path=str(file_path.name),
                    class_name=class_def.name,
                    query_one_nodes=query_one_nodes,
                )
            )


@pytest.mark.parametrize(
    "class_data",
    CLASSES_WITH_THEIR_QUERY_ONE_NODES,
    ids=lambda x: f"{x.class_name} in {x.module_path}",
)
def test_query_one_calls(class_data: ClassData) -> None:
    results: list[str] = []
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
        if isinstance(first_arg, ast.Name):
            # Variable/class name like my_var
            first_arg_str = first_arg.id
        elif isinstance(first_arg, ast.Attribute):
            # Attribute like ids.container.pre_operate
            first_arg_str = first_arg.attr
        else:
            pytest.skip(
                f"Cannot determine first argument type in "
                f"{class_data.module_path}, class '{class_data.class_name}'."
            )
        if not first_arg_str.endswith("_q"):
            results.append(
                f"{class_data.module_path}, "
                f"class '{class_data.class_name}', "
                f"'{first_arg_str}' not ending with '_q'."
            )
    if results:
        pytest.fail("\n".join(results))
