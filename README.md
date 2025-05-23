# Ollama Request Interceptor & Log Viewer

This tool helps you **intercept, log, and visualize** requests and responses sent to a local [Ollama](https://ollama.com) server. It's useful for debugging, auditing, or understanding how prompts are being handled by your models.

## 🧰 Dependencies

* [Go](https://golang.org)
* [Python](https://www.python.org) (3.7+)
* [Streamlit](https://streamlit.io)

Install Python dependencies (once):

```bash
pip install streamlit
```

---

## ⚙️ Getting Started

### 1. Clone the Repository

### 2. Set Up the Interceptor (Go)

Edit the `ollama-request-interceptor.go` file:

#### 🔧 Configuration

```go
// Target Ollama server URL
targetURL := "http://localhost:11434"  // Change if your Ollama server is hosted elsewhere

// Address the proxy listens on
listenAddr := ":11435"  // Clients should send requests to this port instead
```

### 3. Run the Interceptor

```bash
go run ollama-request-interceptor.go
```

* This starts a reverse proxy that logs requests/responses intended for the Ollama server.
* It creates a `logs/` directory where logs are stored in a special format.

---

## 📊 Viewing the Logs

Once you have logs:

### 4. Launch the Viewer

```bash
streamlit run olla.py
```

* Select the default `logs/` folder or provide a custom path to view logs.
* Only logs written in the expected format (by the Go script) will be displayed correctly.

---

## 📌 Notes

* Make sure the client app is configured to point to the proxy (e.g., `http://localhost:11435`) **instead of** directly to Ollama.
* The proxy will forward the request and respond transparently, while logging everything in between.

  
