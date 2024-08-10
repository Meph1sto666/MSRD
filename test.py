import tqdm.utils
from lib.audio import Song, get_song_list
import concurrent.futures
import tqdm
import typing

def download_audio(cid: str) -> None:
	s = Song(cid)
	s.full_download()

def interp(x: float, x1: float, x2: float, y1: float, y2: float) -> float:
		return y1+((y2-y1)/(x2-x1))*(x-x1)

jobs: list[typing.Any | None] = [(s.get("cid")) for s in get_song_list()[::-1]]
with concurrent.futures.ThreadPoolExecutor() as exector:
	workers: typing.Iterator[None] = exector.map(download_audio, jobs)
	pbar = tqdm.tqdm(workers, total=len(jobs), position=0, ascii=".#", colour="#00ff00")
	# for i, w in enumerate(workers):
	# 	pbar.update(i)
	list(pbar)