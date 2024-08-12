import tqdm.utils
import typer.rich_utils
from lib.audio import Song, get_song_list
import concurrent.futures
import tqdm
import typing
import typer
from dotenv import load_dotenv
from typing_extensions import Annotated, Optional
from lib.commands import cache as cache_command
import typer.core

load_dotenv()

cli = typer.Typer()
# typer.core.rich = None

def download_audio(cid: str) -> None:
	s = Song(cid)
	s.full_download()

@cli.command()
def download(
		ids: Annotated[Optional[list[str]], typer.Argument(help="Download the specified songs by their ID (format: ID1 ID2 ID3...)")] = None,
		dw_all: Annotated[Optional[bool], typer.Option("--all", "-a", help="Download the entire discography of MSR.")] = False,
		threads: Annotated[Optional[int], typer.Option("--threads", "-t", help="Specify the maximum amount of parallel downloads")] = None) -> None:
	if not ids and not dw_all:
		typer.pause(f"Please specify the song(s) you want to download. Press any key to continue...")
		return
	jobs: list[typing.Any | None] = []
	if dw_all:
		jobs = [(s.get("cid")) for s in get_song_list()[::-1]]
	else:
		assert ids is not None
		jobs = ids
	with concurrent.futures.ThreadPoolExecutor(max_workers=threads) as executor:
		workers: typing.Iterator[None] = executor.map(download_audio, jobs)
		p_bar = tqdm.tqdm(workers, total=len(jobs), position=0, ascii=".#", colour="#00ff00")
		list(p_bar)
		print(f"Download of {p_bar.n} song{'s' if p_bar.n != 1 else ''} finished in {p_bar.format_dict['elapsed']} seconds")

cli.add_typer(cache_command.cli, name="cache")

if __name__ == "__main__":
	cli()