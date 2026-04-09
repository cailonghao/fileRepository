```shell
docker run -d -v ollama:/root/.ollama -p 11434:11434 --name ollama ollama/ollama:0.20.3
docker exec -it ollama ollama run gemma4:e4b
```