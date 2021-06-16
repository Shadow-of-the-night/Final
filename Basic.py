import hashlib
from wrenchbox.object import Dict2StrSafe

#作于散列函数的基类
class Base(Dict2StrSafe):
    #定义散列函数
    def hash(self):
        return hashlib.sha1(str(self.__dict__).encode()).hexdigest()