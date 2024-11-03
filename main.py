from fastapi import FastAPI
from pydantic import BaseModel, ValidationError, model_validator
from enum import Enum, IntEnum

from typing import Any
from typing_extensions import Self

import z3


def is_digit(x : z3.AstRef): 
    return z3.And(x >= '0', x <= '9')

def check_symbolically(property: z3.ExprRef) -> dict:
    s = z3.Solver()
    s.add(property)
    if s.check() == z3.unsat:
        return {'result': 1, 'message' : 'Model constraints are unsatisfiable. No need to check on data.'}
    else:
        p = z3.Solver()
        p.add(z3.Not(property))
        if p.check() == z3.unsat:
            return {'result': 2, 'message' : 'Model constraints are always true. No need to check on data.'}
        else:
            return {'result': 3, 'message' : 'Model constraints shall be checked on the data.'}




class Postal_Code(Enum):
    code1 = '1001'
    code2 = '1002'
    code3 = '1003'
    code4 = '1004'
    code5 = '999'

    @classmethod
    def z3_format(cls) -> dict:
        var = z3.String('postal_code')
        dd = {}
        dd['ast'] = var
        dd['property'] = [z3.Or(
            var == cls.code1.value, 
            var == cls.code2.value, 
            var == cls.code3.value, 
            var == cls.code4.value, 
            var == cls.code5.value 
        )]
        return dd




class Contact_Number(BaseModel):
    number : str

    @classmethod
    def z3_format(cls) -> dict:
        var = z3.String('contact_number')
        dd = {}
        dd['ast'] = var
        dd['property'] = [z3.StrToInt(var) != -1]       # a way to check is_int
        dd['constraints'] = [z3.Length(var) == 10]
        dd['symbolic_result'] = check_symbolically(z3.And(dd['property'] + dd['constraints']))
        return dd


    @model_validator(mode='after')
    def validate_data(self) -> Self:
        dd = self.z3_format()
        if dd['symbolic_result']['result'] == 1:
            raise ValueError(dd['symbolic_result']['message'])
        elif dd['symbolic_result']['result'] == 2:
            pass
        else:
            s = z3.Solver()
            s.add(z3.And(dd['property'] + dd['constraints']))
            s.add(dd['ast'] == self.number)
            if s.check() != z3.sat:
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


    @classmethod
    def z3_format(cls) -> dict:
        var = {
            'username' : z3.String('username'),
            'password1' : z3.String('password1'),
            'password2' : z3.String('password2'),
            'postal_code' : Postal_Code.z3_format()['ast'],
            'contact_number' : Contact_Number.z3_format()['ast']
        }
        dd = {}
        dd['ast'] = var
        dd['property'] = Postal_Code.z3_format()['property'] + Contact_Number.z3_format()['property'] + Contact_Number.z3_format()['constraints']
        dd['constraints'] = [
            var['password1'] == var['password2'],
            z3.SubString(var['contact_number'], 0, 4) == var['postal_code']
        ]
        dd['symbolic_result'] = check_symbolically(z3.And(dd['property'] + dd['constraints']))
        return dd


    @model_validator(mode='after')
    def validate_user(self) -> Self:
        dd = self.z3_format()
        if dd['symbolic_result']['result'] == 1:
            raise ValueError(dd['symbolic_result']['message'])
        elif dd['symbolic_result']['result'] == 2:
            pass
        else:
            s = z3.Solver()
            s.add(
                dd['ast']['username'] == self.username,
                dd['ast']['password1'] == self.password1,
                dd['ast']['password2'] == self.password2,
                dd['ast']['postal_code'] == self.postal_code.value,
                dd['ast']['contact_number'] == self.contact_number.number
            )
            s.add(z3.And(dd['property'] + dd['constraints'][0:1]))
            if s.check() != z3.sat:
                raise ValueError('Passwords do not match.')
            s.add(dd['constraints'][1])
            if s.check() != z3.sat:
                raise ValueError('First 4 digits of contact number shall be equal to postal code.')
        return self    






class SubUser(User):
    unique_id: int

    @classmethod
    def z3_format(cls) -> dict:
        var = z3.Int('unique_id')
        dd = super().z3_format()
        dd['ast']['unique_id'] = var
        dd['constraints'] += [
            z3.Length(z3.IntToStr(var)) >= 3,
            2*var < z3.StrToInt(dd['ast']['postal_code']) + 999
        ]
        dd['symbolic_result'] = check_symbolically(z3.And(dd['property'] + dd['constraints']))
        return dd
    

    @model_validator(mode='after')
    def validate_sub_user(self) -> Self:
        dd = self.z3_format()
        if dd['symbolic_result']['result'] == 1:
            raise ValueError(dd['symbolic_result']['message'])
        elif dd['symbolic_result']['result'] == 2:
            pass
        else:
            s = z3.Solver()
            s.add(
                dd['ast']['username'] == self.username,
                dd['ast']['password1'] == self.password1,
                dd['ast']['password2'] == self.password2,
                dd['ast']['postal_code'] == self.postal_code.value,
                dd['ast']['contact_number'] == self.contact_number.number,
                dd['ast']['unique_id'] == self.unique_id,
            )
            s.add(z3.And(dd['property'] + dd['constraints'][:3]))
            if s.check() != z3.sat:
                raise ValueError('Unique ID should have at least 3 digits.')
            s.add(dd['constraints'][3])
            if s.check() != z3.sat:
                raise ValueError('Unique ID is not comaptible with Postal code.')
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




