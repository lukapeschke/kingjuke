package main

import (
	"errors"
	"log"
	"os"
	"os/exec"
	"time"

	"github.com/faiface/beep/mp3"
	"github.com/faiface/beep/speaker"

	"github.com/faiface/beep"

	"github.com/otium/ytdl"
)

// Song represents a song of the playlist
type Song struct {
	Vid                          *ytdl.VideoInfo
	Name                         string
	AudioFilename, VideoFilename string
	ctrl                         *beep.Ctrl
	done                         bool
}

// NewSong creates a new song from a youtube video ID
func NewSong(id string) (*Song, error) {
	var song Song
	var err error

	log.Printf("Creating song for ID %s", id)
	song.Vid, err = ytdl.GetVideoInfo(id)
	if err != nil {
		log.Printf("Could not fetch video info for %s\n", id)
		return nil, err
	}
	song.Name = song.Vid.Title
	song.AudioFilename = "cache/" + song.Name + ".mp3"
	song.VideoFilename = "cache/" + song.Name + ".mp4"
	song.done = false
	log.Printf("Created song for %s", song.Name)
	return &song, nil
}

func (s *Song) audioFileExists() bool {
	_, err := os.Stat(s.AudioFilename)
	return err == nil
}

func (s *Song) videoFileExists() bool {
	_, err := os.Stat(s.VideoFilename)
	return err == nil
}

// GetBestAudio returns the best Format object for a Song
func (s *Song) GetBestAudio() (ytdl.Format, error) {
	formats := s.Vid.Formats.Best(ytdl.FormatAudioEncodingKey)
	if len(formats) < 1 {
		return ytdl.Format{}, errors.New(
			"No valid format found for " + s.Name)
	}
	return formats[0], nil
}

// Download downloads a Song to the File Song.VideoFilename
func (s *Song) Download() (err error) {
	if s.audioFileExists() || s.videoFileExists() {
		log.Printf("Found %s in cache, skipping download\n", s.Name)
		return
	}
	format, err := s.GetBestAudio()
	if err != nil {
		log.Printf("No best audio found for %s\n", s.Name)
		return
	}
	file, err := os.Create(s.VideoFilename)
	if err != nil {
		log.Println("Error while creating file ", s.VideoFilename, ":", err)
		return
	}
	defer file.Close()
	log.Printf("Downloading %s to file %s", s.Vid.Title, s.VideoFilename)
	s.Vid.Download(format, file)
	log.Printf("Finished downloading %s", s.Vid.Title)
	return
}

// Convert converts the song to mp3
func (s *Song) Convert() (err error) {
	if s.audioFileExists() {
		log.Printf("Found %s in cache, skipping convert\n", s.Name)
		return
	}
	ffmpegPath, err := exec.LookPath("ffmpeg")
	if err != nil {
		log.Println("Error while looking for ffmpeg: ", err)
		return
	}
	log.Printf("Starting conversion for %s", s.Name)
	cmd := exec.Command(ffmpegPath, "-y", "-i", s.VideoFilename, "-vn", s.AudioFilename)
	cmd.Run()
	log.Printf("Converted %s to %s", s.AudioFilename, s.VideoFilename)
	return
}

// Play plays the song
func (s *Song) Play(c chan string) (err error) {
	log.Printf("Playing %s...\n", s.Name)
	f, err := os.Open(s.AudioFilename)
	if err != nil {
		log.Println("Error while opening ", s.AudioFilename, ": ", err)
		return
	}
	defer f.Close()
	stream, format, err := mp3.Decode(f)
	if err != nil {
		log.Println("Error while decoding ", s.AudioFilename, ": ", err)
		return
	}
	speaker.Init(format.SampleRate, format.SampleRate.N(time.Second/10))

	s.ctrl = &beep.Ctrl{Streamer: stream}

	done := make(chan struct{})
	speaker.Play(beep.Seq(s.ctrl, beep.Callback(func() {
		close(done)
	})))
	<-done
	s.done = true
	c <- "songFinished"
	log.Printf("Finished playing %s\n", s.Name)
	return
}

func (s *Song) isPaused() bool {
	return s.ctrl.Paused
}

// Pause pauses the song
func (s *Song) Pause() {
	speaker.Lock()
	s.ctrl.Paused = true
	speaker.Unlock()
}

// UnPause unpauses the song
func (s *Song) UnPause() {
	speaker.Lock()
	s.ctrl.Paused = false
	speaker.Unlock()
}

// TogglePause toggles pause/unpause
func (s *Song) TogglePause() {
	if s.isPaused() {
		s.UnPause()
	} else {
		s.Pause()
	}
}
