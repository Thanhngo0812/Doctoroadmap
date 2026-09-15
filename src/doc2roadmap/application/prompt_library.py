from pathlib import Path


PROMPT_ROOT = Path(__file__).with_name("prompts")


def load_prompt(phase: str, name: str) -> str:
    path = PROMPT_ROOT / phase / f"{name}.txt"
    try:
        return path.read_text(encoding="utf-8").strip()
    except FileNotFoundError as error:
        raise FileNotFoundError(f"không tìm thấy prompt: {path}") from error
