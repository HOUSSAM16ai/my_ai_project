from fastapi import FastAPI

app = FastAPI(
    title="CogniForge AI Service",
    description="The intelligent core for analyzing and understanding user interactions.",
    version="0.1.0",
)

@app.get("/")
def read_root():
    """Returns a welcome message indicating the service is running."""
    return {"message": "CogniForge AI Analysis Service is running!"}