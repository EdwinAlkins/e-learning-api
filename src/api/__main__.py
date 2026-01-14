if __name__ == "__main__":
    import asyncio
    from src.api.fastapi_app import app
    from src.config import settings

    from hypercorn.config import Config
    from hypercorn.asyncio import serve

    config = Config()
    config.bind = ["0.0.0.0:8000"]
    config.loglevel = settings.LOG_LEVEL
    config.accesslog = "-"
    config.errorlog = "-"

    asyncio.run(serve(app, config))
