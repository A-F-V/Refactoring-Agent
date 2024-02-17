import click
import os
import dotenv
import pygit2 as git
from src.agent import test_agent

dotenv.load_dotenv()


# init click
@click.group()
def cli():
    pass


# A command to download and set up a repo, defaulting to what is in the .env file
@click.command()
@click.option("--repo", default=os.getenv("DEMO_REPO"), help="The repo to download")
@click.option("--folder", default="demo", help="The folder to download the repo to")
def init_repo(repo: str, folder: str):
    # Check if the repo is already downloaded
    if os.path.exists(folder):
        click.echo(f"{folder} already exists")
        # Reset the repo
        click.echo(f"Resetting {folder}...")
        git_repo = git.Repository(folder)
        git_repo.reset(git_repo.head.target, git.enums.ResetMode.HARD)  # type: ignore
        click.echo(f"Reset {folder}")
    else:
        click.echo(f"Downloading {repo}...")
        git.clone_repository(repo, "demo")
        click.echo(f"Downloaded {repo}")


@click.command()
def run():

    click.echo("Running the demo")
    click.echo(test_agent("What is the square root of 110"))


cli.add_command(init_repo)
cli.add_command(run)

if __name__ == "__main__":
    cli()
