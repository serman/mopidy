from mopidy import exceptions
import translator
import logging
from mopidy.frontends.http.exceptions import (
 HttpNoExistError)
try:
    import cherrypy
except ImportError as import_error:
    raise exceptions.OptionalDependencyError(import_error)

logger = logging.getLogger('mopidy.frontends.http')

class ApiResource(object):
    exposed = True

    def __init__(self, core):
        self.core = core
        self.player = PlayerResource(core)
        self.tracklist = TrackListResource(core)
        self.playlists = PlaylistsResource(core)
        self.search = SearchResource(core)
    @cherrypy.tools.json_out()
    def GET(self):
        return {
            'resources': {
                'player': {
                    'href': '/api/player/',
                },
                'tracklist': {
                    'href': '/api/tracklist/',
                },
                'playlists': {
                    'href': '/api/playlists/',
                },
            }
        }


class PlayerResource(object):
    exposed = True

    def __init__(self, core):
        self.core = core

    @cherrypy.tools.json_out()
    def GET(self):
        futures = {
            'state': self.core.playback.state,
            'current_track': self.core.playback.current_track,
            'consume': self.core.playback.consume,
            'random': self.core.playback.random,
            'repeat': self.core.playback.repeat,
            'single': self.core.playback.single,
            'volume': self.core.playback.volume,
            'time_position': self.core.playback.time_position,
        }
        current_track = futures['current_track'].get()
        if current_track:
            current_track = current_track.serialize()
        return {
            'properties': {
                'state': futures['state'].get(),
                'currentTrack': current_track,
                'consume': futures['consume'].get(),
                'random': futures['random'].get(),
                'repeat': futures['repeat'].get(),
                'single': futures['single'].get(),
                'volume': futures['volume'].get(),
                'timePosition': futures['time_position'].get(),
            }
        }

    @cherrypy.tools.json_out()
    def POST(self,prop,value):
        if prop=='state':
            if value=="playing":
                self.core.playback.play()
            if value=="stopped":
                self.core.playback.stop()
            if value=="paused":
                self.core.playback.pause()    

                            
        if prop=='consume':
            self.core.playback.consume=value
        if prop=='random' :
            self.core.playback.random=value
        if prop=='single' :
            self.core.playback.single=value
        if prop=='volume':
            self.core.playback.volume=value
        if prop=='repeat' :
            self.core.playback.repeat=value            
        if prop=='time_position':
            self.core.playback.time_position=value


class TrackListResource(object):
    exposed = True

    def __init__(self, core):
        self.core = core

    @cherrypy.tools.json_out()
    def GET(self):
        futures = {
            'cp_tracks': self.core.current_playlist.cp_tracks,
            'current_cp_track': self.core.playback.current_cp_track,
        }
        cp_tracks = futures['cp_tracks'].get()
        tracks = []
        for cp_track in cp_tracks:
            track = cp_track.track.serialize()
            track['cpid'] = cp_track.cpid
            tracks.append(track)
        current_cp_track = futures['current_cp_track'].get()
        return {
            'currentTrackCpid': current_cp_track and current_cp_track.cpid,
            'tracks': tracks,
        }

    def PUT(self, uri, songpos=None):
        print "uri es " + uri
        track = self.core.library.lookup(uri).get()
        if track is None:
            raise HttpNoExistError(u'No such song', command=u'addid')
        if songpos is None:
            cp_track = self.core.current_playlist.add( track).get()
        else:
            cp_track = self.core.current_playlist.add( track, at_position=songpos).get()     
        print cp_track        
        #self.core.playback.play(cp_track).get()                    
        return {'Id': cp_track.cpid}           

    @cherrypy.expose
    def move (self, cp_id, new_position):
        try:
            cp_id=int(cp_id)
            new_position=int(new_position)
        except ValueError:
            raise HttpWrongParameterError
                
        trackToMove=self.core.current_playlist.get(cpid=cp_id).get()
        if trackToMove is None:
            raise HttpNoExistError(u'No such song', command=u'get(cpid)')
        trackIndex=self.core.current_playlist.index(trackToMove).get()
        self.core.current_playlist.move(trackIndex,trackIndex,new_position)

class SearchResource(object):
    exposed = True

    def __init__(self, core):
        self.core = core

    @cherrypy.tools.json_out()
    def GET(self,search_for, search_what ):
        results = self.core.library.search( artist=[search_for] ).get()
        tracks = []
        #logger.info(results)
        #for track in results.tracks:
        #    track = track.serialize()
        #    tracks.append(track)
        
        return {
            'searchResult': translator.playlist_to_dict_format(results),
            #'searchResult':tracks
        }

class PlaylistsResource(object):
    exposed = True

    def __init__(self, core):
        self.core = core

    @cherrypy.tools.json_out()
    def GET(self):
        playlists = self.core.stored_playlists.playlists.get()
        return {
            'playlists': [p.serialize() for p in playlists],
        }
