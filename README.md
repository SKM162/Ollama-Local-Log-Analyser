Dependencies:
1) go
2) python, streamlit

After cloning the repo,

Intercepting and logging requests:
1) change the targetURL in the ollama-request-interceptor.go script to point to your local ollama base url. Like "http://localhost:11434" in case of running the script in the same machine as ollama server. This is the url to which the requests are redirected once they are logged.
2) change the listenAddr if necessary. This should be the port to which the clients must send the requests intended origninally for ollama server.
3) start the interceptor by running the command - "go run ollama-request-interceptor.go"
4) This should create a logs directory where the script is ran and should log the requests.

Viewing requests:
1) run "streamlit run olla.py" to start the log viewer application. 
2) select the default log location or enter custom path to your logs directory to start viewing the logs.
Note: Only logs in special format could be viewed, which is honoured by the go script.
  
