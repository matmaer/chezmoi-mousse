# """Test if all class members are in use."""

# import ast
# import importlib.util
# from pathlib import Path
# from typing import Any

# # import pytest

# from _test_utils import get_module_classes


# def get_classes_to_test(module_paths: list[Path]) -> list[type]:
#     classes_to_test: list[type] = []
#     for module_path in module_paths:
#         module_name = module_path.stem
#         spec = importlib.util.spec_from_file_location(module_name, module_path)
#         if spec and spec.loader:
#             module = importlib.util.module_from_spec(spec)
#             spec.loader.exec_module(module)
#             module_classes = get_module_classes(module)
#             if module_classes:
#                 classes_to_test.extend(module_classes)
#     return classes_to_test


# def get_class_public_member_objects(
#     class_object: type,
# ) -> dict[str, list[Any]] | None:
#     """
#     Get public member objects of a class, categorized into properties, methods, and attributes.
#     Uses AST to parse the class source and identify defined members, then retrieves the objects.
#     Includes both annotated and non-annotated attributes, excluding type objects.
#     """
#     import inspect

#     try:
#         source = inspect.getsource(class_object)
#     except (OSError, TypeError):
#         # If source cannot be retrieved, return None
#         return None

#     tree = ast.parse(source)

#     class_def = None
#     for node in ast.walk(tree):
#         if isinstance(node, ast.ClassDef):
#             class_def = node
#             break

#     if not class_def:
#         return None

#     public_members: set[str] = set()

#     for node in class_def.body:
#         if isinstance(node, ast.FunctionDef) and not node.name.startswith("_"):
#             public_members.add(node.name)
#         elif isinstance(node, ast.Assign):
#             for target in node.targets:
#                 if isinstance(target, ast.Name) and not target.id.startswith(
#                     "_"
#                 ):
#                     public_members.add(target.id)
#         elif isinstance(node, ast.AnnAssign):
#             # Include annotated attributes (with or without assignment)
#             if isinstance(
#                 node.target, ast.Name
#             ) and not node.target.id.startswith("_"):
#                 public_members.add(node.target.id)
#         # Check for properties (functions with @property decorator)
#         elif (
#             isinstance(node, ast.FunctionDef)
#             and any(
#                 (isinstance(d, ast.Name) and d.id == "property")
#                 or (isinstance(d, ast.Attribute) and d.attr == "property")
#                 for d in node.decorator_list
#             )
#             and not node.name.startswith("_")
#         ):
#             public_members.add(node.name)

#     # Retrieve objects and categorize
#     result: dict[str, list[Any]] = {
#         "property": [],
#         "method": [],
#         "attribute": [],
#     }
#     for name in public_members:
#         try:
#             obj = getattr(class_object, name)
#             if isinstance(obj, property):
#                 result["property"].append(obj)
#             elif callable(obj):
#                 result["method"].append(obj)
#             else:
#                 # Exclude type objects from attributes
#                 if not isinstance(obj, type):
#                     result["attribute"].append(obj)
#         except AttributeError:
#             pass  # Skip if not accessible

#     return result


# def test_class_members_in_use(class_object: type):

#     class_members_dict: dict[str, list[Any]] | None = (
#         get_class_public_member_objects(class_object)
#     )
#     if class_members_dict is None:
#         pytest.skip(f"No members received for {class_object.__name__}")

#     unused_members: dict[str, list[str]] | None = None

#     for py_file in get_module_paths():
#         for key, value_list in class_members_dict:
#             for member in value_list:
#                 # logic to be added
#                 ...

#     if unused_members is not None:
#         for key, values in unused_members:
#             for value in values:
#                 pytest.fail(
#                     f"Class {key}\n{value} is not in use outside of the class."
#                 )
