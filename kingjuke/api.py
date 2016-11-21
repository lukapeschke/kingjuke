import os

from base64 import b64decode
import falcon
from hashlib import sha512
import json

from kingjuke import playlist


class Unauthorized(Exception):
    pass


class BaseHandler(object):
    def on_get(self, req, resp):
        self.send_full_response(resp, 'Jukebox', falcon.HTTP_200)

    @staticmethod
    def get_post_body(req):
        output = ''
        while True:
            chunk = req.stream.read(4096)
            if not chunk:
                break
            output = output + chunk.decode()
        return output

    @staticmethod
    def send_full_response(resp, body, status):
        resp.status = status
        resp.body = body


class ApiAdmin(BaseHandler):
    """Class to handle /admin enpoint."""
    def __init__(self):
        self._user = os.environ.get('JUKEBOX_ADMIN_USER') or 'user'
        self._user = sha512(self._user.encode()).hexdigest()
        self._pwd = os.environ.get('JUKEBOX_ADMIN_PASSWORD') or 'password'
        self._pwd = sha512(self._pwd.encode()).hexdigest()

    def valid_auth(self, req):
        try:
            auth = req.auth.split(' ')[1]
            auth = b64decode(auth).decode()
            user, pwd = auth.split(':')
            user = sha512(user.encode()).hexdigest()
            pwd = sha512(pwd.encode()).hexdigest()
            assert user == self._user
            assert pwd == self._pwd
        except:
            raise Unauthorized

    def on_get(self, req, resp, handler):
        func_map = {
            'log': self.valid_auth
        }
        if handler not in func_map.keys():
            self.send_full_response(
                resp,
                "Invalid request: GET {}".format('/admin/' + handler),
                falcon.HTTP_400
            )
        try:
            func_map[handler](req)
            self.send_full_response(resp, 'OK', falcon.HTTP_200)
        except Unauthorized:
            self.send_full_response(resp, 'Unauthorized', falcon.HTTP_401)

    def on_post(self, req, resp, handler):
        func_map = {
            'play': playlist.Playlist.play,
            'pause': playlist.Playlist.pause,
            'next': playlist.Playlist.next_song,
        }
        if handler not in func_map.keys():
            self.send_full_response(
                resp,
                "Invalid request: POST {}".format('/admin/' + handler),
                falcon.HTTP_400
            )
        else:
            try:
                self.valid_auth(req)
                func_map[handler]()
                self.send_full_response(resp, 'OK', falcon.HTTP_200)
            except Unauthorized:
                self.send_full_response(resp, 'Unauthorized', falcon.HTTP_401)

    def on_delete(self, req, resp, handler):
        func_map = {
            'delete': playlist.Playlist.delete_song
        }
        if handler not in func_map.keys():
            self.send_full_response(
                resp,
                "Invalid request: DELETE {}".format('/admin/' + handler),
                falcon.HTTP_400
            )
        else:
            try:
                self.valid_auth(req)
                req_body = self.get_post_body(req)
                func_map[handler](req_body)
                self.send_full_response(resp, 'OK', falcon.HTTP_200)
            except Unauthorized:
                self.send_full_response(resp, 'Unauthorized', falcon.HTTP_401)


class ApiPlaylist(BaseHandler):
    """Class to handle /playlist endpoint."""
    def __init__(self, to_play):
        super(ApiPlaylist, self).__init__()
        self.playlist = to_play

    def on_get(self, req, resp):
        """Returns the current playlist."""
        resp.status = falcon.HTTP_200
        current_playlist = self.playlist.get_list(voter=req.access_route[0])
        resp.body = json.dumps(current_playlist)

    def on_post(self, req, resp):
        """Adds submited URLs to the current playlist."""
        req_body = self.get_post_body(req)
        try:
            video = playlist.Song.test_song(req_body)
            self.send_full_response(resp, 'Accepted', falcon.HTTP_201)
            self.playlist.add_song(video)
            self.playlist.play_song()
        except playlist.InvalidUrl:
            self.send_full_response(resp, 'Invalid URL', falcon.HTTP_400)
        except playlist.BlackListed:
            self.send_full_response(resp, 'Blacklisted song', falcon.HTTP_403)


class ApiVote(BaseHandler):
    """Class to handle the /vote endpoint."""
    @staticmethod
    def has_voted(voter, title):
        result = playlist.Playlist.has_voted(title, voter)
        return json.dumps({title: result})

    def on_get(self, req, resp, handler, title):
        """Returns the client's vote (0 if client did not vote)."""
        func_map = {
            'has_voted': self.has_voted
        }
        if handler not in func_map.keys():
            self.send_full_response(
                resp,
                "Invalid request: GET {}".format('/vote/' + handler),
                falcon.HTTP_400
            )
        else:
            try:
                voter = req.access_route[0]
                body = func_map[handler](voter, title)
                self.send_full_response(resp, body, falcon.HTTP_200)
            except IndexError:
                self.send_full_response(resp,
                                        'Not Authentified',
                                        falcon.HTTP_401)

    def on_post(self, req, resp, handler, title):
        """Handles upvotes and downvotes"""
        func_map = {
            'up': playlist.Playlist.upvote,
            'down': playlist.Playlist.downvote
        }
        if handler not in func_map.keys():
            self.send_full_response(
                resp,
                "Invalid request: POST {}".format('/vote/' + handler),
                falcon.HTTP_400
            )
        else:
            try:
                voter = req.access_route[0]
                func_map[handler](title, voter=voter)
                self.send_full_response(resp, 'OK', falcon.HTTP_201)
            except IndexError:
                self.send_full_response(resp,
                                        'Not Authentified',
                                        falcon.HTTP_401)
