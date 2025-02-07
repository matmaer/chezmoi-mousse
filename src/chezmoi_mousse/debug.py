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







# to integrate
# use textual.log so no need for screen or other code that could lead to merge conflicts
# create util function to call self.log(self.css) or self.log(self.css_tree)
# make util functions to show app.xxx contents
# locals()
# globals()
# active workers
# check logging events, example from Jazz
# logging message, example from Jazzhands:
# @on(MyWidget.EventFoo)
# async def cell_chosen(self, event: MyWidget.EventFoo):
#     self.log.debug(
#         f"event_foo: {event} \n"
#         f"Row, col: {event.row}, {event.column}"    # example attributes in event
#     )