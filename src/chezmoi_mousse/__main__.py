from chezmoi_mousse.tui import ChezmoiTUI


def main():
    app = ChezmoiTUI()
    app.run(inline=False, headless=False, mouse=True)


if __name__ == "__main__":
    main()
