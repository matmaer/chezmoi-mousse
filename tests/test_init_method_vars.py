import ast
from pathlib import Path

import pytest
from _test_utils import modules_to_test

# Precompute attribute names used in each module to allow cross-module usage exemptions.
_SRC_MODULE_FILES: list[Path] = modules_to_test()
_ATTR_NAMES_BY_FILE: dict[Path, set[str]] = {}


def _scan_file_attribute_names(py_file: Path) -> set[str]:
    try:
        tree = ast.parse(
            py_file.read_text(encoding="utf-8"), filename=str(py_file)
        )
    except Exception:
        return set()
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute):
            names.add(node.attr)
    return names


if not _ATTR_NAMES_BY_FILE:
    for _file in _SRC_MODULE_FILES:
        _ATTR_NAMES_BY_FILE[_file] = _scan_file_attribute_names(_file)


@pytest.mark.parametrize(
    "py_file", modules_to_test(), ids=lambda py_file: py_file.name
)
def test_no_unused_self_vars(py_file: Path):
    content = py_file.read_text(encoding="utf-8")
    tree = ast.parse(content, filename=str(py_file))

    unused_report: list[str] = []

    # Traverse classes; per class collect assignments in __init__ and usages elsewhere in one pass
    for class_node in tree.body:
        if not isinstance(class_node, ast.ClassDef):
            continue

        assigned: set[str] = set()
        used_elsewhere: set[str] = set()
        has_init = False

        for func in class_node.body:
            if not isinstance(func, ast.FunctionDef):
                continue
            if not func.args.args:
                continue
            self_name = func.args.args[0].arg
            is_init = func.name == "__init__"
            if is_init:
                has_init = True
            for node in ast.walk(func):
                # Track assignments only in __init__
                if is_init:
                    if isinstance(node, ast.Assign):
                        for target in node.targets:
                            # self.x = ...
                            if (
                                isinstance(target, ast.Attribute)
                                and isinstance(target.value, ast.Name)
                                and target.value.id == self_name
                            ):
                                assigned.add(target.attr)
                            # (self.x, self.y) = ...
                            elif isinstance(target, (ast.Tuple, ast.List)):
                                for elt in target.elts:
                                    if (
                                        isinstance(elt, ast.Attribute)
                                        and isinstance(elt.value, ast.Name)
                                        and elt.value.id == self_name
                                    ):
                                        assigned.add(elt.attr)
                    elif isinstance(node, ast.AnnAssign):
                        t = node.target
                        if (
                            isinstance(t, ast.Attribute)
                            and isinstance(t.value, ast.Name)
                            and t.value.id == self_name
                        ):
                            assigned.add(t.attr)
                    elif isinstance(node, ast.AugAssign):
                        t = node.target
                        if (
                            isinstance(t, ast.Attribute)
                            and isinstance(t.value, ast.Name)
                            and t.value.id == self_name
                        ):
                            assigned.add(t.attr)
                # Track usage only in non-__init__ methods
                else:
                    if (
                        isinstance(node, ast.Attribute)
                        and isinstance(node.value, ast.Name)
                        and node.value.id == self_name
                    ):
                        used_elsewhere.add(node.attr)

        if not has_init or not assigned:
            continue
        # skip pure data/message classes whose only method is __init__
        method_names = [
            f.name for f in class_node.body if isinstance(f, ast.FunctionDef)
        ]
        if method_names == ["__init__"]:
            continue
        # Treat attributes passed as id=self.attr in super().__init__ as used (lost logic restored)
        for func in class_node.body:
            if (
                isinstance(func, ast.FunctionDef)
                and func.name == "__init__"
                and func.args.args
            ):
                init_self_name = func.args.args[0].arg
                for call in [
                    n for n in ast.walk(func) if isinstance(n, ast.Call)
                ]:
                    for kw in getattr(call, "keywords", []):
                        if (
                            kw.arg == "id"
                            and isinstance(kw.value, ast.Attribute)
                            and isinstance(kw.value.value, ast.Name)
                            and kw.value.value.id == init_self_name
                        ):
                            used_elsewhere.add(kw.value.attr)
        unused_attrs = sorted(assigned - used_elsewhere)
        if unused_attrs:
            # Cross-module exemption: drop attrs whose name appears as attribute access in any other module
            external_attr_names: set[str] = set()
            for f, names in _ATTR_NAMES_BY_FILE.items():
                if f != py_file:
                    external_attr_names.update(names)
            unused_attrs = [
                a for a in unused_attrs if a not in external_attr_names
            ]
        if unused_attrs:
            unused_report.append(
                f"{py_file.name}::{class_node.name} -> {', '.join(unused_attrs)}"
            )

    if unused_report:
        pytest.fail(
            "Unused self attribute(s) detected (assigned in __init__ only):\n"
            + "\n".join(unused_report)
        )
