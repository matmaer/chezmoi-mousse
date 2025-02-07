# import os

# from textual import log


# textual_console_groups = (
#     "DEBUG"
#     "ERROR"
#     "EVENT"
#     "INFO"
#     "LOGGING"
#     "PRINT"
#     "SYSTEM"
#     "WARNING"
#     "WORKER"
# )

# class DebugUtils:
#     @staticmethod
#     def print_env_vars():
#         for key, value in os.environ.items():
#             log(print(f"{key}: {value}"))


# from app.py
# -----------

# @property
# def log(self) -> Logger:
#     """The textual logger.

#     Example:
#         ```python
#         self.log("Hello, World!")
#         self.log(self.tree)
#         ```

#     Returns:
#         A Textual logger.
#     """
#     return self._logger


# from dom.py:
# ------------

# @property
# def tree(self) -> Tree:
#     """A Rich tree to display the DOM.

#     Log this to visualize your app in the textual console.

#     Example:
#         ```python
#         self.log(self.tree)
#         ```

#     Returns:
#         A Tree renderable.
#     """


# @property
# def css_tree(self) -> Tree:
#     """A Rich tree to display the DOM, annotated with the node's CSS.

#     Log this to visualize your app in the textual console.

#     Example:
#         ```python
#         self.log(self.css_tree)
#         ```

#     Returns:
#         A Tree renderable.
#     """

