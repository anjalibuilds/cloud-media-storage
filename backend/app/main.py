from fastapi import FastAPI

app = FastAPI(
    title="Cloud Based Media File Storage Service",
    version="1.0.0"
)


@app.get("/")
def root():
    return {
        "message": "Cloud Media Storage API is running"
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy"
    }