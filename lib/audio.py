import os
import requests
import re
import json
import typing
import ytmusicapi # type: ignore
from datetime import datetime as dt
# from ffmpeg.ffmpeg import FFmpeg # type: ignore
from ffmpeg_progress_yield import FfmpegProgress
from mutagen.flac import FLAC, Picture
import tqdm
import colorama
YTM:ytmusicapi.YTMusic = ytmusicapi.YTMusic()

AUDIO_CACHE = "data/cache/audio/"
COVER_CACHE = "data/cache/cover/"
LYRICS_CACHE = "data/cache/lyrics/"
CONVERTED_CACHE = "data/cache/converted/"

def _request_song_info(song_id: str|None = None) -> dict[str, typing.Any]:
	res: str = requests.get(f"https://monster-siren.hypergryph.com/{'music/'+song_id if song_id else ''}").text
	data: re.Match[str]|None = re.search(r"(?<=window\.g_initialProps = )[\s\S]+(?=;\n\s*<\/script>)", res, flags = re.UNICODE)
	if data is None:
		raise Exception("Failed to retrieve song informations")
	converted_data: str = re.sub(r"(?<=:)undefined(?=,)", "\"none\"", data.group()) # convert "undefined" to "none" cuz we don't like JS /s
	return json.loads(converted_data)

def get_song_list() -> list[dict[str, typing.Any]]:
	song_list: list[dict[str, typing.Any]] = _request_song_info().get("player", {}).get("list", [])
	if len(song_list) < 1:
		raise Exception("No songs found in list")
	return song_list

def is_downloaded(cid: str) -> bool:
	return os.path.exists(f"{os.getenv('LIBRARY_DIR')}/{cid}.flac")

class Song:
	def __init__(self, song_id: str, year_check: bool = True) -> None:
		self.song_data:dict[str, typing.Any] = _request_song_info(song_id)
		__song_dta: dict[str, typing.Any] = self.song_data.get("player", {}).get("songDetail", {})
		__album_dta: dict[str, typing.Any] = self.song_data.get("musicPlay", {}).get("albumDetail", {})

		# === ALBUM DATA ===
		self.album_cid: str = __album_dta.get("cid", "NONE")
		self.album_title: str = __album_dta.get("name", "NONE")
		self.album_cover_url: str = __album_dta.get("coverUrl", "NONE")
		self.album_cover_de_url: str = __album_dta.get("coverDeUrl", "NONE")
		self.album_songs: list[dict[str, str]] = __album_dta.get("songs", "NONE")

		# === SONG DATA ===
		self.song_cid: str = __song_dta.get("cid", "NONE")
		self.song_title: str = __song_dta.get("name", "NONE")
		self.song_album_cid: str = __song_dta.get("albumCid", "NONE")
		self.song_url: str | None = __song_dta.get("sourceUrl")
		self.lyrics_url: str | None = __song_dta.get("lyricUrl")
		self.song_mv_cover_url: str | None = __song_dta.get("mvCoverUrl")
		self.song_artists: list[str] = __song_dta.get("artists", [])
		self.song_position: int = self.__get_song_position()

		# === YTM DATA ===
		self.song_year: int = self.__yt_get_song_year() if year_check else -1
		# self.album_artists: int = self.__yt_get_album_artists() if year_check else -1
		
		# === CODECS ===
		self.__audio_codec: str | None = os.path.splitext(self.song_url)[1] if self.song_url else None
		self.__cover_codec: str = os.path.splitext(self.song_mv_cover_url or self.album_cover_url)[1]		
		self.__lyrics_ext: str | None = os.path.splitext(self.lyrics_url)[1] if self.lyrics_url else None

	def is_downloaded(self) -> bool:
		return os.path.exists(f"{os.getenv('LIBRARY_DIR')}/{self.song_cid}.flac")

	def download_song(self) -> None:
		if not self.song_url:
			raise Exception("song URL is None")
		path: str = f"{AUDIO_CACHE}{self.song_cid}{self.__audio_codec}"
		os.makedirs(AUDIO_CACHE, exist_ok=True)
		with open(path, 'wb') as audio_file:
			audio_stream: requests.Response = requests.get(self.song_url, stream=True)
			pbar = tqdm.tqdm(unit="B", total=int(audio_stream.headers['Content-Length']), desc=f"Downloading [{self.song_cid}{self.__audio_codec}]", ascii=".#", unit_scale=True, leave=False) # , bar_format="{rate} {elapsed} {desc} |{bar}| {percentage:.2f}%"
			for c in audio_stream.iter_content(chunk_size=1024):
				pbar.update(len(c))
				audio_file.write(c)

	def download_cover(self) -> None:
		path: str = f"{COVER_CACHE}{self.song_cid}{self.__cover_codec}"
		os.makedirs(COVER_CACHE, exist_ok=True)
		with open(path, 'wb') as cover_file:
			cover_stream: requests.Response = requests.get(self.song_mv_cover_url or self.album_cover_url, stream=True)
			pbar = tqdm.tqdm(unit="B", total=int(cover_stream.headers['Content-Length']), desc=f"Downloading [{self.song_cid}{self.__cover_codec}]", ascii=".#", unit_scale=True, leave=False) # , bar_format="{rate} {elapsed} {desc} |{bar}| {percentage:.2f}%"
			for c in cover_stream.iter_content(chunk_size=1024):
				pbar.update(len(c))
				cover_file.write(c)

	def download_lyrics(self) -> None:
		if not self.lyrics_url:
			return
		path: str = f"{LYRICS_CACHE}{self.song_cid}{self.__lyrics_ext}"
		os.makedirs(LYRICS_CACHE, exist_ok=True)
		with open(path, 'wb') as lrc_file:
			lrc_stream: requests.Response = requests.get(self.lyrics_url, stream=True)
			pbar = tqdm.tqdm(unit="B", total=int(lrc_stream.headers['Content-Length']), desc=f"Downloading [{self.song_cid}{self.__lyrics_ext}]", ascii=".#", unit_scale=True, leave=False) # , bar_format="{rate} {elapsed} {desc} |{bar}| {percentage:.2f}%"
			for c in lrc_stream.iter_content(chunk_size=1024):
				pbar.update(len(c))
				lrc_file.write(c)

	def convert_to_flac(self) -> None:
		os.makedirs(CONVERTED_CACHE, exist_ok=True)
		in_path: str = f"{AUDIO_CACHE}{self.song_cid}{self.__audio_codec}"
		# FFmpeg().option("y").input(in_path).output(f"{CONVERTED_CACHE}{self.song_cid}.flac").execute() # type: ignore
		cmd: list[str] = ["ffmpeg", f"-i", in_path, f"{CONVERTED_CACHE}{self.song_cid}.flac", "-y"]
		progress_iterator: typing.Iterator[float] = FfmpegProgress(cmd).run_command_with_progress() # type: ignore
		pbar = tqdm.tqdm(progress_iterator, total=100, desc=f"Converting [{self.song_cid}]", ascii=".#", unit_scale=True, leave=False)
		if self.__audio_codec not in [".flac", ".wav"]:
			pbar.write(f"{colorama.Fore.LIGHTBLUE_EX}INFO{colorama.Fore.RESET}: [{self.song_cid}] {colorama.Fore.LIGHTRED_EX}ORIGINAL IS NOT LOSSLESS{colorama.Fore.RESET}")
			# pbar.colour = "#ff0000"
		list(pbar)
		# for p in progress_iterator:
		# 	pbar.update(p)
		# pbar.close()

	def add_metadata(self) -> None:
		operations: int = 8 + (1 if self.lyrics_url else 0)
		pbar = tqdm.tqdm(total=operations, desc=f"Adding metadata [{self.song_cid}]", ascii=".#", leave=False)
		cover = Picture()
		audio_file: FLAC = FLAC(f"{CONVERTED_CACHE}{self.song_cid}.flac") # type: ignore
		pbar.update()
		with open(f"{COVER_CACHE}{self.song_cid}{self.__cover_codec}", "rb") as f:
			cover.data = f.read()
		audio_file["title"] = self.song_title
		pbar.update()
		audio_file["artist"] = " & ".join(self.song_artists)
		pbar.update()
		# audio_file["album_artist"] = " & ".join(self.album_artists)
		audio_file["album"] = self.album_title
		pbar.update()
		audio_file["date"] = str(self.song_year) if self.song_year > 0 else "Unknown"
		pbar.update()
		audio_file["tracknumber"] = str(self.song_position)
		pbar.update()
		if self.lyrics_url:
			lrc_path: str = f"{LYRICS_CACHE}{self.song_cid}{self.__lyrics_ext}"
			audio_file["LYRICS"] = open(lrc_path, 'r', encoding='utf-8').read()
			pbar.update()
		# audio_file["genre"] = "Unknown" # TODO: get genre from YTM API or MusicBrainz
		audio_file.add_picture(cover) # type: ignore
		pbar.update()
		audio_file.save() # type: ignore
		pbar.close()

	def full_download(self) -> None:
		jobs: list[typing.Callable[[], None]] = [self.download_song, self.download_cover, self.download_lyrics, self.convert_to_flac, self.add_metadata]
		for j in jobs:
			j()
		os.replace(f"./{CONVERTED_CACHE}{self.song_cid}.flac", f"./{os.getenv('LIBRARY_DIR')}/{self.song_cid}.flac")

	def __get_song_position(self) -> int:
		for i, song in enumerate(self.album_songs):
			if song.get("cid") == self.song_cid:
				return i+1
		return -1

	def __yt_get_song_year(self) -> int:
		search_res:list[dict[str, typing.Any]] = YTM.search(f"{self.song_title} - {self.song_artists[0] if len(self.song_artists)>0 else '塞壬唱片-MSR'}", limit=1, filter="songs") # type: ignore
		try:
			return dt.fromisoformat(YTM.get_song(search_res[0].get("videoId"))["microformat"]["microformatDataRenderer"]["uploadDate"]).year # type: ignore
		except:
			return -1

	# def __yt_get_album_artists(self) -> None:
	# 	return
	# 	search_res:list[dict[str, typing.Any]] = YTM.search(self.song_title, limit=1) # type: ignore
		
