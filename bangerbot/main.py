import json
import shutil
import subprocess
from functools import cached_property
from pathlib import Path

import click
from pydantic import BaseModel, computed_field
from pydantic_core._pydantic_core import ValidationError

import bangerbot
from bangerbot import utils

BB_PATHS_FILE_PATH = utils.get_bb_paths_file_path()
VERSION = utils.get_bb_version()

DEFAULT_BB_ROOT_PATH = Path("~/Music/bangerbot")
DEFAULT_BANGERS_FILE_PATH = Path("~/Music/bangerbot/bangers.txt")

HQ_TYPE = [".wav", ".aiff"]
LQ_TYPE = [".mp3", ".m4a"]


@click.version_option(version=VERSION, prog_name=bangerbot.__name__)
@click.group()
def bangerbot():
    pass


@bangerbot.command(
    help="""Setup the location for BangerBot to download files to. Downloaded
    bangers will either be placed into an 'HQ' (High Quality) or 'LQ' (Low
    Quality) folder depending on their format. The 'bangers.txt' and
    'bangers_history.txt' files used for the 'banger batch' command will be
    placed there."""
)
@click.option(
    "-p",
    "--path",
    prompt="Enter the location for banger to download files to.",
    type=click.Path(),
    default=DEFAULT_BB_ROOT_PATH,
    help="The root location for banger to work with.",
)
def init(path: click.Path):
    scdl = shutil.which("scdl")
    if not scdl:
        utils.install_pipx_dependency("scdl")

    yt_dlp = shutil.which("yt-dlp")
    if not yt_dlp:
        utils.install_pipx_dependency("yt-dlp")

    bbot_root_path = Path(path).expanduser()
    bb_paths = BangerBotPaths(root=bbot_root_path)
    bb_paths.create()
    bb_paths.save(BB_PATHS_FILE_PATH)

    print("Setup complete. Created:")
    print(f"    - 'HQ-tracks' folder: {utils.ppath(bb_paths.hq_tracks)}")
    print(f"    - 'LQ-tracks' folder: {utils.ppath(bb_paths.lq_tracks)}")
    print(f"    - 'bangers.txt' file: {utils.ppath(bb_paths.batch_file)}")
    print(f"    - 'bangers_history.txt' file: {utils.ppath(bb_paths.batch_history_file)}")


@bangerbot.command(help="Download a track from a Youtube or Soundcloud url")
@click.argument("music_url")
@click.option(
    "--mp3",
    is_flag=True,
    help="""Downloads as mp3 (default for Youtube is m4a). Note that the
    quality of mp3 format is slightly inferior to that of m4a""",
)
def get(music_url: str, mp3: bool):
    utils.check_init()
    bb_paths = BangerBotPaths.load(BB_PATHS_FILE_PATH)
    url = utils.clean_url(music_url)
    old_files = utils.get_files(bb_paths.root)

    if "youtube.com" in url or "youtu.be" in url:
        provider = "Youtube"
        download_from_youtube(url, bb_paths.root, mp3)
    elif "soundcloud.com" in url:
        provider = "SoundCloud"
        download_from_soundcloud(url, bb_paths.root, mp3)
    else:
        print("Unsupported URL: The provided link is neither from YouTube nor SoundCloud.")
        exit(code=1)

    current_files = utils.get_files(bb_paths.root)
    new_files = [file for file in current_files if file not in old_files]

    for file in new_files:
        if file.suffix in HQ_TYPE:
            new_name = file.rename(bb_paths.hq_tracks / file.name)
        elif file.suffix in LQ_TYPE:
            new_name = file.rename(bb_paths.lq_tracks / file.name)

    utils.append_history([url], bb_paths.batch_history_file)
    print(f"Url written to {utils.ppath(bb_paths.batch_history_file)}:")

    print(f"🔥 Banger downloaded from {provider} to {utils.ppath(new_name)}")


@bangerbot.command(
    help="""Download several tracks listed in the bangers.txt.
        Provide one Youtube or Soundcloud url per line."""
)
@click.option("--mp3", is_flag=True, help="Download as MP3 (default is M4A)")
@click.option(
    "-f",
    "--from",
    "from_file",
    type=click.File("r"),
    help="""Downloads as mp3 (default is m4a). Note that the quality
        of mp3 format is slightly inferior to that of m4a""",
)
def batch(mp3, from_file):
    utils.check_init()
    bb_paths = BangerBotPaths.load(BB_PATHS_FILE_PATH)
    batch_file = Path(from_file.name) if from_file else bb_paths.batch_file
    old_files = utils.get_files(bb_paths.root)

    raw_urls = utils.get_urls_from_batch_file(batch_file)
    urls = [utils.clean_url(url) for url in raw_urls]

    print(f"{len(urls)} bangers detected. Starting downloads")

    for url in urls:
        if "youtube.com" in url or "youtu.be" in url:
            download_from_youtube(url, bb_paths.root, mp3)
        elif "soundcloud.com" in url:
            download_from_soundcloud(url, bb_paths.root, mp3)
        else:
            print(f"Unsupported URL: {url}")

    current_files = utils.get_files(bb_paths.root)
    new_files = [file for file in current_files if file not in old_files]

    new_names = []
    for file in new_files:
        if file.suffix in HQ_TYPE:
            new_names.append(file.rename(bb_paths.hq_tracks / file.name))
        elif file.suffix in LQ_TYPE:
            new_names.append(file.rename(bb_paths.lq_tracks / file.name))

    utils.append_history(urls, bb_paths.batch_history_file)

    print(f"Urls from {batch_file.name} written to {utils.ppath(bb_paths.batch_history_file)}:")
    print(f"🔥 {len(new_names)} bangers downloaded:")
    for name in new_names:
        print(utils.ppath(name))


def download_from_youtube(youtube_link: str, path: Path, mp3: bool = False):
    yt_dlp_args = ["yt-dlp", "--format", "bestaudio[ext=m4a]", youtube_link, "-P", path]
    if mp3:
        yt_dlp_args += ["--extract-audio", "--audio-format", "mp3"]

    try:
        result = subprocess.run(yt_dlp_args)
        if result.returncode == 1:
            print("Error while downloading from Youtube.")
            exit(code=1)
    except subprocess.CalledProcessError as e:
        print(f"Error downloading from YouTube: {e}")
        exit(code=1)


def download_from_soundcloud(soundcloud_link: str, path: Path, mp3: bool = False):
    scdl_args = ["scdl", "-l", soundcloud_link, "--path", path]
    if mp3:
        scdl_args.append("--onlymp3")

    try:
        result = subprocess.run(scdl_args)
        if result.returncode == 1:
            print("Error while downloading from SoundCloud.")
            exit(code=1)
    except subprocess.CalledProcessError as e:
        print(f"Error downloading from SoundCloud: {e}")


class BangerBotPaths(BaseModel):
    root: Path

    @computed_field
    @cached_property
    def hq_tracks(self) -> Path:
        return self.root / "HQ-tracks"

    @computed_field
    @cached_property
    def lq_tracks(self) -> Path:
        return self.root / "LQ-tracks"

    @computed_field
    @cached_property
    def batch_file(self) -> Path:
        return self.root / "bangers.txt"

    @computed_field
    @cached_property
    def batch_history_file(self) -> Path:
        return self.root / "bangers_history.txt"

    def create(self):
        try:
            self.root.mkdir(parents=True, exist_ok=True)
            self.hq_tracks.mkdir(parents=True, exist_ok=True)
            self.lq_tracks.mkdir(parents=True, exist_ok=True)
            self.batch_file.touch(exist_ok=True)
            self.batch_history_file.touch(exist_ok=True)
        except Exception as e:
            print(f"Error creating directories: {e}")
            exit(code=1)

    @classmethod
    def load(cls, bb_paths_file: Path):
        try:
            with open(bb_paths_file) as file:
                json_data = json.load(file)
        except FileNotFoundError:
            utils.prompt_init(utils.InitCause.NO_BB_PATHS_FILE)
            exit(code=1)

        try:
            model = cls.model_validate(json_data)
        except ValidationError:
            utils.prompt_init(utils.InitCause.BB_PATHS_FILE_CORRUPTED)
            exit(code=1)

        return model

    def save(self, bb_paths_file):
        with open(bb_paths_file, "w") as file:
            json.dump(self.model_dump(mode="json"), file, indent=4)


if __name__ == "__main__":
    bangerbot()
