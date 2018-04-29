package main

import (
	"sync"

	log "github.com/Sirupsen/logrus"
)

// Playlist represents the current playlist
type Playlist struct {
	songs       []*Song
	currentSong *Song
	ch          chan string
	songCh      chan *Song
	mu          sync.RWMutex
}

var playlist *Playlist

// NewPlaylist creates a new Playlist
func NewPlaylist() *Playlist {
	return &Playlist{
		songs:  make([]*Song, 0),
		ch:     make(chan string),
		songCh: make(chan *Song)}
}

// GetPlaylist returns a usable pointer to a Playlist
func GetPlaylist() *Playlist {
	if playlist == nil {
		playlist = NewPlaylist()
	}
	return playlist
}

// Lock locks the playlist for read/write access
func (p *Playlist) Lock() {
	log.Debug("Locking playlist")
	p.mu.Lock()
}

// Unlock unlocks the playlist for read/write access
func (p *Playlist) Unlock() {
	log.Debug("Unlocking playlist")
	p.mu.Unlock()
}

// RLock locks the playlist for read/write access
func (p *Playlist) RLock() {
	log.Debug("RLocking playlist")
	p.mu.RLock()
}

// RUnlock unlocks the playlist for read/write access
func (p *Playlist) RUnlock() {
	log.Debug("RUnlocking playlist")
	p.mu.RUnlock()
}

// UnPause unpauses the current song
func (p *Playlist) UnPause() {
	p.ch <- "unpause"
}

func (p *Playlist) unPause() {
	log.Debug("UnPause playlist")
	if p.currentSong != nil {
		p.currentSong.UnPause()
	}
}

// Pause pauses the current song
func (p *Playlist) Pause() {
	p.ch <- "pause"
}

func (p *Playlist) pause() {
	log.Debug("Pause playlist")
	if p.currentSong != nil {
		p.currentSong.Pause()
	}
}

// TogglePause toggles pause
func (p *Playlist) TogglePause() {
	p.ch <- "togglePause"
}

func (p *Playlist) togglePause() {
	if p.currentSong != nil {
		p.currentSong.TogglePause()
	}
}

// AddSong adds a song to the playlist
func (p *Playlist) AddSong(s *Song) {
	p.ch <- "add"
	p.songCh <- s
}

func (p *Playlist) addSong() {
	song, _ := <-p.songCh
	p.Lock()
	p.songs = append(p.songs, song)
	p.Unlock()
	go func() {
		song.Download()
		song.Convert()
	}()
	log.Infof("Added %s to the playlist", song.Name)
}

func (p *Playlist) len() int {
	len := 0
	p.RLock()
	for _, val := range p.songs {
		if val != nil {
			len++
		}
	}
	return len
}

func (p *Playlist) firstSong() *Song {
	p.RLock()
	defer p.RUnlock()
	for _, val := range p.songs {
		if val != nil {
			return val
		}
	}
	return nil
}

// Next plays the next song in queue
func (p *Playlist) Next() {
	p.ch <- "next"
}

func (p *Playlist) next() {
	if p.currentSong == nil {
		if p.currentSong = p.firstSong(); p.currentSong != nil {
			go p.currentSong.Play(p.ch)
		}
	} else {
		if len(p.songs) > 1 {
			p.Lock()
			p.songs = p.songs[1:]
			p.currentSong = p.songs[0]
			p.Unlock()
			go p.currentSong.Play(p.ch)
		} else {
			p.songs = make([]*Song, 0)
		}
	}
}

func (p *Playlist) isSongInPlaylist(name string) bool {
	p.RLock()
	defer p.RUnlock()
	for _, song := range p.songs {
		if song != nil && song.Name == name {
			return true
		}
	}
	return false
}

func (p *Playlist) playlistEventHandler() {
	for {
		instruction, open := <-p.ch
		if !open {
			log.Fatal("Playlist channel is not open")
		}
		log.Infof("Received instruction %s\n", instruction)
		switch instruction {
		case "unpause":
			p.unPause()
		case "pause":
			p.pause()
		case "togglePause":
			p.togglePause()
		case "add":
			p.addSong()
		case "songFinished":
			p.next()
		case "next":
			p.next()
		}
		log.Infof("Executed instruction %s\n", instruction)
	}
}

// Start starts the playlist
func (p *Playlist) Start() {
	go p.playlistEventHandler()
}
