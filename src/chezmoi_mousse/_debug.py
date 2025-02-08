
# self.app.log.debug(self.__class__.__mro__)
# self.app.log.debug(self.tree)
# self.app.log.debug(self.css_tree)
# self.app.log.debug(self.ancestors)
# self.app.log.debug(self.children)
# self.app.log.debug(self.css_identifier)

# log like this:
# self.app.log.debug(self.__class__.__mro__)

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

