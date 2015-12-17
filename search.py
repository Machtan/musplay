# 4 December 2015
import subprocess
import argparse
import sys
import os
from patterner import Patterner


def error(*msg, code=1):
    print("error:", *msg, file=sys.stderr)
    exit(code)


extensions = {"mp3", "aac", "mka", "dts", "flac", "ogg", "m4a", "ac3", "opus", "wav"}
patterner = Patterner()
patterner.ENDING = r"[.]({})".format("|".join(extensions))
patterner.SIMPLE = r".*?{}.*?"
patterner.GENERAL = "{}{ENDING}"
patterner.TITLE = r".*?/{}{ENDING}"
patterner.PLAYLIST = r".*?/{}"
patterner.ALBUM = r"{SIMPLE}/.*?{ENDING}"
patterner.NON_PATH = r"[^/]*?{}[^/]*?"


def delimit_pattern(pattern, delimiter, template):
    """Splits the pattern at the delimiter and formats the template with
    each part"""
    return delimiter.join(template.format(part.strip()) for part in pattern.split(delimiter))


def create_pattern_generator(fuzzify_path_elements, pattern, template):
    def pattern_generator(term):
        if fuzzify_path_elements:
            term = delimit_pattern(term, "/", patterner.NON_PATH)
        term = delimit_pattern(term, " ", template)
        return pattern.format(term)
    return pattern_generator


pattern_generators = {
    "@": create_pattern_generator(False, patterner.TITLE, patterner.NON_PATH),
    "@@": create_pattern_generator(True, patterner.ALBUM, patterner.SIMPLE),
    "%": create_pattern_generator(False, patterner.PLAYLIST, patterner.NON_PATH),
    "$": create_pattern_generator(True, patterner.GENERAL, patterner.SIMPLE),
}


sorted_patterns = list(pattern_generators.items())
sorted_patterns.sort(key=lambda pair: len(pair[0]), reverse=True)


loading_sentinent = object()


class Searcher:

    def __init__(self, *, music_dir=None, playlist_dir=None, debug=False, quiet=False):
        if music_dir is None:
            music_dir = os.environ.get('MUSPLAY_MUSIC')
            if music_dir is None:
                error("missing environment variable MUSPLAY_MUSIC", code=2)

        if playlist_dir is None:
            playlist_dir = os.environ.get('MUSPLAY_PLAYLISTS')
            if playlist_dir is None:
                playlist_dir = os.path.join(music_dir, 'Playlists')
                if not os.path.exists(playlist_dir):
                    playlist_dir = music_dir
            else:
                self.warn("MUSPLAY_PLAYLISTS folder doesn't exist {!r}".format(playlist_dir))

        self.music_dir = music_dir
        self.playlist_dir = playlist_dir
        self.debug_flag = debug
        self.quiet = quiet
        self.loaded_playlists = {}
        self.paths = []

    def debug(self, *msg):
        if self.debug_flag:
            print("debug:", *msg, file=sys.stderr)

    def warn(self, *msg):
        if not self.quiet:
            print("warning:", *msg, file=sys.stderr)

    def call_searcher(self, pattern, folder):
        cmd = ['ag', '--nocolor', '-ig', pattern, folder]
        self.debug(' '.join(cmd))
        result = subprocess.run(cmd, stdout=subprocess.PIPE)

        if result.returncode == 0:
            return result.stdout.decode('utf-8').strip().split('\n')
        else:
            return None

    def find_tracks(self, patterns):
        """Attempts to find the music tracks by the given patterns"""

        paths = []
        for pattern in patterns:
            if not pattern:
                continue

            # See if pattern matches one of the prefixes
            match = None
            for prefix, gen in sorted_patterns:
                if pattern.startswith(prefix):
                    match = (prefix, gen)
                    break
            if match:
                prefix, gen = match
                pat = gen(pattern[len(prefix):].lstrip())
                self.debug("match {} => {!r} ({!r})".format(prefix, pattern, pat))

                if prefix == '%':
                    # special playlist search
                    result = self.call_searcher(pat, self.playlist_dir)
                    if result:
                        res = []
                        for playlist in result:
                            res += self.parse_playlist(playlist)
                        result = res
                else:
                    result = self.call_searcher(pat, self.music_dir)

                if result:
                    paths += result
                else:
                    self.warn("no tracks found for pattern {!r}".format(pattern))
                continue

            # Otherwise it must be a simple path
            ext = os.path.splitext(pattern)[1]

            if ext == '.txt':
                pattern = os.path.join(self.playlist_dir, pattern)
                paths += self.parse_playlist(pattern)
                continue

            if ext[1:] in extensions:
                pattern = os.path.join(self.music_dir, pattern)
                paths.append(pattern)
                continue

            # TODO: maybe another solution would make sense
            error("unknown extension {!r} for pattern {!r}".format(ext, pattern))

        return paths

    def parse_playlist(self, playlist):
        playlist = os.path.realpath(playlist)

        cached = self.loaded_playlists.get(playlist)
        if cached is loading_sentinent:
            self.warn("recursive playlists are not supported")
            return []
        if cached:
            self.debug("using cache for {!r}".format(playlist))
            return self.loaded_playlists[playlist]
        self.loaded_playlists[playlist] = loading_sentinent

        self.debug("trying to parse {!r}".format(playlist))
        try:
            with open(playlist, 'r') as f:
                data = f.read()
        except IOError:
            error("could not read playlist file {!r}".format(playlist))

        patterns = []
        for line in data.split('\n'):
            line = line.strip()
            if line.startswith('#'):
                continue
            patterns.append(line)

        if not patterns:
            self.warn("no patterns in playlist file: {!r}".format(playlist))

        paths = self.find_tracks(patterns)
        self.loaded_playlists[playlist] = paths
        return paths


description = """
Find music tracks using 'ag' (aka The Silver Searcher)

environment variables:
  MUSPLAY_MUSIC         where to find music tracks (required)
  MUSPLAY_PLAYLISTS     where to find playlists
                        (default: $MUSPLAY_MUSIC/Playlists)
"""

epilog="""
pattern prefixes:
  @         search by track title (filename minus extension)
  @@        search by album title (directory name)
  %         search for playlists in the playlist directory (see above)
  $         search by the entire path to the file
  no prefix use pattern as a literal path to a file or playlist
"""


def main(args=sys.argv[1:]):
    parser = argparse.ArgumentParser(description=description, epilog=epilog,
        formatter_class=argparse.RawDescriptionHelpFormatter)

    parser.add_argument("pattern", nargs="+",
        help="the patterns to search with (see pattern prefixes below)")

    parser.add_argument("-d", "--debug", action="store_true", default=False,
        help="print extra information for debugging")

    parser.add_argument("-q", "--quiet", action="store_true", default=False,
        help="suppress non-fatal warnings")

    parser.add_argument("--exclude", metavar="pattern", nargs="+",
        help="exclude anything matched by the given patterns")

    parsed = parser.parse_args(args)

    searcher = Searcher(debug=parsed.debug, quiet=parsed.quiet)

    paths = searcher.find_tracks(parsed.pattern)

    if parsed.exclude:
        excluded = set(searcher.find_tracks(parsed.exclude))
        paths = (p for p in paths if not p in excluded)

    for path in paths:
        print(path)


if __name__ == '__main__':
    main()
