from __future__ import unicode_literals

import logging
import random

from mopidy.models import TlTrack
from bbmodels import bbTrack

from mopidy.core import listener

logger = logging.getLogger('mopidy.bb')


class bbTracklistController(object):
    pykka_traversable = True

    def __init__(self, core):
        self._core = core
        self._next_tlid = 1
        self._bb_tracks = []
        self._version = 0




#Get the songs with their votes, comments and so on...
    def get_bb_tracks(self):
        return self._bb_tracks[:]

    tl_tracks = property(get_bb_tracks)
    """
    List of :class:`mopidy.boombox.models.bbTrack`.

    Read-only.
    """

#get only the song
    def get_tracks(self):
        return [bb_track.track for bb_track in self._bb_tracks]

    tracks = property(get_tracks)
    """
    List of :class:`mopidy.models.Track` in the tracklist.

    Read-only.
    """

    def get_length(self):
        return len(self._bb_tracks)

    length = property(get_length)
    """Length of the tracklist."""


    def add(self, track, at_position=None, msg="",name=""):
        """
        Add the track or list of tracks to the tracklist.

        If ``at_position`` is given, the tracks placed at the given position in
        the tracklist. If ``at_position`` is not given, the tracks are appended
        to the end of the tracklist.

        Triggers the :meth:`mopidy.core.CoreListener.tracklist_changed` event.

        :param tracks: tracks to add
        :type tracks: list of :class:`mopidy.models.Track`
        :param at_position: position in tracklist to add track
        :type at_position: int or :class:`None`
        :rtype: list of :class:`mopidy.models.TlTrack`
        """

        iter_track = bbTrack(track,self._next_tlid, " a msg", "perry") #bbTrack(self, mtrack , mid, mmsg="", mname="" ):

        if at_position is not None:
            self._bb_tracks.insert(at_position, iter_track)
            at_position += 1
        else:
            self._bb_tracks.append(iter_track)
        #self._core.tracklist.add(track)
        logger.info('bb - Added Song')
        if iter_track:
            #self._increase_version()
            pass
        self._next_tlid += 1
        return iter_track

    def vote(self,bbTrack,nvotes):
        """
        Ad or remove a vote within

        Perhaps: Triggers the :meth:`mopidy.core.CoreListener.tracklist_changed` event.
        """
        bbTrack.votes+=nvotes

    def getTrackById(self,song_id):
        for song in self._bb_tracks:
            logger.info(" track;  "+ str(song.serialize()) )
            if song.bbid == song_id:
                return song
        return None


    def clear(self):
        """
        Clear the tracklist.

        Triggers the :meth:`mopidy.core.CoreListener.tracklist_changed` event.
        """
        self._bb_tracks = []
        #self._increase_version()

    def index(self, bb_track):
        """
        Get index of the given :class:`mopidy.models.TlTrack` in the tracklist.

        Raises :exc:`ValueError` if not found.

        :param tl_track: track to find the index of
        :type tl_track: :class:`mopidy.models.TlTrack`
        :rtype: int
        """
        return self._bb_tracks.index(bb_track)

    def move(self, start, end, to_position):
        """
        Move the tracks in the slice ``[start:end]`` to ``to_position``.

        Triggers the :meth:`mopidy.core.CoreListener.tracklist_changed` event.

        :param start: position of first track to move
        :type start: int
        :param end: position after last track to move
        :type end: int
        :param to_position: new position for the tracks
        :type to_position: int
        """
        if start == end:
            end += 1

        tl_tracks = self._bb_tracks

        assert start < end, 'start must be smaller than end'
        assert start >= 0, 'start must be at least zero'
        assert end <= len(tl_tracks), \
            'end can not be larger than tracklist length'
        assert to_position >= 0, 'to_position must be at least zero'
        assert to_position <= len(tl_tracks), \
            'to_position can not be larger than tracklist length'

        new_tl_tracks = tl_tracks[:start] + tl_tracks[end:]
        for tl_track in tl_tracks[start:end]:
            new_tl_tracks.insert(to_position, tl_track)
            to_position += 1
        self._bb_tracks = new_tl_tracks
        #self._increase_version()

    def remove(self, m_tlid):
        tl_tracks = self.filter( { 'tlid':m_tlid } )
        for tl_track in tl_tracks:
            position = self._bb_tracks.index(tl_track)
            del self._bb_tracks[position]
        #self._increase_version()
        return tl_tracks

    def filter(self, criteria=None, **kwargs):
        """
        Filter the tracklist by the given criterias.

        Examples::

            # Returns track with TLID 7 (tracklist ID)
            filter({'tlid': 7})
            filter(tlid=7)

            # Returns track with ID 1
            filter({'id': 1})
            filter(id=1)

            # Returns track with URI 'xyz'
            filter({'uri': 'xyz'})
            filter(uri='xyz')

            # Returns track with ID 1 and URI 'xyz'
            filter({'id': 1, 'uri': 'xyz'})
            filter(id=1, uri='xyz')

        :param criteria: on or more criteria to match by
        :type criteria: dict
        :rtype: list of :class:`mopidy.models.TlTrack`
        """
        criteria = criteria or kwargs
        matches = self._bb_tracks
        for (key, value) in criteria.iteritems():
            if key == 'tlid':
                matches = filter(lambda ct: ct.tlid == value, matches)
            else:
                matches = filter(
                    lambda ct: getattr(ct.track, key) == value, matches)
        return matches


#TODO
    def updateOrder():
        pass



  

