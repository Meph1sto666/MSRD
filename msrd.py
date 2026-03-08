from time import sleep
import tqdm.utils
import typer.rich_utils
from lib.audio import Song, get_song_list, is_downloaded
import concurrent.futures
import tqdm
import typing
import typer
from dotenv import load_dotenv
from typing_extensions import Annotated, Optional
from lib.commands import cache as cache_command
import typer.core
import colorama

DOWNLOAD_RETRIES: int = 10
load_dotenv()

cli = typer.Typer(no_args_is_help=True)
# typer.core.rich = None


def download_audio(
    cid: str, codec: typing.Literal["flac", "m4a", "mp3"] = "flac"
) -> None:
    for i in range(DOWNLOAD_RETRIES):
        try:
            s = Song(cid, target_codec=codec)
            s.full_download()
            break
        except:
            sleep(2**i)


def convert_audio(
    cid: str,
    codec: typing.Literal["flac", "m4a", "mp3"] = "flac",
    allow_download: bool = False,
) -> None:
    s = Song(cid, target_codec=codec)
    if not s.full_convert() and allow_download:
        s.full_download()


@cli.command(help="Download music", no_args_is_help=True)
def download(
    ids: Annotated[
        Optional[list[str]],
        typer.Argument(
            help="Download the specified songs by their ID (format: ID1 ID2 ID3...)"
        ),
    ] = None,
    dw_all: Annotated[
        Optional[bool],
        typer.Option("--all", "-a", help="Download the entire discography of MSR."),
    ] = False,
    force: Annotated[
        Optional[bool],
        typer.Option("--force", "-f", help="Overwrite already downloaded files"),
    ] = False,
    threads: Annotated[
        Optional[int],
        typer.Option(
            "--threads", "-t", help="Specify the maximum amount of parallel downloads"
        ),
    ] = None,
    as_mp3: Annotated[
        Optional[bool],
        typer.Option(
            "--mp3", help="Convert to MP3 instead of FLAC, cannot be used with --m4a"
        ),
    ] = False,
    as_m4a: Annotated[
        Optional[bool],
        typer.Option(
            "--m4a", help="Convert to M4A instead of FLAC, cannot be used with --mp3"
        ),
    ] = False,
) -> None:
    if as_m4a and as_mp3:
        typer.echo("Cannot use both --mp3 and --m4a flags together", err=True)
        exit()
    elif as_m4a:
        codec = "m4a"
    elif as_mp3:
        codec = "mp3"
    else:
        codec = "flac"
    if not ids and not dw_all:
        typer.pause(
            f"Please specify the song(s) you want to download. Press any key to continue..."
        )
        return
    jobs: list[typing.Any | None] = []
    if dw_all:
        for s in get_song_list()[::-1]:
            cid: str | None = s.get("cid")
            if not force and (not cid or is_downloaded(cid, codec)):
                print(
                    f"{colorama.Fore.LIGHTBLUE_EX}INFO{colorama.Fore.RESET}: skipping [{cid}], already downloaded"
                )
                continue
            jobs.append(cid)
    else:
        assert ids is not None
        jobs = ids
    with concurrent.futures.ThreadPoolExecutor(max_workers=threads) as executor:
        codec: typing.Literal["flac", "m4a", "mp3"]
        workers: typing.Iterator[None] = executor.map(
            lambda j: download_audio(j, codec), jobs
        )  # type: ignore
        p_bar = tqdm.tqdm(
            workers, total=len(jobs), position=0, ascii=".#", colour="#00ff00"
        )
        list(p_bar)
        print(
            f"Download of {p_bar.n} song{'s' if p_bar.n != 1 else ''} finished in {p_bar.format_dict['elapsed']} seconds"
        )


@cli.command(help="Convert songs", no_args_is_help=True)
def convert(
    ids: Annotated[
        Optional[list[str]],
        typer.Argument(
            help="Convert the specified songs by their ID (format: ID1 ID2 ID3...)"
        ),
    ] = None,
    convert_all: Annotated[
        Optional[bool],
        typer.Option("--all", "-a", help="Download the entire discography of MSR."),
    ] = False,
    force: Annotated[
        Optional[bool],
        typer.Option("--force", "-f", help="Overwrite already converted files"),
    ] = False,
    allow_download: Annotated[
        Optional[bool],
        typer.Option(
            "--download", "-d", help="Allow downloading the song if it does not exist"
        ),
    ] = False,
    threads: Annotated[
        Optional[int],
        typer.Option(
            "--threads", "-t", help="Specify the maximum amount of parallel conversions"
        ),
    ] = None,
    to_mp3: Annotated[
        Optional[bool],
        typer.Option(
            "--mp3", help="Convert to MP3 instead of FLAC, cannot be used with --m4a"
        ),
    ] = False,
    to_m4a: Annotated[
        Optional[bool],
        typer.Option(
            "--m4a", help="Convert to M4A instead of FLAC, cannot be used with --mp3"
        ),
    ] = False,
) -> None:
    if to_m4a and to_mp3:
        typer.echo("Cannot use both --mp3 and --m4a flags together", err=True)
        exit()
    elif to_m4a:
        codec = "m4a"
    elif to_mp3:
        codec = "mp3"
    else:
        codec = "flac"
    if not ids and not convert_all:
        typer.pause(
            f"Please specify the song(s) you want to convert. Press any key to continue..."
        )
        return
    jobs: list[str] = []
    if convert_all:
        for s in get_song_list():
            cid: str = str(s.get("cid"))
            if not force and (not cid or is_downloaded(cid, codec)):
                print(
                    f"{colorama.Fore.LIGHTBLUE_EX}INFO{colorama.Fore.RESET}: skipping [{cid}], already converted"
                )
                continue
            jobs.append(cid)
    else:
        assert ids is not None
        jobs = ids
    workers: list[concurrent.futures.Future[None]] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=threads) as executor:
        codec: typing.Literal["flac", "m4a", "mp3"]
        for j in jobs:
            workers.append(executor.submit(convert_audio, j, codec, allow_download))
        p_bar = tqdm.tqdm(
            workers, total=len(jobs), position=0, ascii=".#", colour="#00ff00"
        )
        for p in concurrent.futures.as_completed(workers):
            pass
        print(
            f"Download of {p_bar.n} song{'s' if p_bar.n != 1 else ''} finished in {p_bar.format_dict['elapsed']} seconds"
        )


cli.add_typer(
    cache_command.cli,
    name="cache",
    help="Make modifications to the cached files. Primarily for deleting old cache files.",
    no_args_is_help=True,
)

if __name__ == "__main__":
    cli()
