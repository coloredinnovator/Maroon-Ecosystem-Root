// Maroon Tube Core — HLS Video Streaming Engine (v4.0)
// Codex §4.1: Netflix/TikTok architecture with FFmpeg transcoding.
// Upload → Transcode → Store (GCS) → Serve (CDN)
package main

import (
	"crypto/sha512"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"io"
	"log"
	"net/http"
	"os"
	"os/exec"
	"path/filepath"
	"time"
)

// TelemetryEvent implements the Palantir Mandate (Codex §5.1).
type TelemetryEvent struct {
	Source             string      `json:"source"`
	EventType          string      `json:"event_type"`
	Timestamp          string      `json:"timestamp"`
	Data               interface{} `json:"data"`
	VerificationStatus string      `json:"verification_status"`
}

func emitTelemetry(eventType string, data interface{}) {
	event := TelemetryEvent{
		Source:             "maroon-tube-core",
		EventType:          eventType,
		Timestamp:          time.Now().UTC().Format(time.RFC3339),
		Data:               data,
		VerificationStatus: "PENDING_MERKLE_HASH",
	}
	payload, _ := json.Marshal(event)
	log.Printf("[Telemetry] %s", string(payload))
}

// hashContent computes SHA-512 of raw bytes for content integrity.
func hashContent(data []byte) string {
	h := sha512.Sum512(data)
	return hex.EncodeToString(h[:])
}

// transcodeToHLS calls FFmpeg to convert an uploaded video to HLS segments.
func transcodeToHLS(inputPath, outputDir string) error {
	os.MkdirAll(outputDir, 0755)
	playlistPath := filepath.Join(outputDir, "playlist.m3u8")

	cmd := exec.Command("ffmpeg",
		"-i", inputPath,
		"-codec:v", "libx264",
		"-codec:a", "aac",
		"-hls_time", "10",
		"-hls_playlist_type", "vod",
		"-hls_segment_filename", filepath.Join(outputDir, "segment_%03d.ts"),
		"-start_number", "0",
		playlistPath,
	)
	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr
	return cmd.Run()
}

// handleUpload accepts a video file, hashes it, and queues transcoding.
func handleUpload(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "POST only", http.StatusMethodNotAllowed)
		return
	}

	file, header, err := r.FormFile("video")
	if err != nil {
		http.Error(w, "Missing 'video' form field", http.StatusBadRequest)
		return
	}
	defer file.Close()

	// Save to temp
	uploadDir := "./uploads"
	os.MkdirAll(uploadDir, 0755)
	inputPath := filepath.Join(uploadDir, header.Filename)
	dest, _ := os.Create(inputPath)
	defer dest.Close()

	data, _ := io.ReadAll(file)
	dest.Write(data)
	contentHash := hashContent(data)

	log.Printf("[Maroon Tube] Uploaded: %s (%d bytes) Hash: %s...%s",
		header.Filename, len(data), contentHash[:16], contentHash[len(contentHash)-16:])

	emitTelemetry("video_uploaded", map[string]interface{}{
		"filename":    header.Filename,
		"size_bytes":  len(data),
		"content_hash": contentHash,
	})

	// Transcode
	outputDir := filepath.Join("./hls", contentHash[:32])
	go func() {
		log.Printf("[Maroon Tube] Transcoding %s to HLS...", header.Filename)
		if err := transcodeToHLS(inputPath, outputDir); err != nil {
			log.Printf("[Maroon Tube] Transcode FAILED: %v", err)
			emitTelemetry("transcode_failed", map[string]string{"error": err.Error()})
		} else {
			log.Printf("[Maroon Tube] Transcode COMPLETE: %s", outputDir)
			emitTelemetry("transcode_complete", map[string]string{
				"content_hash": contentHash,
				"output_dir":   outputDir,
			})
		}
	}()

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]string{
		"status":       "accepted",
		"content_hash": contentHash,
		"stream_url":   fmt.Sprintf("/stream/%s/playlist.m3u8", contentHash[:32]),
	})
}

// handleStream serves HLS playlists and segments.
func handleStream(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Access-Control-Allow-Origin", "*")
	// Serve static files from the ./hls directory
	http.StripPrefix("/stream/", http.FileServer(http.Dir("./hls"))).ServeHTTP(w, r)
	emitTelemetry("stream_requested", map[string]string{"path": r.URL.Path})
}

// handleHealth returns service health (Codex §5.4).
func handleHealth(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]string{
		"status":  "online",
		"service": "maroon-tube-core",
		"version": "4.0.0",
	})
}

func main() {
	fmt.Println("[Maroon Tube] HLS Video Streaming Engine v4.0 Online.")
	fmt.Println("[Maroon Tube] Upload → Transcode (FFmpeg) → Serve (HLS)")

	http.HandleFunc("/api/v1/upload", handleUpload)
	http.HandleFunc("/stream/", handleStream)
	http.HandleFunc("/health", handleHealth)

	fmt.Println("[Maroon Tube] Listening on port 8080.")
	log.Fatal(http.ListenAndServe(":8080", nil))
}
