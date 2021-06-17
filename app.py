import argparse
import json
import logging
import pickle
import time
import datetime

from Transaction import Ledger,Transaction
from redis import Redis
from tornado import websocket,web,ioloop
from wrenchbox.logging import setup_log

from blockchain import Block

clients = []
db = None

class IndexHandler(web.RequestHandler):
    def get(self):
        self.render("index.html")

class SocketHandler(websocket.WebSocketHandler):
    def check_origin(self,origin):
        return True

    def open(self):
        logging.info('Client connected: %s',self.request.remote_ip)
        if self not in clients:
            clients.append(self)

    def on_close(self):
        if self in clients:
            clients.remove(self)

    def on_message(self,message):
        try:
            message = json.loads(message)
        except json.JSONDecodeError:
            logging.warning('Connot parse request message: %s',message)
            self.write_message(json.dumps({
                'status':500,
                'error' : 'Connot parse request message',
                'response':None
            }))
        else:
            if message is not None:
                if 'op' in message:
                    if message['op']=='register':
                        if 'args' in message and 'addr' in message['args']:
                            peers = pickle.loads(db.get('peers'))
                            if not isinstance(message['args']['addr'],list):
                                message['args']['addr'] = [str(message['args']['addr'])]
                            for addr in message['args']['addr']:
                                if addr.startswith('ws://') or addr.startswith('wss://'):
                                    peers.add(addr)
                            db.set('peers', pickle.dumps(peers))
                            self.write_message(json.dumps({
                                'status':202,
                                'error':'Accepter'
                            }))
                        else:
                            self.write_message(json.dumps({
                                'status':500,
                                'error':'Operation "register" requires the following "args":"addr"',
                                'response':None
                            }))
                    elif message['op'] == 'peers':
                        self.write_message(json.dumps({
                            'status':200,
                            'error':'OK',
                            'response':{'peer':list(pickle.loads(db.get('peers')))}
                        }))
                    elif message['op'] == 'time':
                        self.write_message(json.dumps({
                            'status': 200,
                            'error': 'OK',
                            'response': {'time': time.time(),
                                         "time_zore":"CST"}
                        }))

                    #新加
                    elif message['op'] == 'pool':
                        self.write_message(json.dumps({
                            'status': 200,
                            'error': 'OK',
                            'response': {
                                'pool': [json.loads(str(i)) for i in list(pickle.loads(db.get('pool')))]
                            }
                        }))



                    elif message['op'] == 'merge':
                        if 'args' in message and 'pool' in message['args']:
                            pool = pickle.loads(db.get('pool'))
                            ledger = pickle.loads(db.get('ledger'))
                            for i in message['args']['pool']:
                                pool.add(Transaction(
                                    sender=i['sender'],
                                    receiver=i['receiver'],
                                    amount=i['amount'],
                                    content=i['content']
                                ))
                            for i in pool.copy():
                                if ledger.find(i):
                                    pool.remove(i)
                            db.set('pool',pickle.dumps(pool))
                            self.write_message(json.dumps({
                                'status': 202,
                                'error':'Accepted'
                            }))
                        elif 'args' in message and 'blocks' in message['args']:
                            pool = pickle.loads(db.get('pool'))
                            ledger = pickle.loads(db.get('ledger'))
                            for i in message['args']['blocks']:
                                if not len(ledger.blocks) or i['prev_hash'] == ledger.blocks[-1].hash():
                                    block = Block(prev_hash=i['prev_hash'])
                                    for j in i['items']:
                                        transcation = Transaction(
                                            sender = j['sender'],
                                            receiver = j['receiver'],
                                            amount=j['amount'],
                                            t=j['t'],
                                            prev_hash=j['prev_hash'],
                                            transaction_id=j['id'],
                                            content=j['content']
                                        )
                                        if ledger.find(transcation):
                                            self.write_message(json.dumps({
                                                'status':500,
                                                'error':'Duplicate transation in blockchain:{}'.format(transcation)
                                            }))
                                            return
                                        if transcation in pool:
                                            pool.remove(transcation)
                                        block.add(transcation)
                                    ledger.add(block)
                            try:
                                ledger.validate()
                            except AssertionError:
                                self.write_message(json.dumps({
                                    'status':500,
                                    'error':'Malicious block is deleted.'
                                }))
                            else:
                                db.set('pool',pickle.dumps(pool))
                                db.set('ledger',pickle.dumps(ledger))
                                self.write_message(json.dumps({
                                    'status':202,
                                    'error':'Accepted'
                                }))

                        else:
                            self.write_message(json.dumps({
                                'status': 500,
                                'error': 'Operation "merge" require the follow "args":"pool"',
                                'response':None
                            }))

                    elif message['op'] == 'blocks':
                        blocks = json.loads(str(pickle.loads(db.get('ledger'))))['blocks']
                        if 'args' in message and 'start' in message['args']:
                            blocks = blocks[int(message['args']['start']):]
                        self.write_message(json.dumps({
                            'status':200,
                            'error':'OK',
                            'response':{
                                'blocks':blocks
                            }
                        }))

                    elif message['op'] == 'Check_user':
                        ledger = pickle.loads(db.get('ledger'))
                        content = message['args']['content']
                        user = message['args']['user']
                        response = user + "don't has the right to reprint this picture"
                        if(ledger.Search_lawful(content, user)):
                            response = user + "has the right to reprint this picture"
                        self.write_message(json.dumps({
                            'status':200,
                            'error':'OK',
                            'response':{
                                'result':response
                            }
                        }))

                    elif message['op'] == 'Check_owner':
                        ledger = pickle.loads(db.get('ledger'))
                        content = message['args']['content']
                        owner,max_amout,a,b = ledger.Search_Owner(content)
                        response = "The owner of this picture is" + owner
                        self.write_message(json.dumps({
                            'status':200,
                            'error':'OK',
                            'response':{
                                'result':response
                            }
                        }))

                    elif message['op'] == 'Check_creator':
                        ledger = pickle.loads(db.get('ledger'))
                        content = message['args']['content']
                        creator = ledger.Search_Creator(content)
                        if(creator!='0'):
                            response = "The creator of this picture is " + creator
                        else:
                            response = content+"hasn't uploads"
                        self.write_message(json.dumps({
                            'status':200,
                            'error':'OK',
                            'response':{
                                'result':response
                            }
                        }))

                    else:
                        self.write_message((json.dumps({
                            'status':404,
                            'error':'Operation"{} is not supported.'.format(message['op']),
                            'response':None
                        })))
            else:
                logging.warning('Message body is not suppoeted: %s', message)
                self.write_message(json.dumps({
                    'status':500,
                    'error':'Message body is not supported',
                    'response':None
                }))

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('--debug',action='store_true',
                        default=False, help='show debug information'
                        )
    parser.add_argument('-p', '--port',
                        type=int, default=9000,
                        help='listening port,default:{}'.format(9000)
                        )
    parser.add_argument('-r', '--redis', type=str,
                        default='localhost',
                        help='redis database file,default: localhost'
                        )
    parser.add_argument('-d', '--dbNum', type=int,
                        default= 0,
                        help='redis database Number,default: 0'
                        )
    args, _ = parser.parse_known_args()
    print(args.port)

    setup_log(level=logging.DEBUG if args.debug else logging.INFO)
    db = Redis(host=args.redis,db=args.dbNum)
    if b'peers' not in db.keys():
        db.set('peers',pickle.dumps(set([])))
    if b'pool' not in db.keys():
        db.set('pool',pickle.dumps(set([])))
    if b'ledger' not in db.keys():
        db.set('ledger',pickle.dumps(Ledger()))
    web.Application([
        (r'/', IndexHandler),
        (r'/ws', SocketHandler)
    ]).listen(args.port)
    logging.info('Tornade is listening on port: %d', args.port)
    ioloop.IOLoop.instance().start()
