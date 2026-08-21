# Video Downloader Project

A small Python project that downloads videos from YouTube, Instagram, and Facebook links,
built as a teaching project for a 2nd-year B.Tech Python class. It comes in two forms that
share the exact same core logic:

- **`downloader.py`** -- a plain terminal script, run with `python downloader.py`.
- **`notebooks/video_downloader.ipynb`** -- the same project as an interactive Jupyter
  notebook with buttons and an upload widget.

Both pick a destination folder, read a list of links, detect the platform automatically,
try to keep files under a target size, and always save the final file as `.mp4`. Full
explanation of *why* the project is built this way -- the real-world problem it solves,
and a walkthrough of every function -- is in [`docs/field_guide.pdf`](docs/field_guide.pdf).

Code comments throughout are in Hinglish (simple English + everyday Hindi), written so a
student who has never seen a particular Python feature or library function before can
still follow along line by line.

## Project structure

```
video-downloader-project/
├── README.md                      <- you are here
├── requirements.txt                <- Python packages to install
├── .gitignore
├── downloader.py                   <- run this from a terminal
├── notebooks/
│   └── video_downloader.ipynb      <- run this in Jupyter
├── docs/
│   └── field_guide.pdf             <- full explanation + storytelling walkthrough
├── sample_links.txt                <- example input file (one link per line)
└── downloads/                      <- videos + summary reports land here (empty in git)
```

## Requirements

- **Python 3.8 or newer.** Check your version with `python --version` (or `python3 --version`
  on Mac/Linux).
- **ffmpeg**, installed separately from Python -- see below. `yt-dlp` uses it to guarantee the
  final file is a proper `.mp4`, even when the source site serves video and audio as two
  separate streams that need to be merged.
- The Python packages listed in `requirements.txt` (just `yt-dlp` for the script; add
  `ipywidgets` and `jupyterlab` if you also want to run the notebook).

Nothing else is required for `downloader.py` itself -- every other import it uses
(`os`, `re`, `sys`, `json`, `argparse`, `traceback`, `datetime`, `urllib.parse`) is part of
Python's standard library and needs no installation.

## Installation

**1. Clone the repository and move into it:**

```bash
git clone <your-repo-url>
cd video-downloader-project
```

**2. (Recommended) Create and activate a virtual environment**, so these packages don't mix
with anything else on your system:

```bash
python -m venv venv

# Windows:
venv\Scripts\activate

# Mac/Linux:
source venv/bin/activate
```

**3. Install the Python packages:**

```bash
pip install -r requirements.txt
```

**4. Install ffmpeg** (not a Python package, so `pip` cannot install it):

- **Windows:** open PowerShell or Command Prompt and run `winget install ffmpeg`.
  If `winget` isn't available (older Windows), download a build from
  [ffmpeg.org](https://ffmpeg.org/download.html), unzip it somewhere like `C:\ffmpeg`, then add
  `C:\ffmpeg\bin` to your System PATH (Settings -> search "Environment Variables" -> edit the
  `Path` variable -> add that folder). Open a **new** terminal window afterwards.
- **Mac:** `brew install ffmpeg` (needs [Homebrew](https://brew.sh) installed first).
- **Linux (Debian/Ubuntu):** `sudo apt update && sudo apt install ffmpeg`.
  Other distros: `sudo dnf install ffmpeg` (Fedora) or `sudo pacman -S ffmpeg` (Arch).

Confirm it worked by closing and reopening your terminal, then running `ffmpeg -version` -- if
you see a version number and build info, you're set. If it says "command not found" / "not
recognized," the PATH step above didn't take effect -- this is the most common sticking point,
especially on Windows.

> **Note for running this in class:** ffmpeg installation is the step most likely to trip up a
> few students (Windows PATH issues especially). Consider having them install it *before* class,
> or budgeting a few extra minutes for it during the session.

## Usage

### Option A: terminal script

Guided mode (it will ask you for a destination folder and a links file):

```bash
python downloader.py
```

Non-interactive mode, useful for scripting or quick reruns:

```bash
python downloader.py --dest ./downloads --links sample_links.txt
```

The first time you confirm a destination folder, you'll be asked whether to save it as your
default -- say yes and future runs can skip that prompt with a blank Enter.

### Option B: Jupyter notebook

```bash
jupyter lab notebooks/video_downloader.ipynb
```

Run the cells top to bottom, confirm your destination folder in the "Choose your destination
folder" section, then upload a `.txt` file of links and click **Start**.

### Links file format

One link per line, plain text, e.g. `sample_links.txt`:

```
https://www.youtube.com/watch?v=XXXXXXXXXXX
https://www.instagram.com/reel/XXXXXXXXXXX/
```

Blank lines are ignored.

## Output

Downloaded videos and a timestamped `download_summary_<date>_<time>.txt` report are written
into your chosen destination folder (`downloads/` by default). The summary lists every link,
whether it succeeded or failed, and -- for failures -- the reason, so a failed run is never a
dead end.

## Troubleshooting

- **"ffmpeg not found" / merging errors:** ffmpeg isn't installed or isn't on your PATH --
  see step 4 above, then open a new terminal.
- **Download fails with a network/proxy error:** check your internet connection; some college
  or hostel networks block video-hosting domains outright.
- **"No formats found" for a link:** the video may be private, age-restricted, or removed --
  try the link in a normal browser first to confirm it's public and working.
- **`yt-dlp` errors that mention an outdated version:** run `pip install -U yt-dlp` -- sites
  change frequently and `yt-dlp` ships fixes often.

## License

Add a license of your choice here (e.g. MIT) before making the repository public.

## Credits

Built as a class project for a 2nd-year B.Tech Python course. Powered by
[`yt-dlp`](https://github.com/yt-dlp/yt-dlp).
