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

### 2. Run the Interceptor

```bash
sh run-interceptor.sh
```
defaults:
Target URL : http://localhost:11434
Log Dir   : ./logs
Listen Addr: :11435

or 

```bash
sh run-interceptor.sh -target "http://ai-test-3:11434" -log "./newlogs" -listen ":7800"
```

* This starts a reverse proxy that logs requests/responses intended for the Ollama server.
* It creates a directory where logs are stored in a format the viewer understands.

---

## 📊 Viewing the Logs

Once you have logs:

### 3. Launch the Viewer

```bash
streamlit run olla.py
```

* Select the default `logs/` folder or provide a custom path to view logs.
* Only logs written in the expected format (by the Go script) will be displayed correctly.

---

## 📌 Notes

* Make sure the client app is configured to point to the proxy (e.g., `http://localhost:11435`) **instead of** directly to Ollama.
* The proxy will forward the request and respond transparently, while logging everything in between.
