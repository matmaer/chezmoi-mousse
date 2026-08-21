import ast
import re

import pytest

from static_tests._cached_data import MODULE_DIR, ast_parse, get_file_paths

# Standard Textual/Python builtin actions that don't need a local custom action_ handler
BUILTIN_ACTIONS = {
    "quit",
    "exit",
    "noop",
    "none",
    "toggle_dark",
    "screenshot",
    "focus",
    "back",
    "forward",
}


def camel_to_snake(name: str) -> str:
    """Convert CamelCase to snake_case."""
    s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
    return re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1).lower()


class TextualHousekeepingDetector(ast.NodeVisitor):
    def __init__(self) -> None:
        self.current_file: str = ""
        self.current_class: str | None = None

        # Tracking for Bindings vs Actions
        # class_name -> set(local action method names e.g., 'action_quit')
        self.class_actions: dict[str, set[str]] = {}
        # class_name -> list of base class names
        self.class_bases: dict[str, list[str]] = {}
        # List of tuples: (class_name, action_name, file, line) for checks
        self.bindings_to_check: list[tuple[str, str, str, int]] = []

        # Tracking for Custom Messages
        # Set of all defined custom Message class names
        self.custom_messages: set[str] = set()
        # Set of all message class names that are instantiated/mentioned in code
        self.message_instantiations: set[str] = set()
        # Set of message class names that are referenced in @on(MyMsg) or similar
        self.message_listeners: set[str] = set()

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        # Save old class context for nested classes
        old_class = self.current_class
        self.current_class = node.name

        # Record class bases
        bases: list[str] = []
        is_message_subclass = False
        for base in node.bases:
            if isinstance(base, ast.Name):
                bases.append(base.id)
                if "Message" in base.id:
                    is_message_subclass = True
            elif isinstance(base, ast.Attribute):
                bases.append(base.attr)
                if "Message" in base.attr:
                    is_message_subclass = True
        self.class_bases[node.name] = bases

        if is_message_subclass or node.name.endswith("Msg"):
            self.custom_messages.add(node.name)

        # Record action methods defined in this class
        local_actions: set[str] = set()
        for item in node.body:
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if item.name.startswith("action_"):
                    local_actions.add(item.name)
                # Check for on_... method listeners (implicit message handling)
                if item.name.startswith("on_"):
                    # e.g., on_current_node_msg -> CurrentNodeMsg
                    func_name = item.name
                    # Try to map camel case / name match if possible
                    self.message_listeners.add(func_name)
        self.class_actions[node.name] = local_actions

        # Now scan class body specifically for Binding definitions
        self.generic_visit(node)
        self.current_class = old_class

    def visit_Call(self, node: ast.Call) -> None:
        # Check for Binding(...) calls inside classes
        if (
            self.current_class
            and isinstance(node.func, ast.Name)
            and node.func.id == "Binding"
        ):
            self._process_binding_call(node)

        # Check for message instantiation or reference as a listener
        if isinstance(node.func, ast.Name):
            if node.func.id == "on" and node.args:
                # e.g. @on(CurrentNodeMsg)
                for arg in node.args:
                    if isinstance(arg, ast.Name):
                        self.message_listeners.add(arg.id)
            else:
                # General function or class instantiation call
                self.message_instantiations.add(node.func.id)

        self.generic_visit(node)

    def _process_binding_call(self, node: ast.Call) -> None:
        if self.current_class is None:
            return

        # Try to find the action Name/Value
        action_node = None

        # Positional arguments: key, action, description
        if len(node.args) >= 2:
            action_node = node.args[1]

        # Keyword arguments: action=...
        for kw in node.keywords:
            if kw.arg == "action":
                action_node = kw.value
                break

        if not action_node:
            return

        action_name = None
        if isinstance(action_node, ast.Constant) and isinstance(action_node.value, str):
            action_name = action_node.value
        elif isinstance(action_node, ast.Attribute):
            action_name = action_node.attr
        elif isinstance(action_node, ast.Name):
            action_name = action_node.id

        if action_name:
            # Strip potential call arguments if parameterized e.g., action="quit('now')"
            action_name = action_name.split("(")[0].strip()
            self.bindings_to_check.append(
                (self.current_class, action_name, self.current_file, node.lineno)
            )


def test_textual_housekeeping() -> None:
    detector = TextualHousekeepingDetector()

    for file_path in get_file_paths():
        detector.current_file = str(file_path.relative_to(MODULE_DIR))
        tree = ast_parse(file_path)
        detector.visit(tree)

    # List of inherited/resolved action handlers for each class
    resolved_actions: dict[str, set[str]] = {}

    def get_all_actions(cls: str) -> set[str]:
        if cls in resolved_actions:
            return resolved_actions[cls]
        actions = set(detector.class_actions.get(cls, []))
        for base in detector.class_bases.get(cls, []):
            if base in detector.class_actions:
                actions.update(get_all_actions(base))
        resolved_actions[cls] = actions
        return actions

    # 1. Bindings validation
    failed_bindings: list[str] = []
    for cls, action, file, line in detector.bindings_to_check:
        if action in BUILTIN_ACTIONS:
            continue

        action_method = f"action_{action}"
        all_class_actions = get_all_actions(cls)

        if action_method not in all_class_actions:
            failed_bindings.append(
                f"- Class '{cls}' binds action '{action}', but '{action_method}' "
                f"is not defined ({file}:{line})"
            )

    # 2. Custom Message validation
    unused_messages: list[str] = []
    for msg in sorted(detector.custom_messages):
        # Determine if there is an instantiation call anywhere
        is_instantiated = msg in detector.message_instantiations

        # Determine if there is any listener listening to it
        snake_name = camel_to_snake(msg)
        has_listener = (
            msg in detector.message_listeners
            or f"on_{snake_name}" in detector.message_listeners
        )

        missing_reasons: list[str] = []
        if not is_instantiated:
            missing_reasons.append("never instantiated/posted")
        if not has_listener:
            missing_reasons.append("has no event listener (@on or on_handler)")

        if missing_reasons:
            unused_messages.append(f"- {msg} ({' and '.join(missing_reasons)})")

    errors: list[str] = []
    if failed_bindings:
        msg_header = "Found Action Bindings with missing or misspelled handlers:\n"
        errors.append(msg_header + "\n".join(failed_bindings))
    if unused_messages:
        msg_header = "\nFound unused or unhandled custom Messages:\n"
        errors.append(msg_header + "\n".join(unused_messages))

    if errors:
        pytest.fail("\n".join(errors))
