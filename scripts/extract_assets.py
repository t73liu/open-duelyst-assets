import argparse
import glob
import json
import os
import plistlib
import shutil
from pathlib import Path

parser = argparse.ArgumentParser()

parser.add_argument(
    "--src",
    help="path to cloned open-duelyst repo",
    required=True,
    type=str,
)
parser.add_argument(
    "--dest",
    default="assets",
    help="folder to generate assets",
    type=str,
)
parser.add_argument(
    "--move-png",
    default=False,
    help="move png assets",
    type=bool,
    action=argparse.BooleanOptionalAction,
)

resources_folder = "app/resources"

# The following plist files are not animations (e.g. static images or particle
# effects).
excluded_plist_folders = {
    "arena",
    "booster_pack_opening",
    "core_gem",
    "loot_crates",
    "maps",
    "matchmaking",
    "particles",
    "prismatic",
    "rift",
    "runes",
    "scenes",
    "tiles",
    "tutorial",
}


common_animations = {
    "active",
    "appear",
    "attack",
    "breath",
    "breathing",
    "cast",
    "caststart",
    "casting",
    "castend",
    "castloop",
    "crawl",
    "damage",
    "death",
    "disappear",
    "hit",
    "hurt",
    "idle",
    "move",
    "movement",
    "open",
    "projectile",
    "run",
}


def move_png_assets(src: str, dest: str):
    """
    Moves PNG files from src to dest location while maintaining folder structure.
    """
    src_folder = Path(src, resources_folder)
    src_to_dest_paths = {}
    dest_folders = set()
    for f in glob.iglob(os.path.join(src_folder, "**", "*.png"), recursive=True):
        relative_path = os.path.relpath(f, src_folder)
        target = Path(dest, relative_path)
        dest_folders.add(os.path.dirname(target))
        src_to_dest_paths[f] = target

    for f in dest_folders:
        Path.mkdir(Path(f), parents=True, exist_ok=True)

    for k in src_to_dest_paths:
        shutil.move(k, src_to_dest_paths[k])


def convert_plists(src: str, dest: str):
    """
    Convert .plist files to .json files for animations.
    """
    src_folder = Path(src, resources_folder)
    for f in glob.iglob(os.path.join(src_folder, "**", "*.plist"), recursive=True):
        relative_path = os.path.relpath(f, src_folder)
        target = Path(dest, relative_path.replace(".plist", ".json"))
        topmost_folder = relative_path.split(os.path.sep)[0]
        if topmost_folder not in excluded_plist_folders:
            convert_plist_file(f, str(target))


def convert_plist_file(src: str, dest: str):
    res = {}
    try:
        with open(src, "rb") as fp:
            pl = plistlib.load(fp)
            for k in pl:
                if k == "frames":
                    frames = parse_frames(pl[k])
                    res["frames"] = frames
                elif k == "metadata":
                    metadata = pl[k]
                    texture_filename = metadata["textureFileName"]
                    size = metadata["size"]
                    res["texture_filename"] = texture_filename
                    res |= format_dimensions(parse_tuples(size))
                else:
                    raise RuntimeError(f"Unhandled plist key {k}")

        with open(dest, "w") as fp:
            json.dump(res, fp, indent=None)
    except Exception as e:
        print(f"Failed to convert {src}: ", e)
        raise


def parse_frames(frames: dict[str, dict[str, str | bool]]):
    """
    Expects frames in the following format:
    {
      'frame': '{{303,101},{100,100}}',
      'offset': '{0,0}',
      'rotated': False,
      'sourceColorRect': '{{0,0},{100,100}}',
      'sourceSize': '{100,100}'
    }
    """
    res = {}
    unhandled_animation_types = set()
    sorted_frames = dict(sorted(frames.items()))
    for k in sorted_frames:
        frame_name_sections = k.replace("-", "_").lower().split("_")
        animation_type = frame_name_sections[-2]
        if animation_type.isnumeric():
            animation_type = frame_name_sections[-3]
        if animation_type not in common_animations:
            unhandled_animation_types.add(animation_type)
        if res.get(animation_type) is None:
            res[animation_type] = []
        frame = sorted_frames[k]
        assert isinstance(frame["frame"], str)
        assert isinstance(frame["sourceSize"], str)
        res[animation_type].append(
            {
                "frame_name": k,
                # Only fx_distortion_hex_shield uses rotation.
                # "rotated": frame["rotated"],
            }
            | format_frame(parse_tuples(frame["frame"]))
            | format_dimensions(parse_tuples(frame["sourceSize"]))
        )

    # If there is only a single animation type, rename it to default.
    if len(unhandled_animation_types) == 1 and len(res) == 1:
        for k in unhandled_animation_types:
            res["default"] = res.pop(k)

    return res


def parse_tuples(s: str) -> list[int]:
    nums = s.replace("{", "").replace("}", "").split(",")
    return [int(n) for n in nums]


def format_dimensions(nums: list[int]) -> dict[str, int]:
    return {
        "width": nums[0],
        "height": nums[1],
    }


def format_frame(nums: list[int]) -> dict[str, int]:
    assert len(nums) == 4, "Must have 4 numbers to select a sprite"
    return {
        "x0": nums[0],
        "y0": nums[1],
        "x1": nums[0] + nums[2],
        "y1": nums[1] + nums[3],
    }


def main():
    args = parser.parse_args()
    if args.move_png:
        move_png_assets(args.src, args.dest)
    convert_plists(args.src, args.dest)


if __name__ == "__main__":
    main()
