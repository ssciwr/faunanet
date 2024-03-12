import pytest
import time  # simulate runtime


class Dummy: 
    def __init__(self): 
        self.x = 3  
    
    def test_dummy(self): 
        time.sleep(2)
        return self.x + 4


@pytest.fixture 
def dummyfixture(): 
    return Dummy()


def test_dummy(dummyfixture): 
    y = dummyfixture.test_dummy() 
    assert y == 7