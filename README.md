# neath
Lightweight and extensible RSS bridge.

# Features
- Includes bridge for Spotify (via its API) and SoundCloud (via web scraping)
- Support for user-specified bridges

## Pre-Supplied Bridges
Each individual script provides an RSS bridge for a website and is known as an adapter. They are found in the "adapters" directory. Adapters are named according to the website they act as a bridge for, in reverse-URL notation: e.g. the Spotify adapter is called `com,spotify,open`, and the SoundCloud adapter is called `com,soundcloud`.

Each adapter takes 1 command-line argument, which is the URL to scrape. Additional information is passed in via environment variables. These are defined in .env files, which live in the "env" folder. .env files must be named identically to the adapter they correspond to. If an adapter needs a .env file, it will be listed below.

### Spotify
Requires CLIENT_SECRET and CLIENT_ID to be set in the corresponding .env file; these can be obtained by registering with Spotify.

# Usage
Point your RSS aggregator to \$YOUR_DOMAIN/v0/bridge/\$URL_TO_SCRAPE, where $URL_TO_SCRAPE is url-encoded. `neath` will look in the adapters and userscripts directories for any adapters that match the URL. If no adapters are found, a 404 is returned; other error codes can be thrown through various adapter errors. Otherwise, the generated RSS feed will be returned.

# Docker
This is the recommended way to deploy `neath`. A docker image for `neath` (coming soon) will be provided at ghcr.io/ubas-of-the-bush/neath. For now, clone the repository and build the image locally. You'll need to create 2 folders in the project root, "env" and "userscripts", before the container can build.

## Compose
An example docker-compose.yaml file might look like:
```yml
services:
    neath:
        image: ghcr.io/ubas-of-the-bush/neath:latest
        container_name: neath
        restart: unless-stopped
    ports:
        - 62244:62244
    volumes:
        - cache:/home/librarian/neath/cache
        - /path/to/your/scripts:/home/librarian/neath/userscripts
        - /path/to/your/env/config:/home/librarian/neath/env
    environment:
        - RUST_LOG=INFO

volumes:
    cache:
```

Change the log level shown by changing the RUST_LOG environment variable. Adapters inherit the main process's log level.

By default, the server listens on port 62244, but this can be changed by changing the run command. The port is the first argument given to the server.

# Adapter API
This is only relevant if you want to write a userscript. The API is somewhat inspired by CGI scripts.

Adapters are Python scripts which take 1 argument, which is the name of the URL to scrape to generate the RSS feed. They should be subclasses of the BaseAdapter class. Upon successfully generating a feed, they print the feed to stdout; the backend then passes what's in stdout to the caller. Throw an error by exiting with a non-zero exit code. The exit code is the status code the server will use in its response.

There is no sandboxing for these scripts so *do not* run untrusted userscripts!

Userscripts have access to the following libraries in addition to the stdlib: bs4, lxml, pydantic, requests, selenium, as well as convenience functions found in userscripts/lib - mainly see `rss.py` to generate and serialise an RSS feed.
