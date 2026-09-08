from fastapi import FastAPI

app = FastAPI(
    title="AI E-Commerce API",
    description="Production-ready e-commerce backend API",
    version="0.1.0",
)


@app.get("/")
def root():
    return {"message": "AI E-Commerce API is running"}
