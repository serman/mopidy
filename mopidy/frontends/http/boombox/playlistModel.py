from threading import Timer

import json
import logging, cherrypy, turbogears, urllib, cgi, re, string, math, findlyrics
from turbogears import controllers, expose, validate, redirect, config
import mpd
from os.path import *
import os
import atexit
import time
import traceback
from operator import itemgetter, attrgetter

start_votes=4

timer1=None #timer
log2 = logging.getLogger('sergio2')        

class song():
    def __init__(self,m_id,m_user):
        self.id=m_id
        self.user=m_user
        self.votes=start_votes
        self.timeStamp=time.time()
        
    def setMetaInfo(self,mtitle,martist,malbum):
        print "metainfo:"
        self.title=mtitle
        self.artist=martist
        self.album=malbum
        
    def vote(self, number):
        self.votes=self.votes+number
        return self.votes
        
    def setPlistId(self,mid):
        self.plistID=mid;

    def getStringObject(self):
        return {'spotify_id':self.id,"title": self.title, 'artist':self.artist, 'album':self.album, 'user':self.user,'votes':self.votes}
    
    def __str__(self):
        return "id="+str(self.id) + "|| votes=" + str(self.votes) 
    
 
        
#All the songs are accessed through songlist[id]
#The current list is: 

# how to sort dict by value
#http://stackoverflow.com/questions/613183/python-sort-a-dictionary-by-value

#http://doc.pfsense.org/index.php/Creating_a_DNS_Black_Hole_for_Captive_Portal_Clients



class songList():
    def __init__(self):
        #status variables
        self.moreSongsLeft=False
        self.host=config.get("mpd_host", "172.16.227.130")
        self.port=6600
        print "host:" + self.host
        self.songDict={}
        self.sortedlist=[]
        self.currentSong=None
        self.totalSongs=0
        self.songCloseToEnd=0;
        #self.mpdThread=mpd.MPDClient()
        #TODO start timer
        timer1 = Timer(2.0, self.syncFromServer)
        timer1.start()
        ########
        
 
    def getPlaylistSummary(self):
        listb=[]
        if(self.currentSong!=None):
            listb.append(self.currentSong.getStringObject()) 
            
            for i in range(0,len(self.sortedlist)) : 
                firstElement=   self.songDict[ self.sortedlist[i] ]
                listb.append(firstElement.getStringObject())
            return listb
        else: return "" 
        
    def getSong(self,spotify_id):
        try: 
            return self.songDict[spotify_id]
        except KeyError:
            if(self.currentSong!=None):
                if(self.currentSong.id==spotify_id):
                    return self.currentSong
            else:
                return None 
             
    def getVotes(self,spotify_id):
        if (self.getSong(spotify_id)!=None):
            return self.getSong(spotify_id).votes
        else:
             return None
 
    def addSong(self,m_id,m_user,mtitle,martist,malbum):
        #self.totalSongs+=1
        self.moreSongsLeft=True
        tmp_id=0
        if(self.countTotalSongs()==0): #if no song is playing currently I don't add it to the list but send it directly to mpd
            try:
                mpdTmp=myMpd(self.host, self.port)
                tmp_id=mpdTmp.addid(m_id.encode('utf-8'),0)
                mpdTmp.playid(tmp_id)
                self.currentSong=song(m_id,m_user)
                self.currentSong.setMetaInfo(mtitle,martist,malbum)
                self.currentSong.setPlistId(tmp_id)
                endMpd(mpdTmp)
            except:
                log2.debug("Error adding song"+ str(tmp_id) + "spotify id:" + str(m_id))
                log2.debug( traceback.format_exc())
                
        else: #Add the song to the list
            self.songDict[m_id]=song(m_id,m_user);
            self.songDict[m_id].setMetaInfo(mtitle,martist,malbum)
            self.arrangePlaylist();

       
    def saliendo(self):
        timer1.cancel()
    #Rearrange the playlist and update it against the server in case sth happens.
    #Returns false if the order didn't change 
    #Return True if it made a change
    def arrangePlaylist(self):
#imprescindible        
        oldList=self.sortedlist;
        #self.sortedlist = sorted(self.songDict, key=lambda x: self.songDict[x].votes , reverse=True)
        #first order by time  
        sortedlist_tmp = sorted(self.songDict.values(), key=attrgetter('timeStamp'), reverse=False);
        # and then by votes 
        sortedlist_tmp = sorted(sortedlist_tmp, key=attrgetter('votes'), reverse=True); 
        
        self.sortedlist=[]
        for b in sortedlist_tmp: 
            self.sortedlist.append(b.id);
        
        if(oldList==self.sortedlist):
            del oldList
            return False;
        else:
            del oldList
            return True
    
    def countTotalSongs(self):
        songsAtList=0
        if(self.currentSong!=None):
            songsAtList=len(self.songDict)+1;
        else:     
            if (len(self.songDict)>0):
                return -2
            else:
                return 0            
        return songsAtList
    return   

#move the queue up and send the first song to the server 
#If there is no song in te line it just remove the currentSong fom the localList
    def sendNextSongToServer(self,position=0,playNow=True):
        self.arrangePlaylist()
        self.currentSong=None 
        tmp_id=0
        if( len(self.sortedlist)>0 ):
            newCurrentSongId=self.sortedlist.pop(0)     
            mpdTmp=myMpd(self.host, self.port)            
     
            try:
                tmp_id=mpdTmp.addid(self.songDict[newCurrentSongId].id.encode('utf-8'),position)
                self.currentSong=self.songDict[newCurrentSongId]
                del self.songDict[newCurrentSongId]
                self.currentSong.setPlistId(tmp_id)
                if(playNow==True):
                    mpdTmp.playid(tmp_id)                          
                endMpd(mpdTmp)     
            except CommandError:
                del self.songDict[newCurrentSongId]
                log2.debug("Error adding song")
                log2.debug( "spotify id:" + str(m_id))
                log2.debug( traceback.format_exc())

                       
            print "envio al servidor la cancion" + str(tmp_id)
        else:
            
            self.moreSongsLeft=False
        
    
#Return True if the playlist order change
#FAlse if it didnt
#None if Error
        
    def voteUp(self,mid):
        #Check if the song to receive the vote is the currentSong
        if (mid==self.currentSong.id):
            self.currentSong.vote(1)
            return False
        else:
            try:
                self.songDict[mid].vote(1)
                return self.arrangePlaylist()
            except KeyError:
                return False 
        	
    def voteDown(self,mid):
        if (mid==self.currentSong.id):#current song
            self.currentSong.vote(-1)
            if(self.currentSong.votes<=0):
                self.removeCurrentSong()
                self.sendNextSongToServer()
            return False    
        else:
            try:
                self.songDict[mid].vote(-1)
                if(self.songDict[mid].votes<=0):
                    del self.songDict[mid]
                    self.arrangePlaylist()
                    return str(-2);
                return self.arrangePlaylist()
            except KeyError:
                log2.debug("vote:down KeyError")
                log2.debug( traceback.format_exc())
                return None
            
#send mpd message to remove current song            
    def removeCurrentSong(self):
        try:
            mpdTmp=myMpd(self.host, self.port)
            tmp_id = mpdTmp.deleteid(self.currentSong.plistID)
            endMpd(mpdTmp)
        except:
            log2.debug(",removeCurrentSong,")
            log2.debug( traceback.format_exc())
        #mpd remove current
        #TODO mpd remove
        return
    
# {'album': 'Rage Against The Machine/Evil Empire', 'title': 'Killing In The Name', 'track': '2', 'artist': 'Rage Against The Machine', 'pos': '0', 'file': 'spotify:track:4SkDYOAZSsHb7uF66xXpgt', 'time': '314', 'date': '2009-01-01', 'id': '3'}
#status:

#{'songid': '0', 'playlistlength': '4', 'playlist': '4', 'repeat': '0', 'consume': '0', 'song': '1', 'random': '0', 'state': 'play', 'xfade': '0', 'volume': '100', 'single': '0', 'time': '83:230', 'elapsed': '83.546', 'bitrate': '160'}

    def printQueueStatus(self):
        try:
            print "currentSong :"+ str(self.currentSong)# + "title:" + self.currentSong.title 
            print "elements in List: " + str(len(self.songDict))
            print "count total songs: " + str(self.countTotalSongs())
        except AttributeError:
            pass
    
    def maintenance(self,mpdTmp):
        try:            
            #self.mpdThread.connect(self.host, self.port,timeout=6)
            status_now=mpdTmp.status()            
            if(status_now['state']!='play' and int(status_now['playlistlength'])>0 ):
                #mpdTmp.play(0)
                pass
            elif(status_now['state']!='play'):
                self.clear(mpdTmp)   
        except:
            log2.debug("maintenance. Error") 
            log2.debug( traceback.format_exc())   
            

    def clear(self,mpdTmp):
        mpdTmp.clear()
        mpdTmp.load('Stapelbaddsparken')
        mpdTmp.shuffle()
        mpdTmp.consume(1)
  #      self.m.crossfade(3)
        mpdTmp.play()        
        del self.songDict
        self.songDict={}
        self.currentSong=None
        self.sortedlist=[]
        self.totalSongs=0
        self.songCloseToEnd=0;             
        
    def syncFromServer(self):        
        
        mpdTmp1=myMpd(self.host, self.port)
        self.maintenance(mpdTmp1)
        endMpd(mpdTmp1) 
        
        #Only if I have songs to send:
        timeLeft=100
        #self.printQueueStatus()
        if ( len(self.songDict)  <= 0 and self.currentSong==None ): #If there is no song at the queue. we don't need to do anything here
            timer1 = Timer( 5.0 , self.syncFromServer )            
            timer1.start()         
            return False     
#########        
        
        try:
            mpdTmp=myMpd(self.host, self.port)
            #self.mpdThread.connect(self.host, self.port,timeout=4)
            elapsed=mpdTmp.status()['elapsed']
            songtime=mpdTmp.currentsong()['time']
            #self.mpdThread.disconnect()
            timeLeft=int(songtime)-int(float(elapsed))

            endMpd(mpdTmp)            
        except :
            log2.debug("error on function syncFromServer 1")
            print "error on function syncFromServer 1"
            log2.debug( traceback.format_exc())
            
            #print "keyError en syncFromServer. Probablemente porque no quedan ya canciones en la lista"        
        #print str(timeLeft) + " songtime " +  str(songtime) + "elapsed_time" + str(elapsed)
        try:
            if(timeLeft<7): #if less than 7 seconds left to  the currentsong:                
                #self.mpdThread.connect(self.host, self.port,timeout=4)
                mpdTmp=myMpd(self.host, self.port)
                tmp_id=mpdTmp.currentsong()['id']
                endMpd(mpdTmp) 
                if(tmp_id!=self.songCloseToEnd): # it means I have to change song. We only join here once per track
                    self.songCloseToEnd = tmp_id               
                    self.sendNextSongToServer(1,False)              
                    print "sendNextSong. Nueva cancion al servidor id"  
        except:
            print "error on function syncFromServer 2"
            log2.debug("syncFromServer2")
            log2.debug( traceback.format_exc())
            
        timer1 = Timer(5.0, self.syncFromServer)
        timer1.start()        
        return False
        
#     def getPlayList_json(){
#     
#     
#     }    
        
    def startAutoTest(self,):
        exampleList=["spotify:track:1q1JhABnsBxbeWsgwlLll7", "spotify:track:5d47h8XfBJ0nM68JdEFudI","spotify:track:5mY1gIKCqG6yNmmXDwCtWp","spotify:track:4a26gjktpS0Yoh8bLiwkUT"]
        #for i in exampleList:
        for i in range(1,5):
        #(self,m_id,m_author,mtitle,martist,malbum):
            #self.addSong(i,"user"+str(i),str(i),str(i),str(i))
            self.songDict[i]=song(i,"user");
            self.songDict[i].setMetaInfo("title_"+str(i),"art"+str(i),"malbum"+str(i))
            time.sleep(1)
        #aa=self.arrangePlaylist();    
        print self.sortedlist    
        #self.voteUp("code_3") 
        
        
        #for key in self.songDict.iterkeys():
         #    print key, self.songDict[key].votes        
        #print self.sortedlist
        #print aa;
        #newlist = sorted(self.songDict, key=lambda x: self.songDict[x].votes , reverse=False)  
        #print newlist    
       
mylist=None
        
def main():
    mhost="172.16.227.130" #config.get("172.16.227.130", "localhost")
    mport=6600 #int(config.get("mpd_port", 6600))
    m=mpd.MPDClient()
    m.connect(host=mhost, port=mport,timeout=10)
    m.clear()
    m.load('Stapelb\xc3\xa4ddsparken')
    m.shuffle()
    m.consume(1)
    m.disconnect()
    mylist=songList(m)
    try:
        timer1.cancel()
    except:
        pass    
    atexit.register(mylist.saliendo)
    
    
    #playlistInfo = m.playlistinfo()
    #playlistID = m.status().playlist


    
    #mylist.startAutoTest()
    return mylist
    print "Aaaaa"
            
if __name__ == "__main__":
    main()            