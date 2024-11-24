import argparse
import glob
import json
import os
import plistlib
import shutil
from pathlib import Path

parser = argparse.ArgumentParser()

parser.add_argument("--src", help="path to cloned open-duelyst repo", type=str)
parser.add_argument("--dest", default="assets", help="folder to move assets", type=str)

resources_folder = "app/resources"

excluded_plist_folders = {
    "arena",
    "booster_pack_opening",
    "core_gem",
    "loot_crates",
    "matchmaking",
    "particles",
    "prismatic",
    "rift",
    "tutorial",
}


animations = [
    "attack",
    "breathing",
    "death",
    "hit",
    "idle",
    "run",
]


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
    Convert .plist files to .json files for sprite sheets.
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
                res["size"] = parse_tuples(size)
            else:
                raise RuntimeError(f"Unhandled plist key {k}")

    with open(dest, "w") as fp:
        json.dump(res, fp)


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
    for k in frames:
        animation_type = k.split("_")[-2]
        if animation_type not in animations:
            unhandled_animation_types.add(animation_type)
            animation_type = "default"
        if res.get(animation_type) is None:
            res[animation_type] = []
        frame = frames[k]
        assert isinstance(frame["frame"], str)
        assert isinstance(frame["offset"], str)
        assert isinstance(frame["sourceSize"], str)
        res[animation_type].append(
            {
                "filename": k,
                "frame": parse_tuples(frame["frame"]),
                "offset": parse_tuples(frame["offset"]),
                "rotated": frame["rotated"],
                "source_size": parse_tuples(frame["sourceSize"]),
            }
        )

    if len(unhandled_animation_types) > 1:
        raise RuntimeError(
            f"More than one unhandled animation type {unhandled_animation_types}"
        )

    return res


def parse_tuples(s: str):
    nums = s.replace("{", "").replace("}", "").split(",")
    nums = [int(n) for n in nums]

    if len(nums) == 2:
        return nums

    res = []
    i = 0
    while i < len(nums):
        res.append([nums[i], nums[i + 1]])
        i += 2
    return res


def main():
    args = parser.parse_args()
    # move_png_assets(args.src, args.dest)
    convert_plists(args.src, args.dest)


if __name__ == "__main__":
    main()
