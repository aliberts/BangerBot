# Banger Bot

Get those bangers banging 🔥

## Installation

### 1. Install pipx

If you don't have it, install [pipx](https://github.com/pypa/pipx)

#### MacOS

```bash
brew install pipx
pipx ensurepath
```

#### Linux

```bash
python3 -m pip install --user pipx
python3 -m pipx ensurepath
```

### 2. Install BangerBot

```bash
pipx install bangerbot
pipx inject --include-apps bangerbot scdl yt-dlp
```

### 3. Run init

Follow the prompt to setup the folder used by BangerBot

```bash
banger init
```

## Use BangerBot

### get

Download a banger.

```bash
banger get https://soundcloud.com/fc_kabagar/kylie-on-jersey
```

### batch

Download multiples bangers at once.
Simply put your tracks url inside `bangers.txt` (1 url per line) and run a batch:

```bash
banger batch
```

The default location for `bangers.txt` is `~/Music/bangerbot/bangers.txt`
but you can point to any file you like using the `-f` option.

```bash
banger batch -f ~/Music/some_more_bangers.txt
```

## Supported urls

For now, BangerBot only supports SoundClound and Youtube urls

## Roadmap

[x] Support Youtube and SoundCloud urls
[ ] Shell completion
[ ] Add metadata to downloaded tracks

## Disclaimer

This tool is intended to get tracks when they are made available freely by the publisher.
Don't use it if you don't have permission
Do not use this tool to steal artists and music producers work, seriously.
