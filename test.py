from lib.audio import Song, get_song_list

for i, s in enumerate(get_song_list()):
	print(i, s.get("cid"), s.get("name"))

s = Song("514533")
print("ABM_CID:", s.album_cid)
print("ABM_TIT:", s.album_title)
print("ABM_COV:", s.album_cover_url)
print("ABM_CDE:", s.album_cover_de_url)
# print("ABM_SNG:", s.album_songs)
print("SNG_CID:", s.song_cid)
print("SNG_TIT:", s.song_title)
print("SNG_AID:", s.song_album_cid)
print("SNG_URL:", s.song_url)
print("SNG_LYR:", s.lyrics_url)
print("SNG_MVC:", s.song_mv_cover_url)
print("SNG_INT:", s.song_artists)
print("SNG_POS:", s.song_position)
print("SNG_YÆR:", s.song_year)