#!/usr/bin/env python3

import falcon

from kingjuke import api as play_api
from kingjuke.playlist import Playlist
from waitress import serve


to_play = Playlist()
api = falcon.API()

api.add_route('/jukebox', play_api.BaseHandler())
api.add_route('/playlist', play_api.ApiPlaylist(to_play))
api.add_route('/vote/{handler}/{title}', play_api.ApiVote())
api.add_route('/admin/{handler}', play_api.ApiAdmin())

serve(api, listen='*:9090')
