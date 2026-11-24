# Claude Code + Ollama on Windows

This repository already uses Ollama for local LLM calls. To use Claude Code with a custom local GGUF model, create an Ollama model from the GGUF file and then point Claude Code at Ollama's Anthropic-compatible API.

## 1. Create the Ollama model

Run the helper script from the repo root and pass the path to your downloaded GGUF file:

```powershell
.\scripts\setup-claude-code-ollama.ps1 -GgufPath "D:\Downloads\yuxinlu1-gemma-4-12B-coder-fable5-composer2.5-v1-GGUF.gguf" -ModelName gemma-coder
```

The script writes a local `Modelfile` under `ollama\gemma-coder\Modelfile` and runs `ollama create gemma-coder -f ...` for you.

## 2. Launch Claude Code against Ollama

Set the Anthropic environment variables in the current PowerShell session and start Claude Code with the model name you created:

```powershell
$env:ANTHROPIC_AUTH_TOKEN = "ollama"
$env:ANTHROPIC_API_KEY = ""
$env:ANTHROPIC_BASE_URL = "http://localhost:11434"
claude --model gemma-coder
```

If you want to use the Ollama launcher instead, the equivalent command is:

```powershell
ollama launch claude --model gemma-coder
```

## Notes

- Keep Ollama running on `localhost:11434` before starting Claude Code.
- The model name in Claude Code must match the name you passed to `ollama create`.
- For best results, use a model with a large context window. Ollama's Claude Code integration recommends at least 64k tokens.