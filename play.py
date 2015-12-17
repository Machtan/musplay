# November 2015
import subprocess
import argparse
import sys
import os
from search import find_tracks


SHARED_AUDIO_DEVICE = "coreaudio/~:StackedOutput:0"
SHARE_VOLUME=30


def errprint(message):
    """Prints the message to stderr"""
    print(message, file=sys.stderr)


def play_tracks(paths, force_window=False, keep_open=False, shuffle=False,
        share=False, volume=None, normalize=False, loop=False):
    """Plays the given paths using mpv"""
    if not paths:
        errprint("No tracks found :(")
        sys.exit(1)  # Is this an error or not?

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


def main(args=sys.argv[1:]):
    """Entry point"""
    description = """
    Find and play music tracks using 'ag' (aka The Silver Searcher) and 'mpv'.
    Playlists will only be included once (to avoid the program searching in circles)
    Syntax:
    No prefix for the path to a file or playlist (.txt containing patterns).
    @ for track titles      (eg: '@Cascadia').
    @@ for album titles     (eg: '@@Icarus EP').
    %% for playlists        (eg: '%%Fake.txt')
    $ for general patterns  (eg: '$Trash80') (titles, albums, paths) .
    """
    parser = argparse.ArgumentParser(description=description)

    parser.add_argument("pattern", nargs="+",
        help="A pattern to search for")

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

    parser.add_argument("--normalize", action="store_true", default=False,
        help="[NOT WORKING] Attempt to normalize the audio using libavresample")

    parser.add_argument("-d", "--debug", action="store_true", default=False,
        help="Print extra information for debugging")

    parser.add_argument("-l", "--loop", action="store_true", default=False,
        help="Loop the tracks")

    parser.add_argument("-x", "--exclude", metavar="pattern", nargs="+",
        help="Exclude anything matched by the given patterns")

    parser.add_argument("-n", "--dry-run", action="store_true",
        help="Just print the found tracks instead of playing them")


    # ======== Post-parser =========
    parsed = parser.parse_args(args)


    paths = find_tracks(parsed.pattern, debug=parsed.debug)
    if parsed.exclude:
        excluded = set(find_tracks(parsed.exclude, debug=parsed.debug))
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
            normalize=parsed.normalize, loop=parsed.loop)

    except KeyboardInterrupt:
        print("\nGoodbye!")


if __name__ == '__main__':
    main()
