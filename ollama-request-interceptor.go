package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"log"
	"net/http"
	"os"
	"path/filepath"
	"strings"
	"sync/atomic"
	"time"
)

const (
	listenAddr = ":11435"            // Localhost port exposed to clients to receive requests.
	targetURL  = "http://host:11434" // Change this to actual local ollama server base url
	logDir     = "logs"
)

var reqID int64

type LogEntry struct {
	Timestamp string         `json:"timestamp"`
	ID        int64          `json:"id"`
	Path      string         `json:"path"`
	Method    string         `json:"method"`
	Request   LoggedData     `json:"request"`
	Response  LoggedResponse `json:"response"`
}

type LoggedData struct {
	Headers map[string][]string `json:"headers"`
	Body    any                 `json:"body,omitempty"`
}

type LoggedResponse struct {
	Status  int                 `json:"status"`
	Headers map[string][]string `json:"headers"`
	Body    any                 `json:"body,omitempty"`
}

func main() {
	_ = os.Unsetenv("HTTP_PROXY")
	_ = os.Unsetenv("HTTPS_PROXY")
	_ = os.MkdirAll(logDir, 0755)

	http.HandleFunc("/", handleProxy)
	log.Printf("Proxy started: %s → %s", listenAddr, targetURL)
	log.Fatal(http.ListenAndServe(listenAddr, nil))
}

func handleProxy(w http.ResponseWriter, r *http.Request) {
	id := atomic.AddInt64(&reqID, 1)
	start := time.Now()

	// Read and copy the request body
	var reqBody []byte
	if r.Body != nil {
		reqBody, _ = io.ReadAll(r.Body)
		r.Body = io.NopCloser(bytes.NewReader(reqBody))
	}

	// Prepare request to target
	url := targetURL + r.URL.RequestURI()
	req, _ := http.NewRequestWithContext(r.Context(), r.Method, url, bytes.NewReader(reqBody))
	req.Header = r.Header.Clone()

	// Perform request
	resp, err := http.DefaultClient.Do(req)
	if err != nil {
		http.Error(w, "Proxy error: "+err.Error(), http.StatusBadGateway)
		return
	}
	defer resp.Body.Close()

	// Read response body
	respBody, _ := io.ReadAll(resp.Body)

	// Write back to client
	copyHeader(w.Header(), resp.Header)
	w.WriteHeader(resp.StatusCode)
	_, _ = w.Write(respBody)

	// Save logs
	logEntry := LogEntry{
		Timestamp: start.UTC().Format(time.RFC3339),
		ID:        id,
		Path:      r.URL.Path,
		Method:    r.Method,
		Request: LoggedData{
			Headers: r.Header,
			Body:    parseBody(reqBody),
		},
		Response: LoggedResponse{
			Status:  resp.StatusCode,
			Headers: resp.Header,
			Body:    parseBody(respBody),
		},
	}

	data, _ := json.MarshalIndent(logEntry, "", "  ")
	safePath := strings.ReplaceAll(strings.Trim(r.URL.Path, "/"), "/", "_")
	if safePath == "" {
		safePath = "root"
	}
	filename := fmt.Sprintf("%d-%s.json", id, safePath)
	_ = os.WriteFile(filepath.Join(logDir, filename), data, 0644)
}

func copyHeader(dst, src http.Header) {
	for k, v := range src {
		dst[k] = v
	}
}

func parseBody(data []byte) any {
	trimmed := bytes.TrimSpace(data)
	if len(trimmed) == 0 {
		return nil
	}

	// Try single JSON object
	var single any
	if err := json.Unmarshal(trimmed, &single); err == nil {
		return single
	}

	// Try JSON Lines (streaming chunks)
	lines := bytes.Split(trimmed, []byte("\n"))
	var result []any
	for _, line := range lines {
		line = bytes.TrimSpace(line)
		if len(line) == 0 {
			continue
		}
		var obj any
		if err := json.Unmarshal(line, &obj); err == nil {
			result = append(result, obj)
		} else {
			// If any line fails, fall back to raw
			return string(trimmed)
		}
	}

	return result
}
