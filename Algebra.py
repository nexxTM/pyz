# -*- coding: utf-8 -*-
from abc import ABCMeta, abstractmethod
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
def mempty(type_):
# Don't use this. Use monoid.mempty
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

    __metaclass__ = ABCMeta

    @abstractmethod
    def isNothing(self):
        pass

    @abstractmethod
    def map(self, f):
        pass

    @abstractmethod
    def ap(self, a):
        pass


class Nothing(Maybe):

    def __init__(self):
        pass

    def __str__(self):
        return "Nothing"

    def isNothing(self):
        return True

    def map(self, f):
        return self

    def ap(self, a):
        return self


class Just(Maybe):

    def __init__(self, value):
        self.value = value

    def __str__(self):
        return "Just " + self.value.__str__()

    def isNothing(self):
        return False

    def map(self, f):
        return Just(f(self.value))

    def ap(self, a):
        if a.isNothing():
            return Nothing()
        else:
            v = partial(self.value, a.value)
            try:
                v = v()
            # this seems to be a very bad idea
            except TypeError:
                pass
            return Just(v)


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


def const(a):
    return lambda b: a


def id_(a):
    return a


def compose(f, g):
    return lambda a: f(g(a))


class Applicative(Functor):

    def __init__(self, fmap, ap, pure):
        super(Applicative, self).__init__(fmap)
        self.ap = ap
        self.pure = pure

    def right_ap(self, a, b):
        """
        *>  f a -> f b -> f b
        """
        return self.ap(self.ap(self.pure(const(id_)), a), b)

    def left_ap(self, a, b):
        """
        <*  f a -> f b -> f a
        """
        return self.ap(self.ap(self.pure(const), a), b)

maybeApplicative = Applicative(maybeFunctor.fmap, lambda f, a: f.ap(a), Just)


@singledispatch
def ap(f, a):
    pass


@singledispatch
def pure(type_, x):
# this is worse than mempty.
    pass


def right_ap(a, b):
    pure_ = pure.registry[type(a)]
    return ap(ap(pure_(const(id_)), a), b)


def left_ap(a, b):
    pure_ = pure.registry[type(a)]
    return ap(ap(pure_(const), a), b)

ap.register(Maybe, maybeApplicative.ap)
pure.register(Maybe, maybeApplicative.pure)
pure.register(Just, maybeApplicative.pure)
pure.register(Nothing, maybeApplicative.pure)

f = Just(lambda x: x + 2)
g = Just(lambda x, y, z: x + y * z)

print(ap(f, Just(3)))
print(ap(ap(ap(g, Just(3)), Just(4)), Just(5)))
print(ap(ap(g, Just(3)), Just(4)))
print(right_ap(Just(3), Just(5)))
print(left_ap(Just(3), Just(5)))
