# Async Console Chatbot

Simple async console chatbot using `pydantic_ai` with retry logic, persistent history, and Logfire instrumentation.

## Features
- Model selection via `MODEL` env var (default: `google-gla:gemini-2.5-flash`)
- Optional system prompt via `SYSTEM_PROMPT`
- Persistent conversation history to JSON (`HISTORY_FILE`)
- Graceful exit on `exit`, `quit`, or `bye`
- Basic exponential backoff retries (`MAX_RETRIES`, `BACKOFF_FACTOR`)
- Logfire instrumentation (falls back to local-only if not authenticated)
- Gemini key alias support: `GEMINI_API_KEY` maps automatically to `GOOGLE_API_KEY`

## Environment Variables
| Name | Purpose | Default |
|------|---------|---------|
| MODEL | Provider + model id (e.g. `google-gla:gemini-2.5-flash`) | google-gla:gemini-2.5-flash |
| SYSTEM_PROMPT | System instructions for assistant | "You are a helpful assistant." |
| HISTORY_FILE | JSON file for storing chat history (set empty to disable) | .chat_history.json |
| MAX_RETRIES | API retry attempts | 3 |
| BACKOFF_FACTOR | Base seconds for exponential backoff | 1.5 |
| GOOGLE_API_KEY | Google Gemini API key (can use `GEMINI_API_KEY` instead) | — |
| GEMINI_API_KEY | Alias for `GOOGLE_API_KEY` | — |
| OPENAI_API_KEY | OpenAI API key (used if MODEL starts with `openai`) | — |
| FALLBACK_MODEL | Optional fallback model if primary provider key missing | — |

## Gemini Setup
Add your Gemini key to a `.env` file as either:
```
GEMINI_API_KEY=your_gemini_key_here
```
Or:
```
GOOGLE_API_KEY=your_gemini_key_here
```
If you only set `GEMINI_API_KEY`, the app will alias it to `GOOGLE_API_KEY` automatically.

## Running
1. Create and populate `.env`.
2. Install dependencies:
```bash
pip install -r requirements.txt
```
3. Start chatbot:
```bash
python chatbot.py
```
4. Type messages; use `exit`, `quit`, or `bye` to end.

## Files
- `chatbot.py`: Minimal basic chatbot.
- `chatbot_basic.py`: Also minimal; similar to `chatbot.py` (keep one if desired).
- `chatbot_advanced.py`: Advanced features (history, retries, fallbacks).

## Basic Version
A minimal version is provided in `chatbot_basic.py`:
```bash
python chatbot_basic.py
```
Set `GOOGLE_API_KEY` (or `GEMINI_API_KEY`) in `.env` for Gemini models, or `OPENAI_API_KEY` for OpenAI models.

## History Persistence
Set `HISTORY_FILE` in `.env` to control where history is stored. Example:
```
HISTORY_FILE=.chat_history.json
```
Disable persistence by setting it to an empty value:
```
HISTORY_FILE=
```

## Fallback Logic
- If `MODEL` starts with `google` but no Gemini key is found, the bot tries fallback to an OpenAI model if an `OPENAI_API_KEY` is present.
- If `MODEL` starts with `openai` but you only have a Gemini key, it switches to the default Gemini model.

## Error Handling & Retries
On transient errors, the bot retries with exponential backoff: `sleep = BACKOFF_FACTOR * 2^(attempt-1)`.

## Notes
- Update dependencies if you hit import errors:
```bash
pip install -U logfire pydantic-ai pydantic-graph
```
- Logfire instrumentation is best-effort; warnings will not stop the chatbot.

## License
MIT (adjust as needed).
