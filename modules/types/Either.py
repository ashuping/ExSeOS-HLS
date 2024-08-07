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
C = TypeVar('C')

class Either[A, B](ABC):
    '''
        Represents a value that could be "either" of two possible types.

        The 'Left' type usually represents an error condition, and the 'Right'
        type indicates success.
    '''

    @property
    @abstractmethod
    def is_right(self) -> bool:
        ''' Return True if this Either is a Right; otherwise, return False.
        '''
        ...

    @property
    @abstractmethod
    def val(self) -> B: 
        ''' Return the inner value of a Right.

            @warning Raises a TypeError if called on a Left.
        '''
        ...

    @property
    @abstractmethod
    def lval(self) -> B:
        ''' Return the inner value of a Left.

            @warning Raises a TypeError if called on a Right.
        '''
        ...

    @abstractmethod
    def map(self, f: Callable[[B], C]) -> 'Either[A, C]':
        ''' If this Either is a Right, call `f` on its rval and return a Right()
            of the result.
        
            If it is a Left, do not call `f` and just return a Left() of the
            lval.
        '''
        ...

    @abstractmethod
    def flat_map(self, f: Callable[[B], 'Either[A, C]']) -> 'Either[A, C]':
        ''' Similar to Map, except that `f` should convert `B`'s directly into
            an `Either`.
        '''
        ...


class Left[A](Either):
    def __init__(self, val: A):
        self.__lval = val

    @property
    def is_right(self) -> bool:
        return False
    
    @property
    def val(self) -> B:
        raise TypeError("Can't return rval from Left()!")
    
    @property
    def lval(self) -> A:
        return self.__lval
    
    def map(self, f: Callable[[B], C]) -> Either[A, C]:
        return self
    
    def flat_map(self, f: Callable[[B], Either[A, C]]) -> Either[A, C]:
        return self
    
    def __str__(self) -> str:
        return f'Left[{self.__lval.__class__.__name__}]({self.__lval})'
    

class Right[B](Either):
    def __init__(self, val: B):
        self.__rval = val

    @property
    def is_right(self) -> bool:
        return True
    
    @property
    def val(self) -> B:
        raise self.__rval
    
    @property
    def lval(self) -> A:
        raise TypeError("Can't return lval from Right()!")
    
    def map(self, f: Callable[[B], C]) -> Either[A, C]:
        return Right(f(self.__rval))
    
    def flat_map(self, f: Callable[[B], Either[A, C]]) -> Either[A, C]:
        return f(self.__rval)
    
    def __str__(self) -> str:
        return f'Right[{self.__rval.__class__.__name__}]({self.__rval})'