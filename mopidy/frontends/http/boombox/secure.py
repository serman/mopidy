import cherrypy
import logging
import datetime
logger = logging.getLogger('mopidy.frontends.http')
import cPickle
MAX_CREDITOS=3;
connection=None
import urllib2

def sessionManager():
    #1 Si no existe sesion la creo
    ##
    if (('my_id' in cherrypy.session.keys()) == False):
        logger.info( " %%%%%% %%%%%%%%%%%%%%%%%%%%%%%%%%% NuevaSesion session_id= " + cherrypy.session.id )
        cherrypy.session['my_id'] = cherrypy.session.id
        cherrypy.session['songsLeft']  = MAX_CREDITOS
        cherrypy.session['songsVoted'] = []
        cherrypy.session['user'] = "anonymous"
        cherrypy.session['timeNextSong']=0
        
    else:
        logger.info( " %%%%%% %%%%%%%%%%%%%%%%%%%%%%%%%%% ViejaSesion ids info sesion= " +  str(cherrypy.session.items()))
    
        
def restartSession(motivo=""):
    logger.info(" ErrorSession ERROR EN LA CLAVE DE SESION: " +str(motivo))
    #if 'my_id' in cherrypy.session: del cherrypy.session['my_id']
    #sessionManager();
    pass


def canIAddSong( songId="" ):
    try:
        if (cherrypy.session['songsLeft']>0):
            return True
        else:
            return False
    except KeyError:
        restartSession("canIAddSong")
        return True
    
    
#Check if the song cannot be added because is already there ...
def canAddThis(songURI="",tracklist="",  ):
    if(tracklist.isSongInTracklist(songURI)!=None):
        return False
    
    return True

#Check if the user can vote a song
def canIVoteThis(songId ):
    try:
        if (songId in cherrypy.session['songsVoted']) == False :
            return True
        else:
            return False
    except KeyError:
        restartSession("canIVoteThis")
        return True    


def computeSongsLeft( tlLength):
    """
    Key function. Receives current trackList length in miliseconds returns the number of songs left. Add time for next sont into cherrypy.session['timeNextSong']
    It runs when the user
    """
    intervalo=computeTimeToAddNewSong(tlLength)
    try:
        cherrypy.session['songsLeft']  -= 1
        #if (cherrypy.session['songsLeft']==0):
        #INCLUYO MOMENTO DE ACTUALIZACION DE CREDITOS
        cherrypy.session['timeNextSong'] = intervalo
        return cherrypy.session['songsLeft']    
    except KeyError:
        restartSession("computeSongsLeft")
        return True

def computeTimeToAddNewSong(tlLength):
    tlLength=tlLength/1000
    tlLength-=90
    if (tlLength<1):
        tlLength=17
    return datetime.datetime.now() + datetime.timedelta( seconds=tlLength ) 
    
def updateCredits(tlLength):
    """
    Se ejecuta cuando un usuario pretende conocer sus creditos con getStatus o realiza alguna peticion al servidor   
    Toma los datos de la sesion del usuario que realiza la peticion            
        :rtype: 0 si el usuario teiene creditos para enviar canciones o el tiempo que falta para poder enviar la cancion 
    """
    try:
        #code
        if  cherrypy.session['timeNextSong'] == 0:
            return 0
        if  cherrypy.session['timeNextSong'] < datetime.datetime.now(): #Si ha llegado el momento de actualizar
            if ( cherrypy.session['songsLeft']<MAX_CREDITOS ): # y no estamos sobre el limite
                cherrypy.session['songsLeft']  += 1 #se actualiza
                cherrypy.session['timeNextSong'] = computeTimeToAddNewSong(tlLength);
            else:
                cherrypy.session['timeNextSong'] = 0;
            return 0
        else:
            return cherrypy.session['timeNextSong'] - datetime.datetime.now()       
    except KeyError:
        return 0;
        

class blackList(object):
    #self.balcklist={'uri':'timestamp'}
    
    def __init__(self, filename):
        self.filename=filename
        self.blacklist={}
        pass
    
    def load(self):
        try:
            self.blacklist = cPickle.load(open(self.filename, 'rb'))
        except Exception, e:
            logger.info("blacklist file not found or cannot be open" + str(e))          
        
    
    
    def addURI(self, URI):
        if self.isOnBlacklist(URI)==False:
            self.blacklist[URI]=datetime.datetime.now()+datetime.timedelta(days=10)
        return
    
    def empty(self, arg1):
        self.blacklist={}
        pass
    
    def isOnBlacklist(self, URI):
        if(self.blacklist.get(URI))==None:
            return False
        else:
            return True
    
    
    def updatePL(self):
        for k,v in self.blacklist.items():
            if v< datetime.datetime.now():
                del self.blacklist[k]
        pass
    
    
    def saveToFile(self):
        cPickle.dump(self.blacklist, open(self.filename, 'wb')) 
        pass
    
    

    
    
if __name__ == '__main__':
    mlist=blackList("otroe.txt")
    mlist.load()
#    mlist.addURI("http://asdfasda:asdasdf")
    mlist.addURI("aaa")
    mlist.addURI("cccasdf")
    mlist.updatePL()
    print mlist.blacklist
    mlist.saveToFile()

    
    
    
    
    

