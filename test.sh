#!/usr/bin/env bash

cd "$(dirname "$0")"
test -d test && rm -R test
mkdir test
cd test

mkdir music music/alpha music/beta playlists
touch music/{a.wav,b.wav,c.ogg,d.flac}
touch music/alpha/{b.wav,c.ogg} music/beta/d.flac

cat >playlists/a.txt <<EOF
# This is a comment
#a.wav
a.wav
b.wav
EOF
cat >playlists/b.txt <<EOF
a.wav
a.txt
EOF
cat >playlists/c.txt <<EOF
a.txt
b.txt
c.txt
EOF

export MUSPLAY_MUSIC="music"
export MUSPLAY_PLAYLISTS="playlists"

SUCCESS=1

run_test() {
	EXPECTED="$1"
	shift
	echo "Running test $@..."
	COUNT=$(echo $(python3 ../search.py "$@" | wc -l))
	# echo to strip leading space
	if test "$EXPECTED" != "$COUNT"; then
		echo "Test failed! (expected: $EXPECTED, got: $COUNT)"
		echo
		SUCCESS=0
	fi
}

# Test paths (music)
run_test 1 a.wav
run_test 2 a.wav b.wav
run_test 2 alpha/b.wav c.ogg
run_test 1 "$(pwd)/music/a.wav"

# Test title
run_test 7 '@' # wildcard (TODO)
run_test 2 '@b'
run_test 1 '@a'

# Test album
run_test 2 '@@alpha'
run_test 7 '@@' # it is recursive! (TODO)

# Test general
run_test 1 '$lph/b'
run_test 7 '$' # wildcard (TODO)

# Test paths (playlists)
run_test 2 'a.txt'

# Test fuzzy playlist search
run_test 2 '%a'
run_test 2 '%a.txt'
run_test 10 '%'

# Test recursive playlists
run_test 3 'b.txt'
run_test 5 'c.txt'

# Test exclusion
run_test 2 'c.txt' --exclude '@a'

echo ========================================
if test 1 = "$SUCCESS"; then
	echo "All tests succeded"
	exit 0
else
	echo "Some tests failed!"
	exit 1
fi
