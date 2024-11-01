from fastapi import FastAPI
from pydantic import BaseModel, ValidationError, model_validator
from enum import Enum, IntEnum

from typing import Any
from typing_extensions import Self



class Postal_Code(Enum):
    code1 = '1001'
    code2 = '1002'
    code3 = '1003'
    code4 = '1004'
    code5 = '999'



class Contact_Number(BaseModel):
    number : str

    @model_validator(mode='after')
    def check_digits(self) -> Self:
        if len(self.number) != 10:
            raise ValueError('Contact number should have 10 digits')
        return self



class User(BaseModel):
    username: str
    password1: str
    password2: str
    postal_code: Postal_Code
    contact_number: Contact_Number


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
            raise ValueError('Passwords do not match')
        return self
    

    @model_validator(mode='after')
    def check_contact_starts_with_postal(self) -> Self:
        if not(self.contact_number.number.startswith(self.postal_code.value)):
            raise ValueError('Contact number should start with postal code')
        return self
    



class SubUser(User):
    unique_id: int

    @model_validator(mode='after')
    def check_number_of_digits(self) -> Self:
        if len(str(self.unique_id)) < 3:
            raise ValueError('Unique ID should have 3 digits')
        return self


    @model_validator(mode='after')
    def check_compatiblity_with_postal(self) -> Self:
        if 2*self.unique_id >= int(self.postal_code.value) + 999:
            raise ValueError('Unique ID is not comaptible with Postal code')
        return self



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




