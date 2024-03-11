# this is a dummy file that defines a test function to check the docs work etc 

def testfunc(x: int, y: float) -> str:
    """
    testfunc A test functin that makes a string out of its arguments with a '_' inbetween.

    Args:
        x (int): first arg
        y (float): second arg

    Returns:
        str: "$x"+":_"+"$y"
    """
    return str(x) + str(y)