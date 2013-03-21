import cherrypy
import logging
import datetime
logger = logging.getLogger('mopidy.frontends.http')

def sessionManager():
    #1 Si no existe sesion la creo
    ##
    if (('my_id' in cherrypy.session.keys()) == False):
        logger.info( " %%%%%% %%%%%%%%%%%%%%%%%%%%%%%%%%% NuevaSesion session_id= " + cherrypy.session.id)
        cherrypy.session['my_id'] = cherrypy.session.id
        cherrypy.session['songsLeft']  = 4
        cherrypy.session['songsVoted'] = []
        cherrypy.session['user'] = "anonymous"
        cherrypy.session['timeNextSong']=0
        
    else:
        logger.info( " %%%%%% %%%%%%%%%%%%%%%%%%%%%%%%%%% ids info sesion= " +  str(cherrypy.session.keys()))

def canIAddSong( songId="" ):
    if (cherrypy.session['songsLeft']>0):
        return True
    else:
        return False
#Check if the song cannot be added for some reason: black list, already there ...
def canAddThis(songId="",tracklist="" ):       
    return True

#Check if the user can vote a song
def canIVoteThis(songId ):
    if (songId in cherrypy.session['songsVoted']) == False :
        return True
    else:
        return False

def computeSongsLeft():
    cherrypy.session['songsLeft']  -= 1
    if (cherrypy.session['songsLeft']==0):
        cherrypy.session['timeNextSong'] =datetime.datetime.now()+datetime.timedelta(minutes=10)
    return cherrypy.session['songsLeft']


def updateCredits():
    """
    Se ejecuta cuando un usuario pretende conocer sus creditos o realiza alguna peticion al servidor   
    Toma los datos de la sesion del usuario que realiza la peticion            
        :rtype: 0 si el usuario teiene creditos para enviar canciones o el tiempo que falta para poder enviar la cancion 
    """
    if  cherrypy.session['timeNextSong'] == 0:
        return 0
    if  cherrypy.session['timeNextSong'] < datetime.datetime.now():
        cherrypy.session['songsLeft']  += 1
        cherrypy.session['timeNextSong'] = 0;
        return 0
    else:
        return cherrypy.session['timeNextSong'] - datetime.datetime.now()
    
    


