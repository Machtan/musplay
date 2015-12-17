# Install

This program requires Python 3.2+.
It also requires the program `ag` (aka "The Silver Searcher") in your path.
For music playback, it uses the program `mpv`.
These can be installed on Mac OS X by using the following Homebrew command

```
$ brew install python3 ag mpv
```

### NOTE

Only \*nix systems are supported at the moment.


# Config

The program expects your music to be in a directory given by the environment
variable `MUSPLAY_MUSIC`. Playlists will be searched for in `$MUSPLAY_PLAYLISTS`
or, if that is missing, in `$MUSPLAY_MUSIC/Playlists`.


# Usage

Throw the folder somewhere and run
```
$ python3 musplay --help
```


# Search functionality

If you only want to use the program to search for tracks, use the `-n` flag as in
```
$ python3 musplay -n '@Trash80'
```
or run the `search.py` directly as in
```
$ python3 musplay/search.py '@Trash80'
```
