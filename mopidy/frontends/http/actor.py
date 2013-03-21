from __future__ import unicode_literals

import logging
import json
import os

import pykka

from mopidy import exceptions, models, settings
from mopidy.core import CoreListener
from mopidy.audio import PlaybackState

try:
    import cherrypy
    from ws4py.messaging import TextMessage
    from ws4py.server.cherrypyserver import WebSocketPlugin, WebSocketTool
    from jinja2 import Environment, FileSystemLoader
    import api
    from boombox.bbtracklist import bbTracklistController
    from boombox.bbconst import bbContext
    from boombox.secure import sessionManager
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
        
#mis opciones        
        self.core.playback.consume=True;

    def _setup_server(self):
        cherrypy.config.update({
            'engine.autoreload_on': False,
            'server.socket_host': (
                settings.HTTP_SERVER_HOSTNAME.encode('utf-8')),
            'server.socket_port': settings.HTTP_SERVER_PORT,

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


        cookies_dir = os.path.join(os.path.dirname(__file__), 'cookies')

#http template dir
        if settings.HTTP_SERVER_TEMPLATE_DIR:
            template_dir = settings.HTTP_SERVER_TEMPLATE_DIR
        else:
            template_dir = os.path.dirname(__file__) +"/templates"
        logger.debug(u'HTTP server will serve templates at "%s" ', template_dir)
        env = Environment(loader=FileSystemLoader(template_dir))
        root = RootResource(self.core,env)
        #root = RootResource()
        root.mopidy = MopidyResource()
        root.mopidy.ws = ws.WebSocketResource(self.core)
        root.api = api.ApiResource(bbContext(self.bbTracklist,self.core))
        
        
        mopidy_dir = os.path.join(os.path.dirname(__file__), 'data')
        favicon = os.path.join(mopidy_dir, 'favicon.png')

        config = {
            b'/':{
                'tools.sessions.on': True,
                'tools.sessions.storage_type' : "file",
                'tools.sessions.storage_path' : cookies_dir,
                'tools.sessions.timeout' : 600
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
        }

        return cherrypy.tree.mount(root, '/', config)


    def _setup_logging(self, app):
        cherrypy.log.access_log.setLevel(logging.DEBUG)
        cherrypy.log.error_log.setLevel(logging.DEBUG)
        cherrypy.log.screen = False

        app.log.access_log.setLevel(logging.NOTSET)
        app.log.error_log.setLevel(logging.NOTSET)

    def on_start(self):
        logger.debug('Starting HTTP server')
        cherrypy.engine.start()
        logger.info('HTTP server running at %s', cherrypy.server.base())

    def on_stop(self):
        logger.debug('Stopping HTTP server')
        cherrypy.engine.exit()
        logger.info('Stopped HTTP server')

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
    def __init__(self, core,env):
        self.core = core
        self.env=env
        #cherrypy.sessions.delete()
        
    @cherrypy.expose
    def index(self):
        tmpl = self.env.get_template('mobile.html')
        sessionManager()
        #logger.info("sesiones: " + str(len(cherrypy.session.cache)))
        return tmpl.render(user=cherrypy.session.get('user') , credit=cherrypy.session.get('songsLeft'))


class MopidyResource(object):
    pass
    
    
