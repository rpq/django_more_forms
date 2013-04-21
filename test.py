class Test(object):
    def __init__(self):
        self.x = []

    def testtest(self):
        self.x = ['a', 'b', {}]
        return self.x

    @classmethod
    def classtesttest(cls):
        return ['a', 'b', {}]

a = Test()
b = Test()
a.testtest()
b.testtest()
print a.testtest() is b.testtest()
x = ['a', 'b', 'c']
y = ['a', 'b', 'c']
print x is x
print x is y
print id(x)
print id(y)
print Test.classtesttest() is Test.classtesttest()
