from fastapi import FastAPI

# from data_model import *
from data_model_z3 import *



app = FastAPI()



@app.get('/')
async def root():
    return {"message" : "Hello World"}


@app.post('/get_user/')
async def get_user(user: User):
    return user


@app.post('/get_sub_user/')
async def get_sub_user(sub_user: SubUser):
    return sub_user




if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)




