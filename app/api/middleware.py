from fastapi import FastAPI, Request

def add_middlewares(app: FastAPI):
    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        # In a real app, you'd log more details here
        print(f"Request: {request.method} {request.url}")
        response = await call_next(request)
        return response
