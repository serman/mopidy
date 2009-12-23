mopidy
======

mopidy is a MPD server with a Spotify backend.


Goal
----

Using a standard MPD client we want to search for music in Spotify, manage
Spotify play lists and play music from Spotify.

To limit scope, we will start by implementing a MPD server which only supports
Spotify, and not playback of files from disk. We will make mopidy modular, so
we can extend it with other backends in the future, like file playback and
other online music services such as Last.fm.


Architecture
------------

**TODO**


Resources
---------

- MPD

  - `MPD protocol documentation <http://www.musicpd.org/doc/protocol/>`_
  - The original `MPD server <http://mpd.wikia.com/>`_

- Spotify

  - `spytify <http://despotify.svn.sourceforge.net/viewvc/despotify/src/bindings/python/>`_,
    the Python bindings for `despotify <http://despotify.se/>`_
  - `Spotify's official metadata API <http://developer.spotify.com/en/metadata-api/overview/>`_
  - `pyspotify <http://code.google.com/p/pyspotify/>`_,
    Python bindings for the official Spotify library, libspotify


Installing despotify and spytify
--------------------------------

Check out the despotify source code::

    svn co https://despotify.svn.sourceforge.net/svnroot/despotify@363 despotify

As spytify does not seem up to date with the latest revision of despotify we
explicitly fetch revision 363, which was when spytify was last changed.

Install despotify's dependencies. At Debian/Ubuntu systems::

    sudo aptitude install libssl-dev zlib1g-dev libvorbis-dev \
        libtool libncursesw5-dev libpulse-dev \
        libgstreamer-plugins-base0.10-0 libgstreamer0.10-dev \
        libao-dev

Build and install despotify::

    cd despotify/src/
    make
    sudo make install

Install spytify's dependencies. At Debian/Ubuntu systems::

    sudo aptitude install python-pyrex

Build and install spytify::

    cd despotify/src/bindings/python/
    python setup.py build
    sudo python setup.py install

To validate that everything is working, run the ``test.py`` script which is
distributed with spytify::

    python test.py

The test script should ask for your username and password (which must be for a
Spotify Premium account), ask for a search query, list all your playlists with
tracks, play 10s from a random song from the search result, pause for two
seconds, play for five more seconds, and quit.


Running mopidy
--------------

To start mopidy, go to the root of the mopidy project, then simply run::

    python mopidy

To stop mopidy, press ``CTRL+C``.
