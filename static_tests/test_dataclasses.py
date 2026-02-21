import ast
from typing import NamedTuple

import pytest
from _test_utils import get_module_ast_class_defs, get_module_ast_tree, get_module_paths

MODULE_PATHS = get_module_paths()

type AstClassDefs = list[ast.ClassDef]


def is_dataclass_class(class_def: ast.ClassDef) -> bool:
    def get_decorator_name(decorator: ast.expr) -> str | None:
        if isinstance(decorator, ast.Name):
            return decorator.id
        elif isinstance(decorator, ast.Attribute):
            return decorator.attr
        elif isinstance(decorator, ast.Call):
            return get_decorator_name(decorator.func)
        return None

    for decorator in class_def.decorator_list:
        if get_decorator_name(decorator) == "dataclass":
            return True
    return False


class ModuleData(NamedTuple):
    module_path: str  # the module path for error reporting
    module_nodes: list[ast.AST]  # all ast nodes in the module (materialized)


class ClassData(NamedTuple):
    module_path: str  # the module path for error reporting
    class_name: str  # the ast.ClassDef.name
    class_lineno: int  # line number where the class is defined
    class_nodes: list[ast.AST]  # the ast nodes within the class (materialized)
    fields: list[str]  # the field names of the dataclass


all_dataclass_classes: list[ClassData] = []
module_data_list: list[ModuleData] = []

for file_path in MODULE_PATHS:
    # Store module-level nodes
    module_tree = get_module_ast_tree(file_path)
    module_data_list.append(
        ModuleData(module_path=str(file_path), module_nodes=list(ast.walk(module_tree)))
    )
    class_defs: AstClassDefs = get_module_ast_class_defs(file_path)
    for class_def in class_defs:
        fields: list[str] = []
        for stmt in class_def.body:
            if isinstance(stmt, ast.AnnAssign):
                if isinstance(stmt.target, ast.Name):
                    fields.append(stmt.target.id)
            elif isinstance(stmt, ast.Assign):
                for target in stmt.targets:
                    if isinstance(target, ast.Attribute):
                        if (
                            isinstance(target.value, ast.Name)
                            and target.value.id == "self"
                        ):
                            fields.append(target.attr)
        to_append = ClassData(
            module_path=str(file_path),
            class_name=class_def.name,
            class_lineno=class_def.lineno,
            class_nodes=list(ast.walk(class_def)),
            fields=fields,
        )
        if is_dataclass_class(class_def):
            all_dataclass_classes.append(to_append)


all_dataclass_nodes: set[ast.AST] = set()
for cd in all_dataclass_classes:
    all_dataclass_nodes.update(cd.class_nodes)


@pytest.mark.parametrize(
    "class_data",
    all_dataclass_classes,
    ids=lambda x: f"{x.class_name} ({x.module_path}:{x.class_lineno})",
)
def test_fields_in_use(class_data: ClassData) -> None:
    # Use the pre-collected fields
    dataclass_field_names = class_data.fields

    results: list[str] = []
    for field_name in dataclass_field_names:
        if field_name.startswith("_"):
            continue
        in_use = False
        for module_data in module_data_list:
            if in_use:
                break
            for node in module_data.module_nodes:
                if isinstance(node, ast.Attribute):
                    if node.attr == field_name and isinstance(node.ctx, ast.Load):
                        in_use = True
                        break
        if not in_use:
            results.append(field_name)

    if results:
        pytest.fail(
            f"Dataclass {class_data.class_name} in {class_data.module_path}:{class_data.class_lineno} has unused fields: {', '.join(results)}"
        )
