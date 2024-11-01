from fastapi import FastAPI
from pydantic import BaseModel, ValidationError, model_validator
from enum import Enum, IntEnum

from typing import Any
from typing_extensions import Self

import z3


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
        number_str = z3.String('number_str')
        s = z3.Solver()
        s.add(z3.Length(number_str) == 10)                # adding constraints
        s.add(number_str == self.number)                  # adding known values
        if s.check() != z3.sat:                           # checking satisfiability
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
        data_str = z3.String('data_str')
        s = z3.Solver()
        s.add(z3.Not(z3.Contains(data_str, 'card_number')))            # adding constraints
        s.add(data_str == str(data))                                   # adding known values
        if s.check() != z3.sat:                                        # checking satisfiability
            raise ValueError('Card number should not be present')
        return data


    @model_validator(mode='after')
    def check_passwords_match(self) -> Self:
        pw1 = z3.String('pw1')
        pw2 = z3.String('pw2')
        s = z3.Solver()
        s.add(pw1 == pw2)                                       # adding constraints
        s.add(pw1 == self.password1, pw2 == self.password2)     # adding known values
        if s.check() != z3.sat:                                 # checking satisfiability
            raise ValueError('Passwords do not match')
        return self


    @model_validator(mode='after')
    def check_contact_starts_with_postal(self) -> Self:
        if self.contact_number.number[0:4] != self.postal_code.value:
            raise ValueError('Contact number should start with postal code')
        return self
    



class SubUser(User):
    unique_id: int

    @model_validator(mode='after')
    def check_number_of_digits(self) -> Self:
        if len(str(self.unique_id)) < 3:
            raise ValueError('Unique ID should have at least 3 digits')
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




