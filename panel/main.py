from fastapi import FastAPI
import uvicorn
from database import test_connection
from routes.user_routes import router

app = FastAPI(title="IT Admin Panel")

@app.on_event("startup")
async def startup():
    is_connected = await test_connection()
    if is_connected:
        print("Successfully connected to the database.")
    else:
        print("Warning: Could not connect to the database.")

app.include_router(router)

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=5001, reload=True)