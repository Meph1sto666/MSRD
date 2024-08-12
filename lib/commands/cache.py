import typer
from typing_extensions import Annotated
import os
import shutil

cli: typer.Typer = typer.Typer()

@cli.command()
def clear(type: str, y: Annotated[bool, typer.Option("--yes", "-y")] = False):
	if not type in ["audio", "lyrics", "cover"]:
		typer.pause(f"Specified cache ({type.upper()}) does not exist. Press any key to continue...")
		return
	if not os.path.exists(os.getenv(f"{type.upper()}_CACHE_DIR", "")):
		typer.pause(f"{type.upper()} cache is already cleared. Press any key to continue...")
		return
	if not y:
		typer.confirm(f"Are you sure you want to clear {type} cache data?", abort=True)
	if type == "all":
		cache_dir: str | None = os.getenv("CACHE_DIR")
		assert cache_dir is not None
		shutil.rmtree(cache_dir)
	else:
		cache_dir: str | None = os.getenv(f"{type.upper()}_CACHE_DIR")
		assert cache_dir is not None
		shutil.rmtree(cache_dir)
		typer.pause(f"{type.upper()} has been cleared. Press any key to continue...")