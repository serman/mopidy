from __future__ import unicode_literals

import logging
import json
import os

import pykka

from mopidy import exceptions, models, settings
from mopidy.core import CoreListener
from mopidy.audio import PlaybackState
from threading import Timer
try:
    import cherrypy
    from ws4py.messaging import TextMessage
    from ws4py.server.cherrypyserver import WebSocketPlugin, WebSocketTool
    from jinja2 import Environment, FileSystemLoader
    import api
    import admin
    from boombox.bbtracklist import bbTracklistController
    from boombox.bbconst import bbContext
    from boombox.secure import sessionManager
    from passwd import userpassdict
    import urllib2
except ImportError as import_error:
    raise exceptions.OptionalDependencyError(import_error)

from . import ws


logger = logging.getLogger('mopidy.frontends.http')


class HttpFrontend(pykka.ThreadingActor, CoreListener):
    def __init__(self, core):
        super(HttpFrontend, self).__init__()
        self.core = core
        self._setup_server()
        self._setup_websocket_plugin()
        app = self._create_app()
        self._setup_logging(app)
        self.inetStatus=True;        
        self.t = Timer(60.0, self.checkConnection)
        self.t.start()
        
#mis opciones        
        self.core.playback.consume=True;

    def _setup_server(self):
        cherrypy.config.update({
            'engine.autoreload_on': False,
            'server.socket_host': (
                settings.HTTP_SERVER_HOSTNAME.encode('utf-8')),
            'server.socket_port': settings.HTTP_SERVER_PORT,
            #'server.thread_pool_max' : 7,
            #'server.thread_pool' : 7,
            'error_page.404': os.path.join(settings.HTTP_SERVER_STATIC_DIR, "404.html")
        })

    def _setup_websocket_plugin(self):
        WebSocketPlugin(cherrypy.engine).subscribe()
        cherrypy.tools.websocket = WebSocketTool()

    def _create_app(self):

        self.bbTracklist=bbTracklistController(self.core)
        if settings.HTTP_SERVER_STATIC_DIR:
            static_dir = settings.HTTP_SERVER_STATIC_DIR
        else:
            static_dir = os.path.join(os.path.dirname(__file__), 'data')
        logger.debug('HTTP server will serve "%s" at /', static_dir)

        if settings.HTTP_SERVER_COOKIES_DIR:
            cookies_dir = settings.HTTP_SERVER_COOKIES_DIR
        else:
            cookies_dir = os.path.join(os.path.dirname(__file__), 'cookies')

#http template dir
        if settings.HTTP_SERVER_TEMPLATE_DIR:
            template_dir = settings.HTTP_SERVER_TEMPLATE_DIR
        else:
            template_dir = os.path.dirname(__file__) +"/templates"
        logger.debug(u'HTTP server will serve templates at "%s" ', template_dir)
        env = Environment(loader=FileSystemLoader(template_dir))
        root = RootResource(self.core,env,self)
        #root = RootResource()
        root.mopidy = MopidyResource()
        root.mopidy.ws = ws.WebSocketResource(self.core)
        root.api = api.ApiResource(bbContext(self.bbTracklist,self.core))
        root.admin = admin.AdminResource(bbContext(self.bbTracklist,self.core),env)
        
        mopidy_dir = os.path.join(os.path.dirname(__file__), 'data')
        favicon = os.path.join(static_dir, 'favicon.ico')
        checkpassword = cherrypy.lib.auth_basic.checkpassword_dict(userpassdict)
        basic_auth = {'tools.auth_basic.on': True,
                  'tools.auth_basic.realm': 'earth',
                  'tools.auth_basic.checkpassword': checkpassword,
        }        
        
        config = {
            b'/':{
                'tools.sessions.on': True,
                'tools.sessions.storage_type' : "file",
                'tools.sessions.storage_path' : cookies_dir,
                'tools.sessions.timeout' : 900
            },
            b'/static': {
                'tools.staticdir.on': True,
                'tools.staticdir.index': 'index.html',
                'tools.staticdir.dir': static_dir,
            },
            b'/favicon.ico': {
                'tools.staticfile.on': True,
                'tools.staticfile.filename': favicon,
            },
            b'/mopidy': {
                'tools.staticdir.on': True,
                'tools.staticdir.index': 'mopidy.html',
                'tools.staticdir.dir': mopidy_dir,
            },
            b'/mopidy/ws': {
                'tools.websocket.on': True,
                'tools.websocket.handler_cls': ws.WebSocketHandler,
            },
            b'/admin' : basic_auth
        }

        return cherrypy.tree.mount(root, '/', config)


    def _setup_logging(self, app):
        cherrypy.log.access_log.setLevel(logging.WARNING)
        cherrypy.log.error_log.setLevel(logging.DEBUG)
        cherrypy.log.screen = False        
        app.log.access_log.setLevel(logging.DEBUG)
        app.log.error_log.setLevel(logging.DEBUG)

    def on_start(self):
        logger.debug('Starting HTTP server')
        cherrypy.engine.start()
        logger.info('HTTP server running at %s', cherrypy.server.base())

    def on_stop(self):
        logger.debug('Stopping HTTP server')
        cherrypy.engine.exit()
        self.t.cancel();
        logger.info('Stopped HTTP server')
        
    def checkConnection(self, ):        
        try:
            response=urllib2.urlopen('http://apple.com/library/test/success.html',timeout=2)
            self.inetStatus= True            
            self.t = Timer(10.0, self.checkConnection)
            self.t.start()            
        except:
            self.inetStatus = False
            self.t = Timer(10.0, self.checkConnection)
            self.t.start()

    # def on_event(self, name, **data):
    #     event = data
    #     event['event'] = name
    #     logger.info('-------- evento -- ' + name)
    #    # if(name=="track_playback_ended"):
    #        # self.track_playback_ended(**data)
    #
    #     message = json.dumps(event, cls=models.ModelJSONEncoder)
    #     cherrypy.engine.publish('websocket-broadcast', TextMessage(message))
    #     getattr(self, event)(**data)


    def track_playback_ended(self,tl_track, time_position):
        self.bbTracklist.playNext()




    def playlist_changed(self):
        #TODO
        pass
    
    def options_changed(self):
        #TODO   
        pass
    
    def volume_changed(self):
        #TODO
        pass



class RootResource(object):
#    pass
    def __init__(self, core,env,parent):
        self.core = core
        self.env=env
        self.parent=parent
        #cherrypy.sessions.delete()
        
    @cherrypy.expose
    def index(self):
        #if(cherrypy.request.headers['Host']!="boombox.asociacion-semilla.org"    ):
        #    raise cherrypy.HTTPRedirect("http://boombox.asociacion-semilla.org")
        if (self.parent.inetStatus==True):
            logger.info("statustrue")
            tmpl = self.env.get_template('mobile.html')
        else:
            logger.info("no internet")
            tmpl = self.env.get_template('noInternet.html')
        sessionManager()
        #logger.info("sesiones: " + str(len(cherrypy.session.cache)))
        return tmpl.render(user=cherrypy.session.get('user') , credit=cherrypy.session.get('songsLeft'))
    
    @cherrypy.expose
    def default(self, attr='abc'):
        raise cherrypy.HTTPRedirect("http://boombox.asociacion-semilla.org")
        
        
        


class MopidyResource(object):
    pass
    
    
