from nexora.server import create_app

app, rt = create_app()

if __name__ == "__main__":
    import uvicorn
    from nexora.config import settings
    uvicorn.run(app, host=settings.host, port=settings.port)
