import requests
import re
import json
import typing
import ytmusicapi # type: ignore
from datetime import datetime as dt

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

class Song:
	def __init__(self, song_id: str, year_check: bool = True) -> None:
		self.song_data:dict[str, typing.Any] = _request_song_info(song_id)
		__song_dta: dict[str, typing.Any] = self.song_data.get("player", {}).get("songDetail", {})
		__album_dta: dict[str, typing.Any] = self.song_data.get("musicPlay", {}).get("albumDetail", {})

		self.album_cid: str = __album_dta.get("cid", "NONE")
		self.album_title: str = __album_dta.get("name", "NONE")
		self.album_cover_url: str = __album_dta.get("coverUrl", "NONE")
		self.album_cover_de_url: str = __album_dta.get("coverDeUrl", "NONE")
		self.album_songs: list[dict[str, str]] = __album_dta.get("songs", "NONE")
		# print(self.album_title, self.album_cover_url, self.album_songs)

		self.song_cid: str = __song_dta.get("cid", "NONE")
		self.song_title: str = __song_dta.get("name", "NONE")
		self.song_album_cid: str = __song_dta.get("albumCid", "NONE")
		self.song_url: str = __song_dta.get("sourceUrl", "NONE")
		self.lyrics_url: str = __song_dta.get("lyricUrl", "NONE")
		self.song_mv_cover_url: str = __song_dta.get("mvCoverUrl", "NONE")
		self.song_artists: list[str] = __song_dta.get("artists", [])
		self.song_position: int = self.__get_song_position()
		self.song_year: int = self.__get_song_year() if year_check else -1
		# print(self.song_cid, self.song_title, self.song_url, self.lyrics_url, self.song_mv_cover_url, self.song_artists, self.song_position, self.song_year)		

	def __get_song_position(self) -> int:
		for i, song in enumerate(self.album_songs):
			if song.get("cid") == self.song_cid:
				return i+1
		return -1

	def __get_song_year(self) -> int:
		ytm:ytmusicapi.YTMusic = ytmusicapi.YTMusic()
		search_res:list[dict[str, typing.Any]] = ytm.search(self.song_title, limit=1) # type: ignore
		return dt.fromisoformat(ytm.get_song(search_res[0].get("videoId"))["microformat"]["microformatDataRenderer"]["uploadDate"]).year # type: ignore