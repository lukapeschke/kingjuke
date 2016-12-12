#!/usr/bin/env python3

import falcon
from falcon_cors import CORS
import gunicorn.app.base

from kingjuke import api as play_api
from kingjuke.playlist import Playlist


class KingJukeApp(gunicorn.app.base.BaseApplication):

    def __init__(self, app, options={}):
        self.options = options
        self.application = app
        super(KingJukeApp, self).__init__()

    def load(self):
        return self.application

    def load_config(self):
        config = dict([(key, value) for key, value in self.options.items()
                       if key in self.cfg.settings and value is not None])
        for key, value in config.items():
            self.cfg.set(key.lower(), value)


def main():
    to_play = Playlist()
    cors_middleware = CORS(allow_all_origins=True)
    api = falcon.API(middleware=cors_middleware.middleware)

    api.add_route('/jukebox', play_api.BaseHandler())
    api.add_route('/playlist', play_api.ApiPlaylist(to_play))
    api.add_route('/vote/{handler}/{title}', play_api.ApiVote())
    api.add_route('/admin/{handler}', play_api.ApiAdmin())

    options = {
        'bind': '{host}:{port}'.format(host='0.0.0.0', port='9090'),
        'workers': 1
    }
    KingJukeApp(api, options).run()


if __name__ == '__main__':
    main()
