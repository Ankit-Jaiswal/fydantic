from fastapi import FastAPI
from pydantic import BaseModel, ValidationError, model_validator

from typing import Any
from typing_extensions import Self




class UserModel(BaseModel):
    username: str
    password1: str
    password2: str


    @model_validator(mode='before')
    @classmethod
    def check_card_number_absent(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if 'card_number' in data:
                raise ValueError("Card number should not be present")
        return data


    @model_validator(mode='after')
    def check_passwords_match(self) -> Self:
        pw1 = self.password1
        pw2 = self.password2
        if pw1 is not None and pw2 is not None and pw1 != pw2:
            raise ValueError('passwords do not match')
        return self
    

    
app = FastAPI()



@app.get('/')
async def root():
    return {"message" : "Hello World"}


@app.post('/check_user/')
async def check_user(user: UserModel):
    return UserModel





if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)




