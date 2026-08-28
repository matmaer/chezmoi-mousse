import ast
from collections.abc import Callable


def is_dataclass(node: ast.ClassDef) -> bool:
    for decorator in node.decorator_list:
        if isinstance(decorator, ast.Name) and decorator.id == "dataclass":
            return True
        if isinstance(decorator, ast.Call):
            func = decorator.func
            if isinstance(func, ast.Name) and func.id == "dataclass":
                return True
            if isinstance(func, ast.Attribute) and func.attr == "dataclass":
                return True
    return False


class DataclassFieldUsageRule:
    def __init__(self) -> None:
        self.defined_fields: dict[str, tuple[str, int]] = {}
        self.used_field_names: set[str] = set()

    def get_rule_data(self, node: ast.AST, file_path: str) -> None:
        if isinstance(node, ast.ClassDef) and is_dataclass(node):
            for item in node.body:
                if isinstance(item, ast.AnnAssign) and isinstance(
                    item.target, ast.Name
                ):
                    field_key = f"{node.name}.{item.target.id}"
                    self.defined_fields[field_key] = (file_path, item.lineno)

        elif isinstance(node, ast.Attribute):
            self.used_field_names.add(node.attr)

        elif isinstance(node, ast.keyword) and node.arg:
            self.used_field_names.add(node.arg)

    def get_issues(self) -> list[str]:
        unused: list[str] = []
        for field_key, (file, line) in self.defined_fields.items():
            class_name, field_name = field_key.split(".")

            if field_name not in self.used_field_names:
                unused.append(
                    f"Unused dataclass field '{field_name}' in {class_name} "
                    f"({file}:{line})"
                )

        return unused


def test_dataclass_fields(run_ast_rule: Callable[..., list[str]]) -> None:
    run_ast_rule(DataclassFieldUsageRule())
