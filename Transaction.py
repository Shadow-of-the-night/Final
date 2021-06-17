from datetime import datetime
from Basic import Base
from uuid import UUID, uuid4

from File import FileHander
from blockchain import Blockchain, Block

super_id = "00000000-0000-0000-0000-000000000000"
#交易记录类
class Transaction(Base):
    def __init__(self,
                 sender: str, receiver: str,
                 amount: int,t: float = None,
                 prev_hash: str = None, transaction_id: str = None,
                 content:str = None):
        assert UUID(sender,version=4)
        assert UUID(receiver, version=4)
        self.id = transaction_id if transaction_id is not None else str(uuid4())
        self.sender = sender
        self.receiver = receiver
        self.amount = amount
        self.content = content if content is not None else "nothing"
        self.t = t if t is not None else datetime.now().timestamp()
        self.prev_hash = prev_hash

    def __eq__(self, other):
        return\
            self.id == other.id and\
            self.sender == other.sender and\
            self.receiver == other.receiver and\
            self.amount == other.amount and\
            self.content == other.content

    def __hash__(self):
        return hash((self.id,self.sender,self.receiver,self.amount))

#分布式账本类
class Ledger(Blockchain):
    def count_balance(self,user):
        balance = 0
        for i in range(len(self.blocks)):
            for j in range(len(self.blocks[i].items)):
                if(user == self.blocks[i].items[j].receiver):
                    balance = balance + self.blocks[i].items[j].amount
                if (user == self.blocks[i].items[j].sender):
                    balance = balance - self.blocks[i].items[j].amount
        return balance

    def add(self, block):
        block.prev_hash = self.blocks[-1].hash() if len(self.blocks) else None
        #校验每一笔交易中的转账金额不能大于账户余额(除非你是超级用户)
        for i in range(len(block.items)):
                print(block.items[i].sender+"现有"+str(self.count_balance(block.items[i].sender)))
                print("现在要转金额:"+str(block.items[i].amount))
                assert block.items[i].sender==super_id \
                            or block.items[i].amount <= self.count_balance(block.items[i].sender)
        self.blocks.append(block)

    #根据图片转好的content进行查询 返回查询出来的创作者 如果返回0则表示图片尚未上传
    def Search_Creator(self,content):
        creator = '0'
        for i in range(len(self.blocks)):
            for j in range(len(self.blocks[i].items)):
                if (content == self.blocks[i].items[j].content):
                        creator = self.blocks[i].items[j].sender
                        return creator


    # 根据图片转好的content进行查询 返回查询出来的拥有者,以及现在的价值,位于区块链的位置 如果返回0则表示图片尚未上传
    def Search_Owner(self,content):
        max_amout = 0
        owner = 0
        a = 0
        b = 0
        for i in range(len(self.blocks)):
            for j in range(len(self.blocks[i].items)):
                if (content == self.blocks[i].items[j].content and self.blocks[i].items[j].amount>max_amout):
                        max_amout = self.blocks[i].items[j].amount
                        owner = self.blocks[i].items[j].sender
                        a = i
                        b = j
        return owner,max_amout,a,b

    # 根据图片转好的content进行查询 返回查询出来的所有可转载者
    def Search_Users(self,content):
        owner,value,a,b = self.Search_Owner(content)
        Users = []
        #避免出现购买拥有权之前有人转账但也被判定为拥有转载权,所以查询直接查询购买以后添加进来的区块链信息
        for j in range(b,len(self.blocks[a].items)):
            if (content == self.blocks[a].items[j].content and self.blocks[a].items[j].receiver == owner \
                    and self.blocks[a].items[j].amount<=value):
                Users.append(self.blocks[a].items[j].sender)
        for i in range(a+1,len(self.blocks)):
            for j in range(len(self.blocks[i].items)):
                if (content == self.blocks[i].items[j].content and self.blocks[i].items[j].receiver == owner \
                        and self.blocks[i].items[j].amount<=value):
                    Users.append(self.blocks[i].items[j].sender)
        return Users

    # 查询用户是否侵权，没有侵权返回True，侵权返回False
    def Search_lawful(self,content,id):
        Users = self.Search_Users(content)
        if id in Users:
            return True
        else:
            return False

#测试功能
if __name__ == '__main__':
    #创建正常用户
    users = []
    for i in range(5):
        user = str(uuid4())
        users.append(user)

    ledger = Ledger()
    block = Block()
    for i in range(5):
        transaction = Transaction(sender=super_id,receiver=users[i],amount=200,content="give money")
        block.add(transaction)
    ledger.add((block))

    #创作者
    creator = users[0]
    #将画转为content
    with open("cover.png", 'rb') as f:
        image = f.read()
    fileHander = FileHander(image)
    content = str(fileHander.base64())

    #转账给拍卖行
    block = Block()
    transaction = Transaction(sender=creator,receiver=super_id,amount=10,content=content)
    block.add(transaction)
    ledger.add((block))

    print("创作者"+users[0] + "成功上传图片")

    block = Block()
    transaction = Transaction(sender=users[1],receiver=creator,amount=60,content=content)
    block.add(transaction)
    ledger.add((block))
    print(users[1] + "向" + creator + "购买了图片")

    print("现在查询图片拥有者：")
    print(ledger.Search_Owner(content))

    print("现在查询图片创作者：")
    print(ledger.Search_Creator(content))

    #现在有user[2]打算了去购买这幅图片的转载权
    #但是它得先知道这个图片的content，和现在的拥有者是谁
    owner,value,i,j = ledger.Search_Owner(content)
    block = Block()
    #转账小于价值的钱给拥有者
    transaction = Transaction(sender=users[2],receiver=owner,amount=5,content=content)
    block.add(transaction)
    ledger.add(block)

    print(users[2]+"向"+owner+"购买了图片的转载权")

    #现在有user[3]打算了去购买这幅图片的转载权
    transaction = Transaction(sender=users[3],receiver=owner,amount=5,content=content)
    block = Block()
    block.add(transaction)
    ledger.add(block)

    print(users[3] + "向" + owner + "购买了图片的转载权")

    #查询哪些用户有图片转载权
    a = ledger.Search_Users(content)
    print(a)

    #验证用户user[4]有没有转载权
    if(ledger.Search_lawful(content,users[4])):
        print(users[4]+"有转载权")
    else:
        print(users[4] + "没有有转载权")

    #此时用户user[4]再购买拥有权
    block = Block()
    transaction = Transaction(sender=users[4],receiver=owner,amount=70,content=content)
    block.add(transaction)
    ledger.add((block))
    print(users[1] + "向" + owner + "购买了图片")

    print("现在查询图片拥有者：")
    print(ledger.Search_Owner(content))

    #查询哪些用户有图片转载权
    a = ledger.Search_Users(content)
    print(a)

    #此时打印转载权者为 空 因为user[4]重新购买了 之前向拥有者购买的转载权就失效 需要重新购买











