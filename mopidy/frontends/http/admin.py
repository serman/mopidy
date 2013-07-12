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

class AdminResource(object):
    exposed = True

    def __init__(self, context,env):
        self.core = context.core
        self.bbTracklist = context.bbTracklist
        self.env=env
       # self.player = PlayerResource(context.core)
       # self.playlists = PlaylistsResource(context.core)
#        self.search = SearchResource(core)

    @cherrypy.expose    
    def index(self):
        tmpl = self.env.get_template('admin.html')        
        #logger.info("sesiones: " + str(len(cherrypy.session.cache)))
        return tmpl.render()
   
#Esta funcion de la api recibe una nueva cancion y la aniade a la playlist

    @cherrypy.tools.json_out()
    @cherrypy.expose
    def addSong(self, jsonTrack="",name="",msg=""): #jsonTrack es la URI
        logger.info( "name......." + name )
        #Elimino restricciones de acceso
        #if(canIAddSong()==False):
        #    return json.dumps({'error': "TooManySongs"})
        #if(canAddThis()==False):
        #    return json.dumps({'error': "AlreadyThere"})
            
        if(jsonTrack==""):
            logger.info( "no hay cancion")
            return json.dumps({'error': "NoSong"})
        else:
            mtrack = self.core.library.lookup(jsonTrack).get()
            #mtrack=json.loads(jsonTrack,object_hook=models.model_json_decoder)
            logger.info(mtrack)
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
                songLeft=computeSongsLeft(self.bbTracklist.getTrackListLength())
            else:
                return json.dumps({'error': "NotFound"})

        return json.dumps({'ok': "ok","credit":songLeft})


    @cherrypy.tools.json_out()
    @cherrypy.expose
    def vote(self,song_id,votes):
        """
        @param song_id is the bb_Tracklist_id

        """
        song_id=int(song_id)
        #if(canIVoteThis(song_id)==True):            
        votes=int(votes)
        bbTrack1=self.bbTracklist.getTrackById(song_id)
        self.bbTracklist.vote(bbTrack1,votes)
        cherrypy.session['songsVoted'].append(song_id)
        return json.dumps({'ok': song_id})    
        #else:
        #    return json.dumps({'error': "You already voted this one"})

    @cherrypy.tools.json_out()
    @cherrypy.expose
    def setVolume(self, value):
        logger.info("setting vol" + value)
        volume = int(value)
        if volume < 0:
            volume = 0
        if volume > 100:
            volume = 100    
        self.core.playback.volume = volume
        return json.dumps({'ok': value}) 

    @cherrypy.tools.json_out()
    @cherrypy.expose    
    def getVolume(self ):
        vol= self.core.playback.volume.get() 
        return json.dumps({'volume': vol}) 
    
    

