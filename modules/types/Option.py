'''
    Chicory ML Workflow Manager
    Copyright (C) 2024  Alexis Maya-Isabelle Shuping

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>.
'''

from modules.types.ComparableError import ComparableError

from typing import TypeVar, Callable
from abc import ABC, abstractmethod

A = TypeVar('A')
B = TypeVar('B')

class Option[A](ABC):
    '''
        Represents a value that could be absent.

        It is either `Some[A]` or `Nothing`.
    '''

    @property
    @abstractmethod
    def has_val(self) -> bool:
        ''' Return True if this is `Some[A]`; otherwise, return False.
        '''
        ... # pragma: no cover

    @property
    @abstractmethod
    def val(self) -> A:
        ''' Return the inner value of a `Some[A]`.

            @warning Raises a TypeError if called on `Nothing`.
        '''
        ... # pragma: no cover

    @abstractmethod
    def map(self, f: Callable[[A], B]) -> 'Option[B]':
        ''' If this is `Some[A]`, call `f` on its value and return a `Some[B]`
            of the result.

            If it is `Nothing`, do not call `f` and just return `Nothing`.

            :param: f: A function that takes an `A` and converts it to a `B`
            :returns: `Some(f(a))` if this Option is `Some(a)`, else `Nothing()`
        '''
        ... # pragma: no cover

    @abstractmethod
    def flat_map(self, f: Callable[[A], 'Option[B]']) -> 'Option[B]':
        ''' Similar to Map, except that `f` should convert `A`'s directly into
            `Option[B]`'s.

            :param f: A function that takes an `A` and converts it to an
                `Option[B]`
            :returns: `f(a)` if this `Option` is `Some(a)`, else `Nothing()`        
        '''
        ... # pragma: no cover

    @staticmethod
    def make_from(obj: any) -> 'Option[A]':
        ''' Convenience method to ensure an object is an Option. If `obj` is
            already an Option, it is returned as-is. If `obj` is None, it is
            converted to `Nothing()`. Otherwise, it is converted to `Some(obj)`

            :param obj: The object to encapsulate
            :returns: `obj` if `obj` is an Option; otherwise, `Some(obj)` if obj
                is not None; otherwise, `Nothing()`.
        '''
        ... # pragma: no cover

    def __eq__(self, other):
        if not issubclass(type(other), Option):
            return False
        if self.has_val:
            if other.has_val:
                return ComparableError.encapsulate(self.val) == ComparableError.encapsulate(other.val)
            else:
                return False
        else:
            if other.has_val:
                return False
            else:
                return True

class Nothing(Option):
    ''' Represents an empty `Option`.'''
    @property
    def has_val(self) -> bool:
        return False
    
    @property
    def val(self) -> A:
        raise TypeError("Can't return val from Nothing!")
    
    def map(self, f: Callable[[A], B]) -> Option[B]:
        return self
    
    def flat_map(self, f: Callable[[A], Option[B]]) -> Option[B]:
        return self

    def __str__(self):
        return f'Nothing'

class Some[A](Option):
    ''' Represents an `Option` that contains a concrete value. '''
    def __init__(self, val: A):
        self.__val = val

    @property
    def has_val(self) -> bool:
        return True
    
    @property
    def val(self) -> A:
        return self.__val
    
    def map(self, f: Callable[[A], B]) -> Option[B]:
        return Some(f(self.__val))
    
    def flat_map(self, f: Callable[[A], Option[B]]) -> Option[B]:
        return f(self.__val)

    def __str__(self):
        return f'Some[{self.val.__class__.__name__}]({self.val})'
    

def _make_from(obj: any) -> Option[A]:
    # The inner function has to be defined after `Some` and `Nothing`, and then
    # injected into the Object class.
    if issubclass(type(obj), Option):
        return obj
    
    if obj is None:
        return Nothing()
    
    return Some(obj)

Option.make_from = _make_from