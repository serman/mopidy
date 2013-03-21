from mopidy import exceptions
from mopidy import models
import translator
import logging
import json
import datetime
from boombox import bbmodels
from mopidy.audio import PlaybackState
from boombox.bbconst import bbContext
from boombox.secure import *
from mopidy.frontends.http.exceptions import (
 HttpNoExistError)
try:
    import cherrypy
except ImportError as import_error:
    raise exceptions.OptionalDependencyError(import_error)

logger = logging.getLogger('mopidy.frontends.http')

class ApiResource(object):
    exposed = True

    def __init__(self, context):
        self.core = context.core
        self.bbTracklist = context.bbTracklist
       # self.player = PlayerResource(context.core)
       # self.playlists = PlaylistsResource(context.core)
#        self.search = SearchResource(core)
    @cherrypy.tools.json_out()
    @cherrypy.expose    
    def index(self):
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

    @cherrypy.tools.json_out()
    @cherrypy.expose
    def search(self,search_for,search_what=""):
        if(search_what==""):
            results = self.core.library.search( any=[search_for] ).get()
        elif(search_what=="artist"):
            results = self.core.library.search( artist=[search_for] ).get()
        tracks = []
#        logger.info(results)
        #for track in results.tracks:
        #    track = track.serialize()
        #    tracks.append(track)
        
        return json.dumps({'searchResult': results}, cls=models.ModelJSONEncoder)
            #'searchResult':tracks
    
    @cherrypy.tools.json_out()
    @cherrypy.expose
    def findExact(self,uri):        
        results = self.core.library.lookup( uri ).get()
#        logger.info(results)
        #for track in results.tracks:
        #    track = track.serialize()
        #    tracks.append(track)
        
        return json.dumps({'searchResult': results}, cls=models.ModelJSONEncoder)
            #'searchResult':tracks
    
#Esta funcion de la api recibe una nueva cancion y la aniade a la playlist
#Comprueba permisos y decrece el contador de canciones disponibles del usuario
    @cherrypy.tools.json_out()
    @cherrypy.expose
    def addSong(self, jsonTrack="",name="",msg=""): #jsonTrack es la URI
        logger.info( "name......." + name )
        if(canIAddSong()==False):
            return json.dumps({'error': "TooManySongs"})
        if(canAddThis()==False):
            return json.dumps({'error': "AlreadyThere"})
            
        if(jsonTrack==""):
            logger.info( "no hay cancion")
            return json.dumps({'error': "NoSong"})
        else:
            mtrack = self.core.library.lookup(jsonTrack).get()
            #mtrack=json.loads(jsonTrack,object_hook=models.model_json_decoder)
            if mtrack:
                myBBTrack=self.bbTracklist.add(mtrack,m_msg=msg,m_name=name)
                self.bbTracklist.playNext()
                # if( self.core.tracklist.get_length().get() == 0 ): #Si no hay ninguna cancion en el TL "oficial"
                #     tl_tracks=self.core.tracklist.add(mtrack).get() #Aniadimos una
                #     myBBTrack.tlid=tl_tracks[0].tlid                #Y copiamos el ID de tracklist
                #     #logger.info("bb tlid------------ " + str(myBBTrack.tlid))
                # #logger.info("state " + self.core.playback.get_state().get())
                # if(self.core.playback.get_state().get()!=PlaybackState.PLAYING):
                #     self.core.playback.play().get()
                #     ctrac =self.core.playback.get_current_track().get().length
                #     self.core.playback.seek(ctrac-15000).get()
                songLeft=computeSongsLeft()
            else:
                return json.dumps({'error': "NotFound"})

        return json.dumps({'ok': "ok","credit":songLeft})

    @cherrypy.tools.json_out()
    @cherrypy.expose
    def trackList(self):
        futures = {
            'cp_tracks':   self.bbTracklist.get_bb_tracks(),
            #'current_cp_track': self.core.playback.current_cp_track,
            }
        cp_tracks = futures['cp_tracks']
        if(self.core.playback.get_state().get()==PlaybackState.PLAYING):
            cp_tracks.insert(0,self.bbTracklist.playingSong)
        return json.dumps({'tracks': cp_tracks}, cls=bbmodels.ModelJSONEncoder)

    @cherrypy.tools.json_out()
    @cherrypy.expose
    def vote(self,song_id,votes):
        """
        @param song_id is the bb_Tracklist_id

        """
        song_id=int(song_id)
        if(canIVoteThis(song_id)==True):            
            votes=int(votes)
            bbTrack1=self.bbTracklist.getTrackById(song_id)
            self.bbTracklist.vote(bbTrack1,votes)
            cherrypy.session['songsVoted'].append(song_id)
            return json.dumps({'ok': song_id})    
        else:
            return json.dumps({'error': "You already voted this one"})    


####### ------- FUNCIONES REFERIDAS AL PERFIL DE USUARIO Y LA SEGURIDAD #####
    @cherrypy.tools.json_out()
    @cherrypy.expose
    def setUserName(self, userName):
        cherrypy.session['user'] = userName
        return json.dumps({'user':userName})
    
    @cherrypy.tools.json_out()
    @cherrypy.expose
    def getInfo(self,what):
        if(what in {"user","songsLeft"}):            
            return json.dumps({'result':cherrypy.session.get(what)})
        else:
            return json.dumps({'error':"forbidden"})

    @cherrypy.tools.json_out()
    @cherrypy.expose
    def getStatus(self):
        updateCredits()
        if( cherrypy.session.get('timeNextSong')==0 ):
            printedtime=0
        else:
            printedtime=str(round((cherrypy.session.get('timeNextSong')-datetime.datetime.now()).seconds/60))
            
        
        
        
        return json.dumps({'user':cherrypy.session.get('user'),
                           'songsLeft':cherrypy.session.get('songsLeft'),
                           'timeNextSong' :printedtime ,
                           'songsVoted' : cherrypy.session.get('songsVoted')
                           })
        
    
    
    
    
