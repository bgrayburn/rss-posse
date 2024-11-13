import typer
import feedparser
import json
import jsonpickle
# import os
from pathlib import Path
from atproto import Client

app = typer.Typer()

# Path to store the IDs of posted RSS entries
POSTED_IDS_FILE = Path("~/.rss_to_bluesky_posted_ids").expanduser()

# Function to load posted IDs
def load_posted_ids():
    if not POSTED_IDS_FILE.exists():
        return set()
    with open(POSTED_IDS_FILE, "r") as f:
        return set(line.strip() for line in f)

# Function to save posted IDs
def save_posted_ids(posted_ids):
    with open(POSTED_IDS_FILE, "w") as f:
        f.write("\n".join(posted_ids))

# Function to post an entry to Bluesky
def post_to_bluesky(client: Client, entry_title: str, entry_link: str):
    post_content = f"{entry_title}\n{entry_link}"
    client.create_post(text=post_content)


@app.command()
def rss_to_print(
    rss_url: str = typer.Argument(..., help="URL of the RSS feed"),
    only_unposted: bool = typer.Option(False, help="Print only unposted or all feed items")
):
    if only_unposted:
        typer.echo("Loading posted entry IDs...")
    posted_ids = load_posted_ids() if only_unposted else []

    feed = feedparser.parse(rss_url)

    if feed.bozo:
        typer.secho("Failed to parse RSS feed. Please check the URL.", fg=typer.colors.RED)
        raise typer.Exit(code=1)

    typer.echo("Printing RSS entries...")

    for entry in feed.entries:
        entry_id = entry.id if hasattr(entry, "id") else entry.link

        if entry_id in posted_ids:
            continue

        entry_json = jsonpickle.encode(entry)
        entry_dict = json.loads(entry_json)
        for k in entry_dict.keys():
            typer.echo(f"{k}: {entry_dict[k]}")
    


@app.command()
def post_rss_to_bluesky(
    rss_url: str = typer.Argument(..., help="URL of the RSS feed"),
    bluesky_handle: str = typer.Option(..., prompt="Bluesky username (e.g., user.bsky.social)"),
    bluesky_password: str = typer.Option(..., prompt="Bluesky password")
):
    """Read an RSS feed and post unposted entries to Bluesky."""

    typer.echo("Loading posted entry IDs...")
    posted_ids = load_posted_ids()

    typer.echo("Parsing RSS feed...")
    feed = feedparser.parse(rss_url)

    if feed.bozo:
        typer.secho("Failed to parse RSS feed. Please check the URL.", fg=typer.colors.RED)
        raise typer.Exit(code=1)

    client = Client()

    typer.echo("Logging into Bluesky...")
    try:
        client.login(bluesky_handle, bluesky_password)
    except Exception as e:
        typer.secho(f"Failed to log into Bluesky: {e}", fg=typer.colors.RED)
        raise typer.Exit(code=1)

    typer.echo("Processing RSS entries...")
    new_ids = set()

    for entry in feed.entries:
        entry_id = entry.id if hasattr(entry, "id") else entry.link

        if entry_id in posted_ids:
            continue

        typer.echo(f"Posting entry: {entry.title}")
        try:
            post_to_bluesky(client, entry.title, entry.link)
            new_ids.add(entry_id)
        except Exception as e:
            typer.secho(f"Failed to post entry: {e}", fg=typer.colors.RED)

    if new_ids:
        typer.echo("Saving new posted IDs...")
        posted_ids.update(new_ids)
        save_posted_ids(posted_ids)

    typer.secho("Done!", fg=typer.colors.GREEN)

if __name__ == "__main__":
    app()
