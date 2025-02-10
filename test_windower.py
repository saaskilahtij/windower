"""
File: test_windower.py
Authors: Johan Sääskilahti, Atte Rajavaara, Minna Repo, Topias Hämäläinen
Description: This file contains the windower unit tests
"""
import pytest
import windower

def test_handle_args():
    """Temporary test: Ensures handle_args() exits when no arguments are given.
    
    This test is incomplete and will be updated.
    """
    with pytest.raises(SystemExit):  #Expect the program to exit due to an error
        windower.handle_args()  #The function will raise an error
