## Requirements 
if you haven't already install [scoop](https://scoop.sh/) and run the following
```
scoop install git ffmpeg python310
```
> alternatively you can use [uv](https://docs.astral.sh/uv/) to manage python for you; also available on scoop.
scoop manages path for you.

## Setup
clone the repo

```
git clone https://github.com/Meph1sto666/MSRD
```
cd into it
```
cd MSRD
```
and run ``setup.bat``
```
.\setup.bat
```

## Usage
To see the commands type `python msrd.py --help` and run it. This will show a small help menu.

Example commands are
- `python msrd.py download 232244 953983` Download the song with the ID `232244` and `953983`
- `python msrd.py download 953986 --format=m4a` Download the song with the ID `953986` as m4a
- `python msrd.py convert -a --format=mp3` Convert songs to mp3.
- `python msrd.py convert -a -d --format=alac` Convert songs (and re-download them if the cache has been cleared) to alac.
- `python msrd.py download -a -t 2` Download all songs with two threads. (good for lower end macines or slower internet)
- `python msrd.py cache clear audio` Clear/delete the audio files the program worked with (don't worry the finished songs will not be deleted).

> Downloading the entire Discography (as of 2024.09.12, 598 songs) at 55Mb/s with 16 threads took 58min.
