# import ast
# import pprint

# import pytest
# from _test_utils import get_module_paths


# def _get_all_class_sources() -> dict[str, str]:
#     """Returns a dict with the keys being the class name and the value being
#     the class source codes for that class."""
#     class_sources: dict[str, str] = {}
#     for p in get_module_paths():
#         content = p.read_text(encoding="utf-8")
#         tree = ast.parse(content)
#         for node in ast.walk(tree):
#             if isinstance(node, ast.ClassDef):
#                 source_segment = ast.get_source_segment(content, node)
#                 if source_segment:
#                     class_sources[node.name] = source_segment
#     return class_sources


# @pytest.mark.parametrize(
#     "class_name, class_source",
#     _get_all_class_sources().items(),
#     ids=list(_get_all_class_sources().keys()),  # Use class names as short IDs
# )
# def test_get_all_class_source_members(class_name: str, class_source: str):
#     tree = ast.parse(class_source)
#     class_def = tree.body[0]
#     members: dict[str, str] = {}
#     if isinstance(class_def, ast.ClassDef):
#         for node in class_def.body:
#             if (
#                 isinstance(node, ast.FunctionDef)
#                 and not node.name.startswith("_")
#                 and node.name not in ["compose", "on_mount"]
#                 and not node.name.startswith("watch_")
#             ):
#                 members[node.name] = "method"
#             elif isinstance(node, ast.Assign):
#                 for target in node.targets:
#                     if isinstance(
#                         target, ast.Name
#                     ) and not target.id.startswith("_"):
#                         members[target.id] = "attribute"
#     print("\n")
#     pprint.pprint(members)
#     print("\n")
