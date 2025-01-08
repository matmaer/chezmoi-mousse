# MainMenu {
#   dock: left;
#   width: 18;
#   margin: 6 0 4 0;
#   height: auto;
#   # layer to sit above content
#   layer: sliders;
# }

# MainMenu.-hidden {
#   display: none;
# }

# MainMenu > Button {
#   border-right: $ui_border;
#   border-top: $ui_border;
#   border-bottom: $ui_border;
#   color: $ui_text;
#   padding: 1 2 0 2;
#   width: 100%;
#   height: 7;
# }

# MainMenu > Button:focus {
#   border-right: round $ui_react_border;
#   border-top: $ui_react_border;
#   border-bottom: $ui_react_border;
#   background-tint: $base_background;
#   color: $ui_react_text;
#   text-style: bold;
# }

# MainMenu > Button:hover {
#   border-right: round $ui_react_border;
#   border-top: $ui_react_border;
#   border-bottom: $ui_react_border;
# }


# RichLog {
#   padding: 0 1 0 1;
#   width: 100%;
#   height: 100%;
#   border-left: $ui_border;
#   border-top: $ui_border;
#   border-bottom: $ui_border;
#   margin: 6 0 4 0;
#   dock: right;
#   max-width: 80%;
#   min-height: 3;
#   # layer to sit above content
#   layer: sliders;
#   transition: offset 400ms;
#   # Offset -100% (left) and 100% (right) to be out of view
#   offset-x: 100%;
#   &:focus {
#     background-tint: $base_background;
#   }
#   &.-visible {
#     # offset.x reaches 0 when fully slided in view
#       offset-x: 0;
#   }
# }


# Binding(
#     key="m",
#     action="toggle_mainmenu",
#     description="Main Menu",
#     key_display="m",
# ),
# Binding(
#     key="s",
#     action="toggle_richlog",
#     description="Standard Output",
#     key_display="s",
# ),

# richlog_visible = reactive(False)

# def rlog(self, to_print: str) -> None:
#     richlog = self.query_one(RichLog)
#     richlog.write(to_print)

# def action_toggle_richlog(self) -> None:
#     self.richlog_visible = not self.richlog_visible

# def watch_richlog_visible(self, richlog_visible: bool) -> None:
#     # Set or unset visible class when reactive changes.
#     self.query_one(MousseLogger).set_class(richlog_visible, "-visible")


# class MainMenu(Vertical):
#     def compose(self) -> ComposeResult:
#         yield Button(
#             label="Inspect",
#             id="inspect",
#         )
#         yield Button(
#             label="Operate",
#             id="operate",
#         )
#         yield Button(
#             label="Setting",
#             id="settings",
#         )

# def action_toggle_mainmenu(self):
#     self.query_one(MainMenu).toggle_class("-hidden")

# @on(Button.Pressed, "#inspect")
# def enter_inspect_mode(self):
#     self.rlog.write("[cyan]Inspect Mode[/]")
#     self.rlog.write("[red]Inspect mode is not yet implemented[/]")

# @on(Button.Pressed, "#operate")
# def enter_operate_mode(self):
#     self.rlog.write("[cyan]Operate Mode[/]")
#     self.rlog.write("[red]Operate mode is not yet implemented[/]")

# @on(Button.Pressed, "#settings")
# def enter_config_mode(self):
#     self.rlog.write("[cyan]Configuration Mode[/]")
#     self.rlog.write("[red]Configuration mode is not yet implemented[/]")
