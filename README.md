# windower
Python tool that creates windows from a given dataset

# Installation
Clone the repository and cd into it
```
git clone https://github.com/saaskilahtij/windower.git && cd windower
```

If you have the repository already, cd into it and run
```
git pull
```
or
```
git fetch
```

Create new branch for the feature
```
git checkout -b feature/feature-name
```

Install dev-dependencies
```
pip install -r dev-requirements.txt
```

Lint the code before you commit by running
```
pylint *.py
```

Pylint will tell you if you have any styling mistakes. For example:
```
└─[$] <git:(feature/logging*)> pylint test_windower.py
************* Module test_windower
test_windower.py:11:0: C0304: Final newline missing (missing-final-newline)
test_windower.py:1:0: C0114: Missing module docstring (missing-module-docstring)

------------------------------------------------------------------
Your code has been rated at 6.00/10 (previous run: 6.00/10, +0.00)
```

Here I am missing a newline, and a module docstring in test_windower.py in the lines 11 and 1.

After fixing:
```
└─[$] <git:(feature/logging*)> pylint *.py

-------------------------------------------------------------------
Your code has been rated at 10.00/10 (previous run: 6.00/10, +4.00)
```

Success 10/10!

Remember to also run the unit tests by cding into the directory and running:
```
pytest
```

An example error might look something like:
```
└─[$] <git:(feature/logging*)> pytest
========================================================== test session starts ==========================================================
platform linux -- Python 3.12.8, pytest-8.3.4, pluggy-1.5.0
rootdir: /home/johans/School/windower
plugins: anyio-4.6.2.post1
collected 2 items

test_windower.py .F                                                                                                               [100%]

=============================================================== FAILURES ================================================================
_______________________________________________________________ test_demo _______________________________________________________________

    def test_demo():
>       assert False
E       assert False

test_windower.py:19: AssertionError
======================================================== short test summary info ========================================================
FAILED test_windower.py::test_demo - assert False
====================================================== 1 failed, 1 passed in 0.04s ======================================================
```

It says where it failed. You are encouraged to read the unit test, what it does and what its goal is, and then go on to fix the bug in the code.

An example success output:
```
└─[$] <git:(feature/logging*)> pytest
========================================================== test session starts ==========================================================
platform linux -- Python 3.12.8, pytest-8.3.4, pluggy-1.5.0
rootdir: /home/johans/School/windower
plugins: anyio-4.6.2.post1
collected 1 item

test_windower.py .                                                                                                                [100%]

=========================================================== 1 passed in 0.01s ==========================================================
```
