from fastapi import FastAPI

app = FastAPI(title="Certrium API")

@app.get("/")
async def root():
    return {"message": "Certrium FastAPI running"}
