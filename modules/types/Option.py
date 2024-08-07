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
        ...

    @property
    @abstractmethod
    def val(self) -> A:
        ''' Return the inner value of a `Some[A]`.

            @warning Raises a TypeError if called on `Nothing`.
        '''
        ...

    @abstractmethod
    def map(self, f: Callable[[A], B]) -> 'Option[B]':
        ''' If this is `Some[A]`, call `f` on its value and return a `Some[B]`
            of the result.

            If it is `Nothing`, do not call `f` and just return `Nothing`.
        '''
        ...

    @abstractmethod
    def flat_map(self, f: Callable[[A], 'Option[B]']) -> 'Option[B]':
        ''' Similar to Map, except that `f` should convert `A`'s directly into
            `Option[B]`'s.
        
        '''
        ...

class Nothing(Option):
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

class Some[A](Option):
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