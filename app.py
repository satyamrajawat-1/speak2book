from fastapi import FastAPI,File,UploadFile
from pydantic import BaseModel
from text_to_json import text_to_json_fn
from fastapi.responses import JSONResponse
import random
import time
import os


app=FastAPI()

@app.get("/")
def hello():
    return {'messgae':"This is the api for irctc automation"}

@app.post("/generate")
async def generate(file: UploadFile = File(...)):
    temp_file = f"temp_{random.randint(0,100000)}.wav"
    with open(temp_file, "wb") as f:
        f.write(await file.read())

    
    try :
        result=text_to_json_fn(temp_file)
        return JSONResponse(content=result)
    finally:
        os.remove(temp_file)
        


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)

