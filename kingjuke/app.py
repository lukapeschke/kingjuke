#!/usr/bin/env python3

import falcon
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
    api = falcon.API()

    api.add_route('/jukebox', play_api.BaseHandler())
    api.add_route('/playlist', play_api.ApiPlaylist(to_play))
    api.add_route('/vote/{handler}/{title}', play_api.ApiVote())
    api.add_route('/admin/{handler}', play_api.ApiAdmin())

    options = {
        'bind': '{host}:{port}'.format(host='127.0.0.1', port='9090'),
        'workers': 1
    }
    KingJukeApp(api, options).run()


if __name__ == '__main__':
    main()
