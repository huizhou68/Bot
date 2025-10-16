# FuBot 🤖

FuBot is a FastAPI-powered AI assistant for customer service.
It uses OpenAI's GPT models to answer user queries, with PostgreSQL for storing chat history.

## Features
- Passcode-protected access per user
- Chat interface built with HTML + JavaScript + CSS
- PostgreSQL database for chat logs
- OpenAI API integration

## Run Locally
```bash
python3 -m uvicorn backend.main:app --reload