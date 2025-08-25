# from textual.widgets import Button

# from chezmoi_mousse.gui import ChezmoiGUI


# async def test_buttons_clickable():
#     """Test pressing every button."""
#     app = ChezmoiGUI()

#     async with app.run_test() as pilot:
#         # Wait for the app to be ready before querying buttons
#         await pilot.pause()

#         # Query buttons after the app is running
#         buttons = app.query(Button)

#         for btn in buttons:
#             print(f"Clicking button: {btn}")
#             await pilot.click(btn)
