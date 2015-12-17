# 4 December 2015
import subprocess
import argparse
import sys
import os
from patterner import Patterner


MUSIC_FOLDER = os.path.join(os.environ["HOME"], "mus")
PLAYLIST_FOLDER = os.path.join(MUSIC_FOLDER, "playlists")


def errprint(message):
    """Prints the message to stderr"""
    print(message, file=sys.stderr)

_p = Patterner()
_EXTENSIONS = {"mp3", "ogg", "flac", "m4a", "wav", "oga"}
_p.ENDING = r"[.]({})".format("|".join(_EXTENSIONS))
_p.SIMPLE = r".*?{}.*?"
_p.GENERAL = "{}{ENDING}"
_p.TITLE = r".*?/{}{ENDING}"
_p.ALBUM = r"{SIMPLE}/.*?{ENDING}"
_p.NON_PATH = r"[^/]*?{}[^/]*?"


def delimit_pattern(pattern, delimiter, template):
    """Splits the pattern at the delimiter and formats the template with 
    each part"""
    return delimiter.join(
        template.format(part.strip())
        for part in pattern.split(delimiter))


def create_title_pattern(term):
    """Creates a title search pattern from the given term"""
    return _p.TITLE.format(delimit_pattern(term, " ", _p.NON_PATH))


def create_album_pattern(term):
    """Creates an album search pattern from the given term"""
    main = delimit_pattern(term, "/", _p.NON_PATH)
    return _p.ALBUM.format(delimit_pattern(main, " ", _p.SIMPLE))


def create_general_pattern(term):
    """Creates a structure general pattern from the given term"""
    main = delimit_pattern(term, "/", _p.NON_PATH)
    return _p.GENERAL.format(delimit_pattern(main, " ", _p.SIMPLE))
    

_pattern_generators = {
    "@":    create_title_pattern,
    "@@":   create_album_pattern,
    "$":    create_general_pattern,
}


def find_tracks(patterns, debug=False, loaded_playlists=None):
    """Attempts to find the music tracks by the given patterns"""
    if loaded_playlists is None:
        loaded_playlists = set()
        
    paths = []
    for pattern in patterns:
        if not pattern: continue
        
        if not pattern.startswith(tuple(_pattern_generators.keys())):
            _, ext = os.path.splitext(pattern)
            
            if pattern.startswith("%"):
                pattern = os.path.join(PLAYLIST_FOLDER, pattern[1:].strip())
            
            if ext == ".txt":
                # Prepend the playlist folder to non-absolute playlists
                pattern = os.path.abspath(os.path.expanduser(pattern))
                
                if pattern in loaded_playlists:
                    msg = "The playlist {!r} is already loaded and won't be reincluded!"
                    errprint(msg.format(pattern))
                    continue
                
                # Add the playlist so that it can't load itself etc.
                loaded_playlists.add(pattern)
                
                paths += find_and_load_playlist(pattern, debug=debug,
                    loaded_playlists=loaded_playlists)
            
            elif ext[1:] in _EXTENSIONS:
                paths += pattern
            
            else:
                errprint("Unknown ending {!r} for pattern {!r}!".format(ext, 
                    pattern))
            continue
        
        else:
            # Find out which prefix it has! (longest first)
            for prefix in sorted(
                    _pattern_generators.keys(), key=len, reverse=True):
                if pattern.startswith(prefix):
                    text = pattern[len(prefix):].lstrip()
                    pat = _pattern_generators[prefix](text)
                    if debug:
                        print("Match: {} => {!r} ({!r})".format(prefix, text, pat))
                    break
        
            cmd = ["ag", "-i", "-g", pat, MUSIC_FOLDER]
        
            res = subprocess.run(cmd, stdout=subprocess.PIPE)
        
            if res.returncode == 0:
                paths += str(res.stdout, encoding="utf-8").strip().split("\n")
            else:
                errprint("No tracks found for pattern {!r}".format(pattern))
    
    return paths


def find_and_load_playlist(playlist, debug=False, loaded_playlists=None):
    """Search for the pattern and find the tracks of the found playlist"""
    if loaded_playlists is None:
        loaded_playlists = set()
    
    found_with_title = False
    playlists = []
    
    def debugprint(message):
        if debug:
            print(message)
    
    debugprint("Loaded playlists:\n{}".format("\n".join(loaded_playlists)))
    
    # If it's a path, just use it
    if os.path.exists(playlist):
        playlists.append(playlist)
        found_with_title = True
    
    # Otherwise try finding a playlist with it as title
    else:
        debugprint("Searching by playlist title...")
        cmd = ["ag", "-i", "-g", playlist, PLAYLIST_FOLDER]
        res = subprocess.run(cmd, stdout=subprocess.PIPE)
        if res.returncode == 0:
            for path in str(res.stdout, encoding="utf-8").strip().split("\n"):
                debugprint("- Found {!r}".format(os.path.basename(path)))
                playlists.append(path)
                found_with_title = True
    
    # If that fizzles, try and find something with the content
    if not found_with_title:
        debugprint("Searching by playlist content...")
        cmd = ["ag", "-l", "-i", playlist, PLAYLIST_FOLDER]
        res = subprocess.run(cmd, stdout=subprocess.PIPE)
        if res.returncode == 0:
            for path in str(res.stdout, encoding="utf-8").strip().split("\n"):
                debugprint("- Found {!r}".format(os.path.basename(path)))
                playlists.append(path)
    
    if not playlists:
        errprint("No playlists found!")
        
    patterns = []
    for playlist in playlists:
        with open(playlist, "r") as f:
            debugprint("Loading {!r}...".format(os.path.basename(playlist).rpartition(".")[0]))
            found = False
            for line in f.read().strip().split("\n"):
                if not line.startswith("#"):
                    patterns.append(line)
                    found = True
            if not found:
                errprint("No tracks found in playlist file {!r}".format(
                    os.path.basename(playlist)))
    
    if not patterns: 
        errprint("No patterns found in the given playlists")
    
    if debug:
        print("Patterns:")
        for pat in patterns:
            print("- {!r}".format(pat))
    
    return find_tracks(patterns, debug=debug, loaded_playlists=loaded_playlists)


def main(args=sys.argv[1:]):
    """Entry point"""
    description = """
    Find music tracks using 'ag' (aka The Silver Searcher)
    Syntax:
    No prefix for the path to a file or playlist (.txt containing patterns).
    @ for track titles      (eg: '@Cascadia').
    @@ for album titles     (eg: '@@Icarus EP').
    \% for playlists        (eg: '\%Fake.txt')
    $ for general patterns  (eg: '$Trash80') (titles, albums, paths) .
    """
    parser = argparse.ArgumentParser(description=description)
    
    parser.add_argument("pattern", nargs="+", 
        help="A pattern to search for")
    
    parser.add_argument("-d", "--debug", action="store_true", default=False,
        help="Print extra information for debugging")
    
    parser.add_argument("-x", "--exclude", metavar="pattern", nargs="+",
        help="Exclude anything matched by the given patterns")
    
    parsed = parser.parse_args(args)
    
    paths = find_tracks(parsed.pattern, debug=parsed.debug)
    if parsed.exclude:
        excluded = set(find_tracks(parsed.exclude, debug=parsed.debug))
        paths = [p for p in paths if not p in excluded]
    
    for path in paths:
        print(path)


if __name__ == '__main__':
    main()
