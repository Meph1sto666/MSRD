# MSRD, a 3rd-party tool to download the Arknights OST from the official MSR [website](https://monster-siren.hypergryph.com/)

## Requirements
- Python (3.10.6 tested, other versions probably work just as fine)
- [FFmpeg](https://github.com/BtbN/FFmpeg-Builds/releases), installed and in system PATH

If you have already installed Python and FFmpeg skip to the [setup](#set-up)
### Install Python

Download python 3.10.6 [here](https://www.python.org/downloads/release/python-3106/) and run the installer.
>! Make sure to check the "Add to PATH" checkbox

### Install FFmpeg
Follow for example [these instructions](https://phoenixnap.com/kb/ffmpeg-windows) on how to set up FFmpeg on your system.

## Set-up

1. [Download](https://github.com/Meph1sto666/MSRD/archive/refs/heads/main.zip) and extract the zip file
2. Go into the MSRD folder and execute the `setup.bat` file (or follow the [contributing instructions](#contributing) 3 to 5)
3. Close the window

## Use it

1. Run `msrd.bat` this will open a new console in which you can use the downloader.
2. To see the commands type `python msrd.py --help` and run it. This will show a small help menu.

Example commands are
- `python msrd.py download 232244 953983` Download the song with the ID `232244` and `953983`
- `python msrd.py download -a -t 2` Download all songs with two threads.
- `python msrd.py cache clear audio` Clear/delete the audio files the program worked with (don't worry the finished songs will not be deleted).

If you have a slow drive or internet I recommend limiting the threads depending on your specs.
> Downloading the entire Discography (as of 2024.09.12, 598 songs) at 55Mb/s with 16 threads took 58min.

## Contributing

Contributions and improvements are very welcome.

1. Fork the repo
2. Make sure you are on the dev branch `git checkout dev`
3. Create the virtual environment `python -m venv venv`
4. Activate it `venv\Scripts\activate`
5. Install the requirements `pip install -r requirements.txt`
6. Make your changes
7. Pull requests should as well be on a separate branch like _dev_

> _This project is not affiliated with Hypergryph, Studio Montagne, Yostar or Gryphline in any ways._