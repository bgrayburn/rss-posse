{ pkgs,  ... }:

{
  # https://devenv.sh/basics/
  env.FEED = "https://brianrayburn.tech/blog/rss.xml";

  scripts.post_rss_to_bluesky.exec = ''
    python $DEVENV_ROOT/rss-posse/__init__.py --bluesky-handle=$BLUESKY_USERNAME --bluesky-password=$BLUESKY_PASSWORD $RSS_FEED_URL
  '';

  packages = with pkgs; [
    git
  ];

  # https://devenv.sh/languages/
  languages.python = {
    package = pkgs.python312;
    enable = true;
    venv = {
      enable = true;
      requirements = ./requirements.txt;
    };
    uv.enable = true;
  };

  pre-commit.hooks.ruff.enable = true;

  dotenv.enable = true;
  difftastic.enable = true;
  # See full reference at https://devenv.sh/reference/options/
}
