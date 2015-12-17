# Install
This program requires Python 3.2+ .
It also requires the program "The Silver Searcher" (aka 'ag') in your path.
For music playback, it uses the program "mpv".
These can all be installed on Mac OSX by using the following homebrew command
```
brew install python3 ag mpv
```

**NOTE**
Only Unix is supported at the moment

# Config
The program expects your music tracks to be in '_~/mus_' and playlists in '_~/mus/playlists_'.
This can be changed by setting the constants **MUSIC\_FOLDER** and **PLAYLIST\_FOLDER** in 'search.py'

# Usage
Throw the folder somewhere and run
```
python3 musplay --help
```

# Search functionality
If you only want to use the program to search for tracks, use the -n flag as in
```
python3 musplay -n '@Trash80'
```
