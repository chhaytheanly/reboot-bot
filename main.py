import uvicorn

def main():
    print("Welcome to telegram-tool! Starting FastAPI and Telegram Bot concurrently...")
    uvicorn.run("src.api:api_app", host="0.0.0.0", port=8000, reload=True)

if __name__ == "__main__":
    main()
