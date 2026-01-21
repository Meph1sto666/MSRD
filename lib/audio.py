import os
import requests
import subprocess
import typing
from ffmpeg_progress_yield import FfmpegProgress
from mutagen.flac import FLAC, Picture
from mutagen.id3 import ID3
from mutagen.id3._frames import APIC, USLT
from mutagen.mp3 import MP3
from mutagen.mp4 import MP4, MP4Cover # type: ignore
from mutagen.easyid3 import EasyID3
import tqdm
import colorama

AUDIO_CACHE = "data/cache/audio/"
COVER_CACHE = "data/cache/cover/"
LYRICS_CACHE = "data/cache/lyrics/"
CONVERTED_CACHE = "data/cache/converted/"

# Check if libfdk_aac is available (which is best AAC encoder in world, but hard to install).
# pass `--with-fdk-aac` to `brew install` if you're on macOS.
def _has_libfdk_aac() -> bool:
	try:
		result = subprocess.run(["ffmpeg", "-encoders"], capture_output=True, text=True)
		return "libfdk_aac" in result.stdout
	except Exception:
		return False

_HAS_LIBFDK_AAC = _has_libfdk_aac()

FFMPEG_PRESETS: dict[str, tuple[str, list[str]]] = {
	# format: (extension, ffmpeg_options)
	"flac": (".flac", ["-compression_level", "8"]),
	"alac": (".m4a",  ["-c:a", "alac"]),
	"m4a":  (".m4a",  ["-c:a", "libfdk_aac", "-b:a", "192k"] if _HAS_LIBFDK_AAC else ["-c:a", "aac", "-b:a", "192k"]),
	"mp3":  (".mp3",  ["-c:a", "libmp3lame", "-b:a", "320k"]),
}

def _request_song_info(song_id: str|None = None) -> dict[str, typing.Any]:
	return requests.get(f"https://monster-siren.hypergryph.com/api/song/{song_id}").json()["data"]

def _request_album_info(album_id: str|None = None) -> dict[str, typing.Any]:
	return requests.get(f"https://monster-siren.hypergryph.com/api/album/{album_id}/detail").json()["data"]

def get_song_list() -> list[dict[str, typing.Any]]:
	return requests.get(f"https://monster-siren.hypergryph.com/api/songs").json()["data"].get("list")

def is_downloaded(cid: str, target_codec: str) -> bool:
	return os.path.exists(f"./{os.getenv(target_codec.upper() + '_LIBRARY_DIR')}/{cid}.{target_codec}")

class Song:
	def __init__(self, song_id: str, year_check: bool = True, target_codec: typing.Literal["flac", "alac", "m4a", "mp3"] = "flac") -> None:
		__song_dta: dict[str, typing.Any] = _request_song_info(song_id)
		__album_dta: dict[str, typing.Any] = _request_album_info(__song_dta.get("albumCid"))

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
		self.song_year: int = self.__get_song_year() if year_check else -1
		# self.album_artists: int = self.__yt_get_album_artists() if year_check else -1

		# === CODECS ===
		self.__target_codec: typing.Literal['flac', 'alac', 'm4a', 'mp3'] = target_codec
		self.__target_ext: str = FFMPEG_PRESETS[target_codec][0]
		self.__audio_codec: str | None = os.path.splitext(self.song_url)[1] if self.song_url else None
		self.__cover_codec: str = os.path.splitext(self.song_mv_cover_url or self.album_cover_url)[1]
		self.__lyrics_ext: str | None = os.path.splitext(self.lyrics_url)[1] if self.lyrics_url else None

	def is_downloaded(self) -> bool:
		return os.path.exists(f"./{os.getenv(self.__target_codec.upper() + '_LIBRARY_DIR')}/{self.song_cid}{self.__target_ext}")

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

	def convert(self) -> None:
		os.makedirs(CONVERTED_CACHE, exist_ok=True)
		in_path: str = f"{AUDIO_CACHE}{self.song_cid}{self.__audio_codec}"
		ext, opts = FFMPEG_PRESETS[self.__target_codec]
		cmd: list[str] = ["ffmpeg", "-i", in_path, *opts, f"{CONVERTED_CACHE}{self.song_cid}{ext}", "-y"]
		progress_iterator: typing.Iterator[float] = FfmpegProgress(cmd).run_command_with_progress() # type: ignore
		pbar = tqdm.tqdm(progress_iterator, total=100, desc=f"Converting [{self.song_cid}]", ascii=".#", unit_scale=True, leave=False)
		if self.__audio_codec not in [".flac", ".wav"]:
			pbar.write(f"{colorama.Fore.LIGHTBLUE_EX}INFO{colorama.Fore.RESET}: [{self.song_cid}] {colorama.Fore.LIGHTRED_EX}ORIGINAL IS NOT LOSSLESS{colorama.Fore.RESET}")
		list(pbar)

	def add_metadata_flac(self) -> None:
		pbar = tqdm.tqdm(total=1, desc=f"Adding metadata [{self.song_cid}]", ascii=".#", leave=False)
		cover = Picture()
		audio_file: FLAC = FLAC(f"{CONVERTED_CACHE}{self.song_cid}.flac") # type: ignore
		with open(f"{COVER_CACHE}{self.song_cid}{self.__cover_codec}", "rb") as f:
			cover.data = f.read()
		audio_file["title"] = self.song_title
		audio_file["artist"] = " & ".join(self.song_artists)
		# audio_file["album_artist"] = " & ".join(self.album_artists)
		audio_file["album"] = self.album_title
		audio_file["date"] = str(self.song_year) if self.song_year > 0 else "Unknown"
		audio_file["tracknumber"] = str(self.song_position)
		if self.lyrics_url:
			lrc_path: str = f"{LYRICS_CACHE}{self.song_cid}{self.__lyrics_ext}"
			audio_file["LYRICS"] = open(lrc_path, 'r', encoding='utf-8').read()
		audio_file.add_picture(cover) # type: ignore
		audio_file.save() # type: ignore
		pbar.close()

	def add_metadata_m4a(self) -> None:
		pbar = tqdm.tqdm(total=1, desc=f"Adding metadata [{self.song_cid}]", ascii=".#", leave=False)
		audio_file: MP4 = MP4(f"{CONVERTED_CACHE}{self.song_cid}{self.__target_ext}") # type: ignore
		with open(f"{COVER_CACHE}{self.song_cid}{self.__cover_codec}", "rb") as f:
			audio_file["covr"] = [MP4Cover(f.read())]
		audio_file["\xa9nam"] = self.song_title
		audio_file["\xa9ART"] = " & ".join(self.song_artists)
		# audio_file["aART"] = " & ".join(self.album_artists)
		audio_file["\xa9alb"] = self.album_title
		audio_file["\xa9day"] = str(self.song_year) if self.song_year > 0 else "Unknown"
		audio_file["trkn"] = [(self.song_position, len(self.album_songs))]
		if self.lyrics_url:
			lrc_path: str = f"{LYRICS_CACHE}{self.song_cid}{self.__lyrics_ext}"
			audio_file["\xa9lyr"] = open(lrc_path, 'r', encoding='utf-8').read()
		audio_file.save() # type: ignore
		pbar.close()

	def add_metadata_mp3(self) -> None:
		pbar = tqdm.tqdm(total=1, desc=f"Adding metadata [{self.song_cid}]", ascii=".#", leave=False)

		audio_path: str = f"{CONVERTED_CACHE}{self.song_cid}{self.__target_ext}"
		with open(f"{COVER_CACHE}{self.song_cid}{self.__cover_codec}", "rb") as f:
			audio_file_cvr: MP3 = MP3(audio_path, ID3=ID3) # type: ignore
			audio_file_cvr.tags.add(APIC(mime=f'image/{"png" if self.__cover_codec == ".png" else "jpeg"}', type=3, desc=u'Cover', data=f.read())) # type: ignore
			audio_file_cvr.save() # type: ignore

		audio_file = EasyID3(audio_path)
		audio_file["title"] = self.song_title
		audio_file["artist"] = " & ".join(self.song_artists)
		# audio_file["albumartist"] = " & ".join(self.album_artists)
		audio_file["album"] = self.album_title
		audio_file["date"] = str(self.song_year) if self.song_year > 0 else "Unknown"
		audio_file["tracknumber"] = [(self.song_position, len(self.album_songs))]
		if self.lyrics_url:
			lrc_path: str = f"{LYRICS_CACHE}{self.song_cid}{self.__lyrics_ext}"
			tag = ID3(audio_path)
			# tag.setall("SYLT", [SYLT(encoding=3, lang="eng", format=2, type=1, text=open(lrc_path, 'r', encoding='utf-8').read())]) # type: ignore
			tag.setall("USLT", [USLT(encoding=3, format=2, type=1, text=open(lrc_path, 'r', encoding='utf-8').read())]) # type: ignore
			tag.save() # type: ignore
		audio_file.save() # type: ignore
		pbar.close()

	def full_download(self) -> None:
		self.download_song()
		self.download_cover()
		self.download_lyrics()
		self.convert()
		metadata_method = "m4a" if self.__target_codec == "alac" else self.__target_codec
		getattr(self, f"add_metadata_{metadata_method}")()
		os.makedirs(f"./{os.getenv(self.__target_codec.upper() + '_LIBRARY_DIR')}/", exist_ok=True)
		os.replace(f"./{CONVERTED_CACHE}{self.song_cid}{self.__target_ext}", f"./{os.getenv(self.__target_codec.upper() + '_LIBRARY_DIR')}/{self.song_cid}{self.__target_ext}")

	def full_convert(self) -> bool:
		if not self.is_cached():
			return False
		self.convert()
		metadata_method = "m4a" if self.__target_codec == "alac" else self.__target_codec
		getattr(self, f"add_metadata_{metadata_method}")()
		os.makedirs(f"./{os.getenv(self.__target_codec.upper() + '_LIBRARY_DIR')}/", exist_ok=True)
		os.replace(f"./{CONVERTED_CACHE}{self.song_cid}{self.__target_ext}", f"./{os.getenv(self.__target_codec.upper() + '_LIBRARY_DIR')}/{self.song_cid}{self.__target_ext}")
		return True

	def is_cached(self) -> bool:
		return os.path.exists(f"{AUDIO_CACHE}{self.song_cid}{self.__audio_codec}")

	def __get_song_position(self) -> int:
		for i, song in enumerate(self.album_songs):
			if song.get("cid") == self.song_cid:
				return i+1
		return -1

	def __get_song_year(self) -> int:
		assert self.song_url
		return int(self.song_url.split("siren/audio/")[1].split("/")[0][0:4])

	# def __yt_get_album_artists(self) -> None:
	# 	return
	# 	search_res:list[dict[str, typing.Any]] = YTM.search(self.song_title, limit=1) # type: ignore
