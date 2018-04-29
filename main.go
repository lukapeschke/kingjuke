package main

import (
	"io/ioutil"
	"net/http"

	log "github.com/Sirupsen/logrus"
	"github.com/gorilla/mux"
)

func putPlaylistHandler(w http.ResponseWriter, r *http.Request) {
	p := GetPlaylist()
	playlistHandlers := map[string]func(){
		"pause":       p.Pause,
		"unpause":     p.UnPause,
		"togglePause": p.TogglePause,
		"next":        p.Next,
	}

	vars := mux.Vars(r)
	handler := vars["handler"]
	handlerFunc := playlistHandlers[handler]
	if handlerFunc == nil {
		w.WriteHeader(http.StatusNotFound)
		return
	}
	handlerFunc()
	w.WriteHeader(http.StatusOK)
}

func postPlaylistHandler(w http.ResponseWriter, r *http.Request) {
	p := GetPlaylist()
	playlistHandlers := map[string]func(*Song){
		"add": p.AddSong,
	}
	vars := mux.Vars(r)
	handler := vars["handler"]
	handlerFunc := playlistHandlers[handler]
	if handlerFunc == nil {
		w.WriteHeader(http.StatusNotFound)
		return
	}
	id, err := ioutil.ReadAll(r.Body)
	if err != nil {
		w.WriteHeader(http.StatusBadRequest)
		return
	}
	song, err := NewSong(string(id))
	if err != nil || p.isSongInPlaylist(song.Name) {
		w.WriteHeader(http.StatusConflict)
		return
	}
	handlerFunc(song)
}

func main() {
	p := GetPlaylist()
	p.Start()
	r := mux.NewRouter()
	r.HandleFunc("/playlist/{handler}", putPlaylistHandler).Methods("PUT")
	r.HandleFunc("/playlist/{handler}", postPlaylistHandler).Methods("POST")
	log.Fatal(http.ListenAndServe(":8000", r))
}
