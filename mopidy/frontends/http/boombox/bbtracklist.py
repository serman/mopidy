from __future__ import unicode_literals

import logging
import random
from mopidy.audio import PlaybackState
from mopidy.models import TlTrack
from bbmodels import bbTrack
import itunes
if not itunes.is_caching_enabled():
      itunes.enable_caching()
import urllib
from mopidy.core import listener
import os
import operator

logger = logging.getLogger('mopidy.bb')
from mopidy import settings
cover_dir=""

class bbTracklistController(object):
    pykka_traversable = True

    def __init__(self, core,config):
        self._core = core
        self._next_tlid = 1
        self._bb_tracks = []
        self._version = 0
        self._tl_length=0
        self.playingSong=None
        if config['http']['static_dir']:
            cover_dir =  config['http']['static_dir']+ "/tmp/"
        else:
            cover_dir = os.path.join(os.path.dirname(__file__), 'data')




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


    def add(self, track, at_position=None, m_msg="",m_name="anonym"):
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

        iter_track = bbTrack(track,self._next_tlid, " a msg", m_name) #bbTrack(self, mtrack , mid, mmsg="", mname="" ):

        if at_position is not None:
            self._bb_tracks.insert(at_position, iter_track)
            at_position += 1
        else:
            self._bb_tracks.append(iter_track)
        #self._core.tracklist.add(track)
        
        if iter_track:
            #self._increase_version()
            pass
        self._next_tlid += 1
        
        self.updateOrder()
        
        #logger.info(iter_track.track[0].artists)
        for art in iter_track.track[0].artists:
            break
        try:
            if art != None:
                iter_track.cover_url = self.getCoverUrl(iter_track.track[0].album.name +" " + art.name )    
            else:
                iter_track.cover_url="default.jpg"
        except NameError:
            iter_track.cover_url="default.jpg"       
        
        return iter_track

    def vote(self,bbTrack,nvotes):
        """
        Ad or remove a vote within

        Perhaps: Triggers the :meth:`mopidy.core.CoreListener.tracklist_changed` event.
        """
        bbTrack.votes+=nvotes
        self.updateOrder()
        return bbTrack.votes

    def getTrackById(self,song_id):
        for song in self._bb_tracks:
            #logger.info(" track;  "+ str(song.serialize()) )
            if song.bbid == song_id:
                return song
        return None

    def getTrackByMainlistId(self,song_id):
        for song in self._bb_tracks:
            if song.tlid==song_id:
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

    def remove(self, m_bbid):
        tl_tracks = self.filter( { 'bbid':m_bbid } )
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
            elif key == 'bbid':
                matches = filter(lambda ct: ct.bbid == value, matches)
            else:
                matches = filter(
                    lambda ct: getattr(ct.track, key) == value, matches)
        return matches


    def getCoverUrl(self, album_title):
        try:
            album = itunes.search_album(album_title)[0]
            aa=album.get_artwork()
            bb=aa['100'].replace('100x100','225x225')
            fname=bb[bb.rfind("/")+1:len(bb)]
        except Exception:
            #logger.info("NO COVER AVAILABLE")
            return "default.jpg"            
        if ( os.path.isfile(cover_dir+fname) ==False) :
            urllib.urlretrieve (bb, cover_dir+fname)
        return fname
        
        
        pass
    



    def getNextOne(self):
        if(self.get_length>0) :
            return self._bb_tracks[0]
        else:
            return None

    def updateOrder(self):

        #imprescindible
            #oldList=self._bb_tracks;
            #self.sortedlist = sorted(self.songDict, key=lambda x: self.songDict[x].votes , reverse=True)
            #first order by time
            #sortedlist_tmp = sorted(self.songDict.values(), key=attrgetter('timeStamp'), reverse=False);
            # and then by votes
            self._bb_tracks.sort( key=operator.attrgetter("votes"), reverse=True);

    def playNext(self):
        #logger.info("playback ended ----")
        if( self._core.tracklist.get_length().get() == 0 ): #Si no hay ninguna cancion en el TL "oficial" Esto va a pasar siempre por disenio
            nextbbSong=self.getNextOne()

            if(nextbbSong!=None):


                tl_tracks=self._core.tracklist.add(nextbbSong.track).get() #Aniadimos una
                nextbbSong.tlid=tl_tracks[0].tlid                #Y copiamos el ID de tracklist
                self.playingSong=nextbbSong
                self.remove(nextbbSong.bbid)
                if(self._core.playback.get_state().get()!=PlaybackState.PLAYING):
                    self._core.playback.play().get()
                    ctrac =self._core.playback.get_current_track().get().length
                    #self._core.playback.seek(ctrac-15000).get()
    
    def isSongInTracklist(self, song_uri):
        for song in self._bb_tracks:            
            if song.track[0].uri == song_uri:
                return song
        return None
    
    def getTrackListLength(self):
        tl_length=0;
        for song in self._bb_tracks:
            try:
                tl_length += song.track[0].length
            except TypeError:
                tl_length += 120000           
        
        if tl_length==0:
            tl_length=90000
            
        self._tl_length=tl_length
        return self._tl_length
    
    def getFastTlLength(self):
        return self._tl_length
    
    
    





  

