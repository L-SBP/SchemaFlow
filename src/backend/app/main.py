import uvicorn
from server import config

if __name__ == "__main__":
    uvicorn.run(config.app.uvicorn, host=config.app.host, port=config.app.port, reload=config.app.reload)