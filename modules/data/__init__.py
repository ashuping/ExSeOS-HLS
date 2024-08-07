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

from abc import ABC, abstractmethod

class DataStore[T](ABC):
    '''
        A write-once data-store.
    '''
    @abstractmethod
    def __init__(self, label: str, prev: DataStore = None): ...
    
    @property
    @abstractmethod
    def label(self) -> str: ...

    @property
    @abstractmethod
    def data(self) -> T: ...

    @property
    @abstractmethod
    def prev(self) -> DataStore|None: ...
    
    def __iter__(self): 
        cur = self
        while(cur is not None):
            yield cur
            cur = cur.prev


    Nothing = NoneDataStore('Nothing')

class NoneDataStore(DataStore):
    def __init__(self, label: str, prev: DataStore = None):
        self.__label = label
        self.__prev = prev

    @property
    def label(self) -> str:
        return self.__label
    
    @property
    def data(self) -> None:
        return None
    
    @property
    def prev(self) -> DataStore|None:
        return self.__prev
    
