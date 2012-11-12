import logging
import os

import pykka

from mopidy import exceptions, settings
from mopidy.core import CoreListener

try:
    import cherrypy
    from ws4py.messaging import TextMessage
    from ws4py.server.cherrypyserver import WebSocketPlugin, WebSocketTool
    from jinja2 import Environment, FileSystemLoader
except ImportError as import_error:
    raise exceptions.OptionalDependencyError(import_error)

from . import api, ws


logger = logging.getLogger('mopidy.frontends.http')


class HttpFrontend(pykka.ThreadingActor, CoreListener):
    def __init__(self, core):
        super(HttpFrontend, self).__init__()
        self.core = core
        self._setup_server()
        self._setup_websocket_plugin()
        app = self._create_app()
        self._setup_logging(app)
        self.core.playback.consume=False;

    def _setup_server(self):
        cherrypy.config.update({
            'engine.autoreload_on': False,
            'server.socket_host':
                settings.HTTP_SERVER_HOSTNAME.encode('utf-8'),
            'server.socket_port': settings.HTTP_SERVER_PORT,
        })

    def _setup_websocket_plugin(self):
        WebSocketPlugin(cherrypy.engine).subscribe()
        cherrypy.tools.websocket = WebSocketTool()

    def _create_app(self):

        if settings.HTTP_SERVER_STATIC_DIR:
            static_dir = settings.HTTP_SERVER_STATIC_DIR
        else:
            static_dir = os.path.dirname(__file__) +"/static"
        logger.debug(u'HTTP server will serve "%s" at /static', static_dir)

        if settings.HTTP_SERVER_TEMPLATE_DIR:
            template_dir = settings.HTTP_SERVER_TEMPLATE_DIR
        else:
            template_dir = os.path.dirname(__file__) +"/templates"
        logger.debug(u'HTTP server will serve templates at "%s" ', template_dir)

        env = Environment(loader=FileSystemLoader(template_dir))
        
        root = RootResource(self.core,env)
        root.api = api.ApiResource(self.core)
        root.ws = ws.WebSocketResource()

        config = {
            '/static': {
                'tools.staticdir.on': True,
                'tools.staticdir.index': 'index.html',
                'tools.staticdir.dir': static_dir,
            },
            '/api': {
                'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
            },
            '/ws': {
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
        logger.debug(u'Starting HTTP server')
        cherrypy.engine.start()
        logger.info(u'HTTP server running at %s', cherrypy.server.base())

    def on_stop(self):
        logger.debug(u'Stopping HTTP server')
        cherrypy.engine.exit()
        logger.info(u'Stopped HTTP server')

    def playback_state_changed(self, old_state, new_state):
        cherrypy.engine.publish('websocket-broadcast',
            TextMessage('playback_state_changed: %s -> %s' % (
                old_state, new_state)))

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
    def __init__(self, core,env):
        self.core = core
        self.env=env
        
    @cherrypy.expose
    def index(self):
        tmpl = self.env.get_template('mobile.html')
        return tmpl.render(user='sss', target='World')
