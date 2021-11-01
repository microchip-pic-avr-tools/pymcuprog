This folder contains tests based on Python unittest. Tests are run from the root of the repo (pymcuprog not pymcuprog/pymcuprog or pymcuprog/pymcuprog/tests)

To run all tests:
~~~~
\pymcuprog>python -m unittest discover
~~~~

To run a specific test module:
~~~~
\pymcuprog>python -m unittest pymcuprog.tests.test_pymcuprogcli
~~~~

To run a specific test:
~~~~
\pymcuprog>python -m unittest pymcuprog.tests.test_pymcuprogcli.TestPymcuprogCLI.test_ping_nedbg_pic16f18446
~~~~