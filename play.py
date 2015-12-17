# November 2015
import subprocess
import argparse
import sys
import os
from search import Searcher, error


SHARED_AUDIO_DEVICE = "coreaudio/~:StackedOutput:0"
SHARE_VOLUME=30


def play_tracks(paths, force_window=False, keep_open=False, shuffle=False,
        share=False, volume=None, normalize=False, loop=False):
    """Plays the given paths using mpv"""
    if not paths:
        # is this an error or not?
        error("no tracks found :(")

    cmd = ["mpv"]
    if force_window:
        cmd.append("--force-window")
        if keep_open:
            cmd.append("--keep-open=yes")

    else:
        cmd.append("--no-audio-display")

    if volume is not None:
        cmd.append("--volume={}".format(volume))

    if share:
        cmd.append("--audio-device={}".format(SHARED_AUDIO_DEVICE))
        if volume is None:
            cmd.append("--volume=30")

    #if normalize:
    #    cmd.append("--af=lavrresample=normalize=yes")

    # Remove duplicates
    if shuffle:
        paths = list(set(paths))
        cmd.append("--shuffle=yes")

    if loop:
        cmd.append("--loop=inf")

    subprocess.run(cmd + paths)

description = """
Find and play music tracks using 'ag' (aka The Silver Searcher) and 'mpv'

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

    parser.add_argument("-s", "--shuffle", action="store_true", default=False,
        help="Shuffle the found tracks")

    parser.add_argument("-w", "--windowed", action="store_true", default=False,
        help="Show the tracks in a GUI window")

    parser.add_argument("-k", "--keep-open", action="store_true", default=False,
        help="Keep the GUI window open after the last track has finished")

    parser.add_argument("-a", "--share", action="store_true", default=False,
        help="Plays to the music to the multi-channel MIDI device to share it to default input (TLDR: play it to Skype)")

    parser.add_argument("-v", "--volume", default=50, type=int,
        help="The volume to start playing at (default: 50)")

    #parser.add_argument("--normalize", action="store_true", default=False,
    #    help="[NOT WORKING] Attempt to normalize the audio using libavresample")

    parser.add_argument("-l", "--loop", action="store_true", default=False,
        help="Loop the tracks")

    parser.add_argument("-n", "--dry-run", action="store_true",
        help="Just print the found tracks instead of playing them")

    parser.add_argument("-d", "--debug", action="store_true", default=False,
        help="print extra information for debugging")

    parser.add_argument("-q", "--quiet", action="store_true", default=False,
        help="suppress non-fatal warnings")

    parser.add_argument("pattern", nargs="+",
        help="the patterns to search with (see pattern prefixes below)")

    parser.add_argument("--exclude", metavar="pattern", nargs="+",
        help="exclude anything matched by the given patterns")

    parsed = parser.parse_args(args)

    searcher = Searcher(debug=parsed.debug, quiet=parsed.quiet)

    paths = searcher.find_tracks(parsed.pattern)
    if parsed.exclude:
        excluded = set(searcher.find_tracks(parsed.exclude))
        paths = [p for p in paths if not p in excluded]

    if not paths:
        errprint("No tracks found :(")
        sys.exit(1)

    if parsed.dry_run:
        for path in paths:
            print(path)
        return

    try:
        play_tracks(paths, keep_open=parsed.keep_open,
            force_window=parsed.windowed, shuffle=parsed.shuffle,
            share=parsed.share, volume=parsed.volume,
            #normalize=parsed.normalize,
            loop=parsed.loop)

    except KeyboardInterrupt:
        print("\nGoodbye!")


if __name__ == '__main__':
    main()
