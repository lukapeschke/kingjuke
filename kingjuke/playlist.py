#!/usr/bin/python3

import json
from time import sleep

import pafy
import vlc

from kingjuke.palette import Palette


class InvalidUrl(Exception):
    pass


class BlackListed(Exception):
    pass


class Song(object):
    def __init__(self, video, tags=[]):
        self._score = 0
        self.title = video.title
        self.url = video.watchv_url
        self.length = video.length
        self._stream = (video.getbestaudio(preftype='ogg')
                        or video.getbestaudio())
        self._stream = self._stream.url
        self._media = Playlist._vlc_inst.media_player_new(self._stream)
        self.set_stop_callback(self.song_end)
        self.voters = {}
        self.tags = tags

    def __gt__(self, comp):
        if self.get_score() > comp.get_score():
            return True
        else:
            return False

    def get_score(self):
        score = self._score
        for key, value in self.voters.items():
            score += value
        return score

    def get_current_time(self):
        return int(self._media.get_time() / 1000)

    def play(self):
        self._media.play()

    def stop(self):
        self._media.stop()

    def pause(self):
        self._media.pause()

    def set_stop_callback(self, callback):
        events = self._media.event_manager()
        events.event_attach(vlc.EventType.MediaPlayerEndReached, callback)

    def has_voted(self, voter):
        if (voter is not None and voter in self.voters.keys()):
            return self.voters[voter]
        else:
            return 0

    def get_song_info(self, voter=None, first_song=False, playing=False):
        output = {
            'title': self.title,
            'url': self.url,
            'length': self.length,
            'score': self.get_score(),
            'has_voted': self.has_voted(voter),
            'tags': self.tags
        }
        if first_song:
            output['current_time'] = self.get_current_time()
            output['playing'] = playing
        return (output)

    @staticmethod
    def song_end(event):
        Playlist.set_playing(False)
        Playlist.delete_first_song()
        Playlist.play_song()

    @staticmethod
    def test_song(url, blacklist=None, tags=[]):
        try:
            video = pafy.new(url)
            if blacklist:
                for word in blacklist:
                    if word in video.title.lower():
                        raise BlackListed
            return video
        except (OSError, ValueError):
            raise InvalidUrl

    def upvote(self, voter=None):
        if not voter:
            self._score += 1
        else:
            if voter in self.voters.keys():
                if self.voters[voter] == 1:
                    self.voters[voter] = 0
                else:
                    self.voters[voter] = 1
            else:
                self.voters[voter] = 1

    def downvote(self, voter=None):
        if not voter:
            self._score -= 1
        else:
            if voter in self.voters.keys():
                if self.voters[voter] == -1:
                    self.voters[voter] = 0
                else:
                    self.voters[voter] = -1
            else:
                self.voters[voter] = -1


class Playlist(object):
    @classmethod
    def __init__(cls, theme='Anything', tags=[]):
        cls._playlist = []
        cls._current = None
        cls._playing = False
        cls._vlc_inst = vlc.Instance()
        cls.theme = theme
        cls.tags = tags
        cls._tag_palette = Palette()

    @classmethod
    def get_list(cls, voter=None):
        output = {}
        output['theme'] = cls.theme
        output['authorized_tags'] = cls.tags
        if cls._current:
            output['first_song'] = cls._current.get_song_info(
                voter=voter,
                first_song=True,
                playing=cls._playing
            )
        else:
            output['first_song'] = {}
        output['playlist'] = [
            i.get_song_info(voter=voter) for i in cls._playlist
        ]
        return output

    @classmethod
    def play_song(cls):
        if cls._current:
            if not cls._playing:
                cls.set_playing(True)
                cls._current.play()

    @classmethod
    def set_playing(cls, value=True):
        cls._playing = value

    @classmethod
    def delete_first_song(cls):
        if len(cls._playlist) > 0 and not cls._playing:
            cls._current = cls._playlist.pop(0)
        else:
            cls._current = None

    @classmethod
    def add_song(cls, video, tags='[]'):
        try:
            assert type(tags) is list
        except (AssertionError):
            tags = []
        song = Song(video, tags)
        for i in cls._playlist:
            i.upvote()
        if cls._current:
            cls._playlist.append(song)
        else:
            cls._current = song

    @classmethod
    def upvote(cls, title, voter=None):
        for song in cls._playlist:
            if title == song.title:
                song.upvote(voter=voter)
                cls._playlist.sort(reverse=True)
                break

    @classmethod
    def downvote(cls, title, voter=None):
        for song in cls._playlist:
            if title == song.title:
                song.downvote(voter=voter)
                cls._playlist.sort(reverse=True)
                break

    @classmethod
    def set_theme(cls, theme='Anything'):
        cls.theme = theme if (theme and len(theme)) else cls.theme

    @classmethod
    def has_voted(cls, title, voter):
        for song in cls._playlist:
            if title == song.title:
                return song.has_voted()
        return 0

    @classmethod
    def play(cls, *args):
        if cls._current:
            cls.set_playing(True)
            cls._current.play()

    @classmethod
    def pause(cls, *args):
        if cls._current:
            cls.set_playing(False) if cls._playing else cls.set_playing
            cls._current.pause()

    @classmethod
    def next_song(cls, *args):
        if cls._current:
            cls._current.stop()
            cls.set_playing(False)
            cls.delete_first_song()
            cls.play_song()

    @classmethod
    def delete_song(cls, title):
        if (cls._current and title == cls._current.title):
            cls.next_song()
        else:
            to_delete = None
            for i, song in enumerate(cls._playlist):
                if title == song.title:
                    to_delete = i
                    break
            if to_delete is not None:
                del cls._playlist[to_delete]

    @classmethod
    def _add_tag(cls, tag):
        if tag not in cls.tags:
            tag = {'name': tag, 'color': cls._tag_palette.get_color()}
            cls.tags.append(tag)

    @classmethod
    def add_tags(cls, tags=[]):
        if type(tags) is not list:
            tags = json.loads(tags)
        for tag in tags:
            cls._add_tag(tag)

    @classmethod
    def _remove_tag(cls, tag):
        tags = [i['name'] for i in cls.tags]
        if tag in tags:
            index = tags.index(tag)
            cls.tags.pop(index)

    @classmethod
    def remove_tags(cls, tags=[]):
        if type(tags) is not list:
            tags = json.loads(tags)
        for tag in tags:
            cls._remove_tag(tag)
