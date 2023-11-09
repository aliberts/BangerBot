import importlib.resources
from importlib.metadata import version
from pathlib import Path

import bangerbot

BB_PATHS_FILE = Path("bb_paths.json")


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
