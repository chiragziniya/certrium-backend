from fastapi import FastAPI

app = FastAPI(title="Vaultix API")

@app.get("/")
async def root():
    return {"message": "Vaultix FastAPI running"}
