import importlib.resources
import shutil
import subprocess
from enum import Enum
from importlib.metadata import version
from pathlib import Path

import bangerbot

BB_PATHS_FILE = Path("bb_paths.json")


class InitCause(Enum):
    NO_DEPENDENCIES = 0
    NO_BB_PATHS_FILE = 1
    BB_PATHS_FILE_CORRUPTED = 2


def get_bb_paths_file_path() -> Path:
    return importlib.resources.files(bangerbot.__name__) / BB_PATHS_FILE


def get_bb_version() -> str:
    return ".".join(version(bangerbot.__name__).split(".")[:3])


def clean_url(url: str):
    return url.strip().split("&")[0]


def ppath(path: Path) -> Path:
    try:
        sub_path = path.relative_to(Path.home())
        return "~" / sub_path
    except ValueError:
        return path


def get_urls_from_batch_file(batch_file: Path) -> list[str]:
    try:
        with open(batch_file) as file:
            urls = file.readlines()
    except FileNotFoundError:
        print(
            f"File '{ppath(batch_file)}' not found. Create the file with a list of URLs to download."
        )
        exit(code=1)
    return urls


def get_files(bb_root_path: Path) -> list[Path]:
    return [x for x in bb_root_path.glob("*") if x.is_file()]


def append_history(urls: list[str], batch_history_file_path: Path):
    with open(batch_history_file_path, "a") as history:
        for url in urls:
            history.write(url + "\n")


def check_init() -> None:
    scdl = shutil.which("scdl")
    yt_dlp = shutil.which("yt-dlp")
    if not (scdl and yt_dlp):
        prompt_init(InitCause.NO_DEPENDENCIES)
        exit(code=1)

    bb_paths_file = get_bb_paths_file_path()
    if not bb_paths_file.is_file():
        prompt_init(InitCause.NO_BB_PATHS_FILE)
        exit(code=1)


def prompt_init(cause: InitCause):
    if cause is InitCause.NO_DEPENDENCIES:
        msg = "No dependencies found"
    if cause is InitCause.NO_BB_PATHS_FILE:
        msg = "Config file not found"
    if cause is InitCause.BB_PATHS_FILE_CORRUPTED:
        msg = "Config file corrupted"
    print(f"{msg}. Run 'banger init' first.")


def install_pipx_dependency(dependency_name: str) -> None:
    args = ["pipx", "inject", "--include-apps", "bangerbot", dependency_name]
    try:
        print(f"Installing {dependency_name}")
        result = subprocess.run(args)
        if result.returncode == 1:
            print("Error while installing dependencies")
            exit(code=1)
    except subprocess.CalledProcessError as e:
        print(f"Error while installing dependencies: {e}")
        exit(code=1)
