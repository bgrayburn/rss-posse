import typer
import feedparser
import json
import jsonpickle
# import os
from pathlib import Path
from atproto import Client
from content_formatter import bluesky_build_post

app = typer.Typer()

# Path to store the IDs of posted RSS entries
POSTED_IDS_FILE = Path("~/.rss_to_bluesky_posted_ids").expanduser()

# Function to load posted IDs
def load_posted_ids():
    if not POSTED_IDS_FILE.exists():
        return set()
    with open(POSTED_IDS_FILE, "r") as f:
        return set(line.strip() for line in f)

def append_to_posted_ids(new_posted_ids: str):
    with open(POSTED_IDS_FILE, "a") as f:
        f.write("\n" + "\n".join(new_posted_ids))

def id(entry):
    return entry.id if hasattr(entry, "id") else entry.link

def get_rss_entries(rss_url: str, only_unposted: bool):
    feed = feedparser.parse(rss_url)

    if feed.bozo:
        typer.secho("Failed to parse RSS feed. Please check the URL.", fg=typer.colors.RED)
        raise typer.Exit(code=1)

    if only_unposted:
        typer.echo("Loading posted entry IDs...")
    posted_ids = load_posted_ids() if only_unposted else []

    entries = [e for e in feed.entries if id(e) not in posted_ids]

    return entries

@app.command()
def rss_to_print(
    rss_url: str = typer.Argument(..., help="URL of the RSS feed"),
    only_unposted: bool = typer.Option(False, help="Print only unposted or all feed items")
):
    entries = get_rss_entries(rss_url, only_unposted)

    for entry in entries:
        entry_json = jsonpickle.encode(entry)
        entry_dict = json.loads(entry_json)
        for k in entry_dict.keys():
            key_label = typer.style(k + ':', fg=typer.colors.GREEN, bold=True)
            typer.echo(key_label + f" {entry_dict[k]}")
    
@app.command()
def skip_to_present(rss_url: str):
    """Skip to the present state of the RSS feed."""
    typer.echo("Skipping to the present state of the RSS feed...")
    unposted_entries = get_rss_entries(rss_url, only_unposted=True)
    # Update the posted IDs file with the IDs of the new entries
    append_to_posted_ids([id(e) for e in unposted_entries])

@app.command()
def post_rss_to_bluesky(
    rss_url: str = typer.Argument(..., help="URL of the RSS feed"),
    bluesky_handle: str = typer.Option(..., prompt="Bluesky username (e.g., user.bsky.social)"),
    bluesky_password: str = typer.Option(..., prompt="Bluesky password"),
    dry_run: bool = typer.Option(False, help="Dry run (do not post to Bluesky)")
):
    """Read an RSS feed and post unposted entries to Bluesky."""
    entries = get_rss_entries(rss_url, only_unposted=True)

    client = Client()

    typer.echo("Logging into Bluesky...")
    try:
        client.login(bluesky_handle, bluesky_password)
    except Exception as e:
        typer.secho(f"Failed to log into Bluesky: {e}", fg=typer.colors.RED)
        raise typer.Exit(code=1)

    typer.echo("Processing RSS entries...")

    for entry in entries:
        typer.echo(f"Posting entry: {entry.title}")
        try:
            text, facets = bluesky_build_post(entry)
            if (not dry_run):
                client.send_post(text=text, facets=facets)
        except Exception as e:
            typer.secho(f"Failed to post entry: {e}", fg=typer.colors.RED)

    if (not dry_run):
        new_ids = [id(e) for e in entries]
        if new_ids.__len__():
            typer.echo("Saving new posted IDs...")
            append_to_posted_ids(new_ids)

    typer.secho("Done!", fg=typer.colors.GREEN)

if __name__ == "__main__":
    app()
