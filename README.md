# fydantic
Extending Pydantic data validation using Formal Methods


## Overview

This is an exercise to demonstrate the application of Z3 (method 2) and explore its advantages, coverage and correctness (over standard approaches - method 1) towards achieving Data/Model Validation in a FastAPI web app. This idea, in more than obvious ways, aligns with the Formal Software Verification.

In summary, a property (desired to be fulfilled by the data/model) can be modelled into a  
Z3 boolean expression (i.e. a theorem), which Z3 is capable of solving/simplifying symbolically, and quite powerful in checking its satisfiability. Such operations can be pipelined to get automatically invoked thanks to Pydantic's validation decorators and Z3py (Z3 API for Python).



## Approach

### Pydantic Data Model

I created an example data model with Pydantic that includes validators for validating the API payload against following constraints:

1. `Postal_Code`: an enumeration class with five preset string values, "1001", "1002", "1003", "1004", "999"
2. `Contact_Number`: a class wrapper around a string, that includes following validations:
	1. check the provided/parsed data contains only numeric characters.
	2. check the provided/parsed data is exactly 10 characters long.
3. `User`: a class wrapping three string attributes `username`, `password1`, `password2`, one `Postal_Code`, and one `Contact_Number`, that includes following validations:
	1. checks (internally invoked by Pydantic) corresponding to `Postal_Code` and `Contact_Number`
	2. check the provided data does not contains string "card_number"
	3. check the parsed data for both the passwords are same,
	4. and, check the first 4 character of `Contact_Number` shall be equal to `Postal_Code`
5. `SubUser`: a subclass of `User` with `unique_id` as the additional attribute, such that:
	1. checks (internally invoked by Pydantic) corresponding to `User`
	2. check the parsed data for `unique_id` is at least 4 digit long
	3. and, check the parsed data for `unique_id` satisfies `2*unique_id < postal_code + 900`

### FastAPI app

The application is created by instantiating the `FastAPI` class with following endpoints:

1. A POST endpoint at `/get_user/` that accept a `User` object and returns it.
2. A POST endpoint at `/get_sub_user/` that accepts a `SubUser` object and returns it. 


### Z3 API for Python

Z3 is a high-performance theorem prover and an SMT solver developed by Microsoft Research. It is used for checking the satisfiability of logical formulas over one or more theories. Z3 is widely used in formal verification, program analysis, and constraint solving.

Z3 can be used in Python thanks to the python package [z3-solver](https://pypi.org/project/z3-solver/). As it has been designed as a language on its own, we need to map concerned artifacts of our Python app like data, functions, classes and Boolean expressions, etc. to Z3's variables, constants, types, structures, functions, and symbolic formulas. Such transformations are natively supported for Python's standard data/types/structures like numbers, strings, Booleans, linear arithmetic, lists, dictionaries, and a lot more.

This transformed object is usually referred as a "theory" in an SMT domain that gets easily accessed and processed by Z3's proof engines to symbolically execute and also, check for satisfiability (and if satisfiable, return a convenient model satisfying this theory).

Essentially, using a Z3 from Python involves following steps:
- Declaring variables, types, functions, structures, etc (equivalent to a term in a FOL setting)
- Constructing theories, theorems, properties, constraints, etc. (equivalent to a Boolean formula in a FOL setting) 
- Symbolic Execution and/or Model Checking (sat/unsat/unknow) 


### Integrating Z3 inside Pydantic Data Model

Keeping the outer structure intact, all the code changes can be broken down into following two major steps:
- Transforming class attributes & validations into Z3 theories (along with its satisfiability state - always true/false) accessible by a class method `z3_format`.
- Binding Z3 satisfiability check (on top of Z3 variables assigned to provided data) with Pydantic model validation decorators.

To be specific, Z3 was integrated in the following way:

1. `Postal_Code`: an enumeration class with five preset string values, "1001", "1002", "1003", "1004", "999", and following:
	1. a class method `z3_format` returning:
		1. `ast`: a Z3 string variable
		2. `property`: `ast` equals any of the following "1001", "1002", "1003", "1004", "999"
2. `Contact_Number`: a class wrapper around a string, and following: 
	1. a class method `z3_format` returning:
		1. `ast`: a Z3 string variable
		2. `property`: `ast` contains only numeric characters
		3. `constraints`: `ast` is exactly 10 characters long
		4. `satisfiability state`:  returned by `check_symbolically` on `property` and `constraints` - `always true`/`always false`/`depends on data`
	2. a validation decorator:
		1. if `satisfiability state depends on data` then check satisfiability again with following additional constraint:
			1. `ast` is equal to the parsed data
3. `User`: a class wrapping three string attributes `username`, `password1`, `password2`, one `Postal_Code`, and one `Contact_Number`: 
	1. a validation decorator:
		1. check the provided data does not contains string "card_number"
	2. a class method `z3_format` returning:
		1. `ast` : a dictionary containing `username`, `password1`, `password2` as Z3 string and `postal_code`, `contact_number` as their respective `ast`
		2. `property`: respective properties/constraints of `postal_code` and `contact_number`
		3. `constraints`: 
			1. both passwords are same,
			2. and, the first 4 character of `contact_number` shall be equal to `postal_code`
		4. `satisfiability state`:  returned by `check_symbolically` on `property` and `constraints` - `always true`/`always false`/`depends on data`
	3. a validation decorator:
		1. if `satisfiability state depends on data` then check satisfiability again with following additional constraint:
			1. `postal_code` is equal to its corresponding parsed data
	4. a validation decorator:
		1. if `satisfiability state depends on data` then check satisfiability again with following additional constraint:
			1. `ast` is equal to the parsed data
5. `SubUser`: a subclass of `User` with `unique_id` as the additional attribute, and following:
	1. a class method `z3_format` returning:
		1. `ast`: a dictionary containing `unique_id` as Z3 Int along with other `ast` members of `User`
		2. `property`: same as `User`
		3. `constraints`(additionally to the constraints of `User`): 
			1. `unique_id` shall be at least 4 digit long
			2. and, that `2*unique_id < postal_code + 900`
		4. `satisfiability state`:  returned by `check_symbolically` on `property` and `constraints` - `always true`/`always false`/`depends on data`
	2. a validation decorator:
		1. if `satisfiability state depends on data` then check satisfiability again with following additional constraint:
			1. `ast` is equal to the parsed data



## Efforts

In case of method 2, as compared to method 1, the effort is almost double, mostly because of mapping Python level abstraction to that of Z3. However, when it come to writing constraints and properties, it is more frugal and convenient to use Z3's robust yet expressive syntax, as it is very close to standard literature practices.



## Coverage and Correctness


### Method 1

1. A well modelled Pydantic classes and well thought validation steps can pretty much ensure bug-free APIs. But this puts a lot of burden entirely on the programmer.
2. Every check or validation step can only happen during runtime, and that too when data is provided (in case of both 'before' and 'after' modes). Hence, if the constraints are too tight then it might be quite a challenge for the end user to guess the allowed configurations (if any).
	1. For example, in case of `/get_sub_user/` the end user will have to spend a good amount of time only to discover that constraints are too strict to be true.
	2. Another example, in case of user entering `postal_code` as `999`; the errors thrown can be pointing towards prefix of `contact_number` not same as `postal_code`.
4. As the core of python language itself cannot be considered as a trusted kernel, therefore the correctness of this method is always limited by this fact.
5. Also, implementation styles in Python is usually imperative (not functional) which speaks more about how to do things (case where clarity and hence the correctness is not very direct), rather than what to do things (case where clarity and the correctness are usually direct)


### Method 2

1. Z3, thanks to its support for many FOL constructs enable us to build theories conveniently with complex and multiple logics at once. More than often times, it is like translating requirements into logical formulas of FOL.
2. Thanks to its symbolic execution, it is possible to explore and check the satisfiability (that too with/without complete/partial data) of the constraints individually, or as a union, or in any other combination.
	1. For example, in case of `/get_sub_user/`, thanks to symbolic execution, the end user get immediately notified about the correct error message - `the model constraints are unsatisfiable`.
	2. Another example, in case of user entering `postal_code` as `999`, thanks to satisfiability check with partial data, the end user get notified about the allowed configurations (i.e. value assignment of other variables).
3. In case of satisfiability, Z3 also returns a example model (appropriate variable assignment) that satisfies the theory in check.
4. Usually the core of such solvers or theorem provers are what is called "trusted kernels".
5. Also, thanks to their functional style of expressing logic, it become more direct and correct to implement the goal.




## Challenges and Mitigations


1. Capturing conflicting case between OOP model (both with Enum and Inheritance) and the validations/constraints.

