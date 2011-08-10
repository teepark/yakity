from __future__ import absolute_import

import cgi
import sys
import time
import traceback

import yajl

from . import client


class WSGIApp(object):
    def __init__(self, conf):
        self._config = conf
        self._junction_client = client.prepare_client(conf)

    def _get_param(self, name, params, default=None):
        val = params.get(name, [])
        return val and val[0] or default

    def _handle(self, environ, start_response):
        segments = filter(None, environ['PATH_INFO'].split('/'))
        params = cgi.parse_qs(
                environ.get('QUERY_STRING', ''), keep_blank_values=True)

        roomname = segments[0]
        username = environ['auth'][0]

        yak = client.Yakity(self._config, self._junction_client, username)

        if len(segments) == 1:
            if environ['REQUEST_METHOD'] == 'GET':
                last_seen = int(self._get_param('last', params) or 0)
                result = yak.read(roomname, last_seen)
                for r in result:
                    r['timestamp'] = time.ctime(r['timestamp'] + timediff)
                return yajl.dumps(result)

            if environ['REQUEST_METHOD'] == 'POST':
                msg = environ['wsgi.input'].read()
                yak.say(roomname, msg)
                return '{"success":true}'

        if segments[1] == 'join':
            yak.join(roomname)
            return '{"success":true}'

        if segments[1] == 'depart':
            yak.depart(roomname)
            return '{"success":true}'

    def __call__(self, environ, start_response):
        # auth required
        if 'HTTP_AUTHORIZATION' not in environ:
            start_response("401 Unauthorized", [
                ("Content-Type", "text/plain"),
                ("Content-Length", "23"),
                ("WWW-Authenticate", 'Basic realm="yakity api"'),
            ])
            return ["authorization required."]
        authtype, token = filter(None,
                environ['HTTP_AUTHORIZATION'].split(' '))
        if authtype.lower() != 'basic':
            start_response("401 Unauthorized", [
                ("Content-Type", "text/plain"),
                ("Content-Length", "29"),
                ("WWW-Authenticate", 'Basic realm="yakity api"'),
            ])
            return ["basic authorization required."]
        environ['auth'] = token.decode("base64").split(":", 1)

        try:
            result = self._handle(environ, start_response)
            rc = "200 OK"
            content_type = "application/json"
        except Exception:
            result = ''.join(traceback.format_exception(*sys.exc_info()))
            rc = "500 Internal Server Error"
            content_type = 'text/plain'

        start_response(rc, [
            ('Content-Type', content_type),
            ('Content-Length', str(len(result)))
        ])
        return [result]

timediff = time.mktime(time.localtime()) - time.mktime(time.gmtime())
