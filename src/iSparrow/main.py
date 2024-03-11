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


class Dummy:
    """
    This is a dummy class.

    This dummy class is only used for demonstration purposes
    """

    def member(self):
        """
        member This is a dummy member that does nothing

        It does really nothing useful other than output 42

        Returns:
            42 (int)
        """
        return 42
