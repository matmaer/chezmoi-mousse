import cProfile
import pstats
from chezmoi_mousse.tui import ChezmoiTUI


def main():
    profiler = cProfile.Profile()
    profiler.enable()

    app = ChezmoiTUI()
    app.run(inline=False, headless=False, mouse=True)

    profiler.disable()
    profiler.dump_stats(
        "/home/mm/repos/chezmoi-mousse/profiling/profiling_data"
    )
    stats = pstats.Stats(profiler)
    stats.strip_dirs()
    stats.sort_stats("cumulative")
    stats.print_stats(20)  # Print the top 20 functions by cumulative time


if __name__ == "__main__":
    main()
