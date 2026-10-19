from pathlib import Path

from PIL import Image, ImageSequence


root = Path(__file__).resolve().parents[4]
source = Image.open(root / "design" / "Untitled_Artwork.gif")
output = root / "src" / "web" / "frontend" / "public" / "assets"
duration = source.info.get("duration", 50)


def frames_at(size: int) -> list[Image.Image]:
    source.seek(0)
    return [
        frame.convert("RGBA").resize((size, size), Image.Resampling.NEAREST)
        for frame in ImageSequence.Iterator(source)
    ]


for size in (240, 120):
    frames = frames_at(size)
    suffix = "" if size == 240 else "-small"
    frame_duration = duration
    if size == 120:
        frames = frames[::2]
        frame_duration *= 2
    if size == 240:
        frames[0].save(
            output / "wayfinder-wait.png",
            format="PNG",
            optimize=True,
        )
    frames[0].save(
        output / f"wayfinder-wait{suffix}.gif",
        format="GIF",
        save_all=True,
        append_images=frames[1:],
        duration=frame_duration,
        loop=0,
        disposal=2,
        optimize=True,
    )
