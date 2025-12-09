import ast
from typing import NamedTuple

import pytest
from _test_utils import (
    get_module_ast_class_defs,
    get_module_ast_tree,
    get_module_paths,
)

type AstClassDefs = list[ast.ClassDef]

MODULE_PATHS = get_module_paths()

# Enums that are used dynamically so not is scope for static tests
EXCLUDE_ENUMS = {"PwMgrInfo", "UnwantedDirs", "UnwantedFileExtensions"}


def is_enum_class(class_def: ast.ClassDef) -> bool:
    for base in class_def.bases:
        if isinstance(base, ast.Name) and base.id in ("Enum", "StrEnum"):
            return True
    return False


class ModuleData(NamedTuple):
    module_path: str  # the module path for error reporting
    module_nodes: list[ast.AST]  # all ast nodes in the module (materialized)


class ClassData(NamedTuple):
    module_path: str  # the module path for error reporting
    class_name: str  # the ast.ClassDef.name
    class_nodes: list[ast.AST]  # the ast nodes within the class (materialized)


all_enum_classes: list[ClassData] = []
module_data_list: list[ModuleData] = []

for file_path in MODULE_PATHS:
    # Store module-level nodes
    module_tree = get_module_ast_tree(file_path)
    module_data_list.append(
        ModuleData(
            module_path=str(file_path),
            module_nodes=list(ast.walk(module_tree)),
        )
    )
    class_defs: AstClassDefs = get_module_ast_class_defs(file_path)
    for class_def in class_defs:
        to_append = ClassData(
            module_path=str(file_path),
            class_name=class_def.name,
            class_nodes=list(ast.walk(class_def)),
        )
        if is_enum_class(class_def):
            all_enum_classes.append(to_append)

###########################################
# Test if all enum class names are unique #
###########################################


def test_unique_enum_class_names() -> None:
    names_to_modules: dict[str, set[str]] = {}

    for item in all_enum_classes:
        names_to_modules.setdefault(item.class_name, set())
        names_to_modules[item.class_name].add(item.module_path)

    pytest_fail_messages: list[str] = []
    failed_names: list[str] = []
    for class_name, modules in names_to_modules.items():
        if len(modules) > 1:
            failed_names.append(class_name)
            pytest_fail_messages.append(
                f"{class_name} found in modules:\n- {'\n- '.join(sorted(modules))}"
            )

    if pytest_fail_messages:
        header = (
            f"Duplicate enum class names found: {', '.join(sorted(failed_names))}\n"
            if failed_names
            else ""
        )
        pytest.fail(header + "\n".join(pytest_fail_messages))


###########################################
# Test if all enum class names are in use #
###########################################


@pytest.mark.parametrize(
    "class_data",
    all_enum_classes,
    ids=lambda x: f"{x.class_name} ({x.module_path})",
)
def test_enum_members_in_use(class_data: ClassData) -> None:
    results: list[str] = []
    # Skip enums that are used dynamically, not in scope for static tests
    if class_data.class_name in EXCLUDE_ENUMS:
        pytest.skip(f"Skipping dynamic enum {class_data.class_name}")

    # Construct the member names to check
    enum_member_names: list[str] = []
    for class_node in class_data.class_nodes:
        if isinstance(class_node, ast.Assign):
            target = class_node.targets[0]
            if isinstance(target, ast.Name):
                enum_member_names.append(target.id)

    # For each enum member, search for any usage in non-enum classes
    # or in other enum classes. We look for attribute access like
    # EnumClass.member_name (or nested attribute chains) and for
    # getattr(EnumClass, 'member_name').
    for member_name in enum_member_names:
        if member_name.startswith("_"):
            # Skip private members
            continue
        found = False
        for module_data in module_data_list:
            if found:
                break
            for node in module_data.module_nodes:
                if isinstance(node, ast.ClassDef):
                    if node.name == class_data.class_name:
                        # Skip the enum class itself
                        continue
                if isinstance(node, ast.Attribute):
                    # direct access: EnumClass.member_name
                    if isinstance(node.value, ast.Name):
                        if (
                            node.value.id == class_data.class_name
                            and node.attr == member_name
                        ):
                            found = True
                            break
                    # access like module.EnumClass.member_name
                    elif isinstance(node.value, ast.Attribute):
                        if (
                            isinstance(node.value.value, ast.Name)
                            and node.value.attr == class_data.class_name
                            and node.attr == member_name
                        ):
                            found = True
                            break
                elif isinstance(node, ast.Call):
                    if (
                        isinstance(node.func, ast.Name)
                        and node.func.id == "getattr"
                        and len(node.args) >= 2
                    ):
                        if (
                            isinstance(node.args[0], ast.Name)
                            and node.args[0].id == class_data.class_name
                        ):
                            if (
                                isinstance(node.args[1], ast.Constant)
                                and node.args[1].value == member_name
                            ):
                                found = True
                                break

        if found is False:
            results.append(
                f"{class_data.class_name}.{member_name} (in {class_data.module_path})"
            )
    if results:
        pytest.fail("\n".join(results))
