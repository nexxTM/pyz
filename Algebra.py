# -*- coding: utf-8 -*-
from functools import reduce, singledispatch, partial
from operator import add


class Monoid(object):

    def __init__(self, mempty, mappend):
        self.mempty = mempty
        self.mappend = mappend

    def mconcat(self, ms):
        return reduce(self.mappend, ms, self.mempty)

listMonoid = Monoid([], lambda a, b: a + b)
numPlusMonoid = Monoid(0, lambda a, b: a + b)
numMulMonoid = Monoid(1, lambda a, b: a * b)
boolAndMonoid = Monoid(True, lambda a, b: a and b)
boolOrMonoid = Monoid(False, lambda a, b: a or b)

xs = [1, 2, 3]
ys = [3, 54]
xss = [[1, 3], [3, 56], [325]]
bs = [False, True]

print(listMonoid.mappend(xs, ys))
print(listMonoid.mconcat(xss))

my_sum = numPlusMonoid.mconcat
my_all = boolAndMonoid.mconcat
my_any = boolOrMonoid.mconcat

print(my_any(bs))


@singledispatch
def mappend(a, b):
    pass


@singledispatch
def mempty(a):
    pass


def mconcat(ms):
    e = mempty.registry[type(ms[0])]()
    append = mappend.registry[type(ms[0])]
    return reduce(append, ms, e)

#list (think of it as type class)
mempty.register(list, lambda: listMonoid.mempty)
mappend.register(list, listMonoid.mappend)

#int +
mempty.register(int, lambda: numPlusMonoid.mempty)
mappend.register(int, numPlusMonoid.mappend)

#bool and
mempty.register(bool, lambda: boolAndMonoid.mempty)
mappend.register(bool, boolAndMonoid.mappend)


print(mappend(xs, ys))
print(mconcat(xss))

print(mconcat(bs))
print(mconcat([True, True]))

#print(mconcat([]))


class HomogeneousList(list):

    def __init__(self, typ, lst=[]):
        super(HomogeneousList, self).__init__(lst)
        self.typ = typ

    # Some type checking... (asserts)


def mconcat2(ms):
    e = mempty.registry[ms.typ]()
    append = mappend.registry[ms.typ]
    return reduce(append, ms, e)


hxs = HomogeneousList(int, xs)

hys = HomogeneousList(bool)

print(mconcat2(hxs))
print(mconcat2(hys))


#think of it as a type synonyme
class Product(int):

    def __new__(cls, v):
        return super(Product, cls).__new__(cls, v)


#int *
mempty.register(Product, lambda: numMulMonoid.mempty)
mappend.register(Product, numMulMonoid.mappend)

ps = [Product(3), Product(4), Product(6)]
#ps = list(map(Product, [3, 4, 6]))
print(mconcat(ps))


class Functor(object):

    def __init__(self, fmap):
        self.fmap = fmap

listFunctor = Functor(lambda f, xs: [f(x) for x in xs])


#maybe we look at another 3.4 feature: enums
class Maybe(object):

    def __init__(self):
        raise Exception("Graar! I'm sorry. Have some fun " +
            "http://i.imgur.com/EwTCf.jpg")


class Nothing(Maybe):

    def __init__(self):
        pass

    def __str__(self):
        return "Nothing"

    def map(self, f):
        return self


class Just(Maybe):

    def __init__(self, value):
        self.value = value

    def __str__(self):
        return "Just " + self.value.__str__()

    def map(self, f):
        return Just(f(self.value))

#def maybe_fmap(f, may):
#    if isinstance(may, Just):
#        return Just(f(may.value))
#    else:
#        return may

maybeFunctor = Functor(lambda f, may: may.map(f))


@singledispatch
def fmap(functor, f):  # dispatches only on first parameter
    pass


def flip(f):
    return lambda x, y: f(y, x)

fmap.register(list, flip(listFunctor.fmap))
fmap.register(Maybe, flip(maybeFunctor.fmap))

print(fmap(Just(5), partial(add, 2)))
print(fmap(Nothing(), partial(add, 2)))