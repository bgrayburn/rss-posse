import typer
import json
from handlebars import Compiler
from atproto import client_utils
from string_utils import word_count, removeSpaces
import re

compiler = Compiler()

def fill_handlebars_template(template, entry):
  template = compiler.compile(template)

  entry.categories = get_categories_from_entry(entry)

  return template(entry).strip()

def get_categories_from_entry(entry):
    if hasattr(entry, 'tags') and entry.tags:
        return [removeSpaces(tag.term) for tag in entry.tags]
    else:
        return []

### Bluesky ###

def bluesky_build_post(entry):
    with open('rss-posse/templates/bluesky.handlebars', 'r') as file:
        template = file.read()
    raw_txt = fill_handlebars_template(template, entry)
    typer.echo(f"raw_txt: {raw_txt}")
    typer.echo(f"raw_txt word count: {word_count(raw_txt)}")
    text, facets = bluesky_build_text_and_facets(raw_txt)
    return [text, facets]

def bluesky_build_text_and_facets(data):
    text_builder = client_utils.TextBuilder()
    post_segments = parse_text_to_text_builder_segments(data)
    for c in post_segments:
        typer.echo(json.dumps(c, indent=2))
        if c['type'] == 'link':
            text_builder.link(c['text'], c['url'])
        elif c['type'] == 'hashtag':
            text_builder.tag(c['text'], c['text'][1:])
        elif c['type'] == 'text':
            text_builder.text(c['text'])
    return [text_builder.build_text(), text_builder.build_facets()]

def parse_text_to_text_builder_segments(text):
    pattern = re.compile(
        r'\[([^\]]+)\]\(([^\)]+)\)|#\w+|[^#\[\]]+'
    )

    segments = []
    for match in pattern.finditer(text):
        typer.echo(f"segment text: {match.group()}")
        if match.group(1) and match.group(2):  # It's a link
            segments.append({
                "type": 'link',
                "text": match.group(1),
                "url": match.group(2)
            })
        elif match.group(0).startswith('#'):  # It's a hashtag
            segments.append({
                "type": 'hashtag',
                "text": match.group(0)
            })
        else:  # It's plain text
            segments.append({
                "type": 'text',
                "text": match.group(0)
            })

    return segments