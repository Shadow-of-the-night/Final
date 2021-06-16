from Basic import Base
import logging
#类:区块
class Block(Base):
    def __init__(self, prev_hash: str = None):
        self.items = []
        self.prev_hash = prev_hash

    def add(self, item):
        if item not in self.items:
            item.prev_hash = self.items[-1].hash() if len(self.items) else None
            self.items.append(item)
        else:
            logging.debug('Duplicate item will be dropped:%s',item)

    #判断是否正确，有没有被修改 也就是hash值是否相等
    def validate(self):
        for i in range(len(self.items)):
            #assert语句是一种插入调试断点到程序的一种便捷的方式。 只有后面条件表达式成立才会正常执行，否则抛出AssertionError
            assert i == 0 or self.items[i].prev_hash == self.items[i - 1].hash()

#类:区块链
class Blockchain(Base):
    def __init__(self):
        self.blocks = []

    def add(self, block):
        block.prev_hash = self.blocks[-1].hash() if len(self.blocks) else None
        self.blocks.append(block)

    def find(self,item):
        for block in self.blocks:
            if item in block.items:
                return block.items[block.items.index(item)]

    def validate(self):
        for i in range(len(self.blocks)):
            assert i == 0 or self.blocks[i].prev_hash == self.blocks[i - 1].hash()
            self.blocks[i].validate()




