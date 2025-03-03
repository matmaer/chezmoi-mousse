# https://textual.textualize.io/guide/workers/#thread-workers
# The urllib module is not async aware, so we will need to use threads


# Use as reference for the loading module which is not async aware by design

from urllib.parse import quote
from urllib.request import Request, urlopen

from rich.text import Text

from textual import work
from textual.app import ComposeResult
from textual.containers import VerticalScroll
from textual.widgets import Input, Static
from textual.worker import Worker, get_current_worker
from textual.screen import Screen





class WeatherApp(Screen):

    def compose(self) -> ComposeResult:
        yield Input(placeholder="Enter a City")
        with VerticalScroll(id="weather-container"):
            yield Static(id="weather")

    #### nobody is calling this method
    async def on_input_changed(self, message: Input.Changed) -> None:
        """Called when the input changes"""
        self.update_weather(message.value)

    @work(exclusive=True, thread=True)
    def update_weather(self, city: str) -> None:
        """Update the weather for the given city."""
        weather_widget = self.query_one("#weather", Static)
        #### imported method
        worker = get_current_worker()
        # Query the network API
        request = Request(f"https://wttr.in/{quote(city)}")
        request.add_header("User-agent", "CURL")
        response_text = urlopen(request).read().decode("utf-8")
        weather = Text.from_ansi(response_text)
        if not worker.is_cancelled:
            self.app.call_from_thread(weather_widget.update, weather)

    def on_worker_state_changed(self, event: Worker.StateChanged) -> None:
        """Called when the worker state changes."""
        self.log(event)
