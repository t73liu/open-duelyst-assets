import argparse
import json

from PIL import Image

parser = argparse.ArgumentParser()

parser.add_argument(
    "--sheet-path",
    help="path to spritesheet",
    required=True,
    type=str,
)
parser.add_argument(
    "--frames-path",
    help="path to animation frames",
    required=True,
    type=str,
)
parser.add_argument(
    "--output",
    default="examples",
    help="folder to write GIFs",
    type=str,
)


def write_gif(images: list[Image.Image], output: str):
    assert len(images) > 1, "GIF must be longer than 1 frame"
    img = images[0]
    img.save(
        output,
        format="GIF",
        save_all=True,
        append_images=images[1:],
        duration=120,
        loop=0,
    )
    # Image.new("RGBA", (width, height), (255, 0, 0))


def read_animation_frames(filename: str):
    with open(filename) as f:
        return json.load(f)


def generate_gifs(sheet_path: str, frames_path: str, output: str):
    sheet = Image.open(sheet_path)
    all_frames = read_animation_frames(frames_path)["frames"]
    for animation in all_frames:
        images = []
        for frame in all_frames[animation]:
            sprite = sheet.crop((frame["x0"], frame["y0"], frame["x1"], frame["y1"]))
            images.append(sprite)
        write_gif(images, f"{output}/{animation}.gif")


def main():
    args = parser.parse_args()
    generate_gifs(args.sheet_path, args.frames_path, args.output)


if __name__ == "__main__":
    main()
