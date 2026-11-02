import random
from pathlib import Path

from chezmoi_mousse.str_enums import ProblemChars

rng = random.Random(42)
words = ["lorem", "ipsum", "dolor", "sit", "amet", "consectetur", "adipiscing", "elit"]
file_prefix = "_test_file"


def file_path(base_path: Path, name: str, ext: str, *, sib_idx: int) -> Path:
    prefix = file_prefix
    sib_str = f"sib_{sib_idx}"
    if sib_idx == 0:
        return base_path / f"{prefix}_{name}{ext}"
    return base_path / f"{prefix}_{name}_{sib_str}{ext}"


def file_name(name: str, ext: str) -> str:
    prefix = file_prefix
    return f"{prefix}_{name}{ext}"


def dir_path(
    base_path: Path, name: str | None, *, depth: int, sibling: bool = False
) -> Path:
    depth_str = f"dep{depth}"
    dir_name = f"_test_dir_{name}" if name is not None else "_test_dir"
    if depth == 0:
        return base_path / dir_name
    if not sibling:
        return base_path / f"{dir_name}_{depth_str}"
    return base_path / f"{dir_name}_{depth_str}_sibling"


def initial_text(test_file_size: int) -> str:

    paragraphs: list[str] = []
    current_bytes: int = 0

    while current_bytes < test_file_size:
        word_count: int = rng.randint(20, 60)
        paragraphs.append(" ".join(rng.choices(words, k=word_count)) + ".\n\n")
        current_bytes += len(paragraphs[-1])

    return "".join(paragraphs)


def tricky_utf8_text() -> str:
    rng = random.Random(42)
    parts: list[str] = []
    parts.append(" ".join(words))
    parts.append("".join(rng.choice("!@#$%^&*()[]{};:,.<>/?\\\"'") for _ in range(60)))
    parts.append("".join(chr(rng.randint(0x0600, 0x06FF)) for _ in range(30)))
    parts.append("".join(chr(rng.randint(0x4E00, 0x9FFF)) for _ in range(30)))
    # emoji sequences and variation selectors
    parts.append("🙂🚀🔥" * 10 + ProblemChars.VARSEL)
    # combining sequences
    parts.append(
        "e"
        + ProblemChars.COMBINING
        + "a"
        + ProblemChars.COMBINING
        + "o"
        + ProblemChars.COMBINING
    )
    parts.append(
        ProblemChars.BIDI_RLO
        + words[2]
        + ProblemChars.BIDI_PDF
        + ProblemChars.ZWS
        + words[3]
    )
    return "".join(parts)


def control_chars_bytes(f_size: int) -> bytes:
    return bytes(rng.randrange(1, 32) for _ in range(f_size))


def high_entropy_bytes(f_size: int) -> bytes:
    return rng.randbytes(f_size)


def invalid_utf8_bytes(f_size: int) -> bytes:
    return bytes(rng.randrange(128, 256) for _ in range(f_size))


def null_bytes(f_size: int) -> bytes:
    null_data = bytearray(f_size)
    null_data[rng.randrange(f_size)] = rng.randrange(1, 256)
    return bytes(null_data)


def printable_ascii_bytes(f_size: int) -> bytes:
    printable = bytes(range(32, 127)) + b"\n\r\t"
    return bytes(rng.choice(printable) for _ in range(f_size))


def utf16_interleaved_bytes(f_size: int) -> bytes:
    utf16_interleaved = bytearray(f_size)
    for offset in range(0, f_size, 2):
        utf16_interleaved[offset] = rng.randrange(65, 91)
    return bytes(utf16_interleaved)
