import argparse
import json
import logging
import threading
import time
import traceback

import websocket
from wrenchbox.logging import setup_log

DEFAULTS = {'max_connection':3}

class Tracker:
    def __init__(self):
        self.spawning = []
        self.peers = []

    def run(self,seed: str, sleep: int =30):
        self.spawn(seed)
        while(True):
            time.sleep(sleep)
            self.query()
            self.announce()
            if not len(self.peers):
                logging.critical('All peers are gone, updater will terminate.')
                break

    #运行启动
    def spawn(self,url):
        #如果url不在列表里则加入
        if url not in self.spawning:
            if len(self.peers)<DEFAULTS['max_connection']:
                self.spawning.append(url)
                logging.info('Spawning new peer: %s',url)

                self.spawning.remove(url)
            else:
                logging.debug('MAX # of connection is reached.')
            for i in self.spawning:
                logging.info('Spawning : %s', i)
            #利用websocket.WebSocketApp模拟客户端
            ws = websocket.WebSocketApp(
                url=url,
                on_open=self.on_open,
                on_message = self.on_message,
                on_close = self.on_close
            )
            '''
            参数说明：
            （3）on_open：在建立Websocket握手时调用的可调用对象，这个方法只有一个参数，就是该类本身。
            （4）on_message：这个对象在接收到服务器返回的消息时调用。有两个参数，一个是该类本身，一个是我们从服务器获取的字符串（utf-8格式）。
            （5）on_error：这个对象在遇到错误时调用，有两个参数，第一个是该类本身，第二个是异常对象。   
            （6）on_close：在遇到连接关闭的情况时调用，参数只有一个，就是该类本身。
            （7）on_cont_message：这个对象在接收到连续帧数据时被调用，有三个参数，分别是：类本身，从服务器接受的字符串（utf-8），连续标志。
            '''
            # 开启线程启动客户端
            peer = threading.Thread(target = ws.run_forever)
            peer.daemon = True
            peer.start()
            #self.spawning.remove(url)

    #握手时调用
    def on_open(self,ws):
        logging.info("New peer connected: %s",ws.url)
        self.peers.append(ws)

    #遇到连接关闭的情况时调用
    def on_close(self,ws):
        logging.info("Peer disconnected: %s",ws.url)
        if ws in self.peers:
            self.peers.remove(ws)

    #接收到服务器返回的消息时调用
    def on_message(self,ws,message):
        try:
            message = json.loads(message)
        except json.JSONDecodeError:
            pass
        if 'response' in message:
            if  'peers' in message['response']:
                for peer in message['response']['peers']:
                    if peer not in [i.url for i in self.peers]:
                        self.spawn(peer)
            if 'pool' in message['response']:
                logging.debug('Receiver pool update from:%s ',ws.url)
                for peer in self.peers:
                    if peer != ws:
                        logging.info('Announced pool updates to: %s',peer.url)
                    peer.send(json.dumps({
                        'op':'merge',
                        'args':{
                            'pool': message['response']['pool']
                        }
                    }))
            if 'blocks' in message['response']:
                logging.debug('Receiver blocks update from:%s ', ws.url)
                for peer in self.peers:
                    if peer != ws:
                        logging.info('Announced blocks updates to: %s', peer.url)
                    peer.send(json.dumps({
                        'op': 'merge',
                        'args': {
                            'blocks': message['response']['blocks']
                        }
                    }))
    #询问认识谁
    def query(self):
        for peer in self.peers:
            try:
                peer.send(json.dumps({'op':'peers'}))
                peer.send(json.dumps({'op': 'pool'}))
                peer.send(json.dumps({'op': 'blocks'}))
            except:
                logging.error('Connot request peers from: %s', peer.url)
                traceback.print_exc()

    #广播
    def announce(self):
        for peer in self.peers:
            try:
                peer.send(json.dumps({
                    'op':'register',
                    'args':{
                        'addr':[i.url for i in self.peers]
                    }
                }))
            except:
                pass

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--debug', action='store_true',
                        default=False, help='show debug information'
                        )
    parser.add_argument('-t','--sleep',
                        type=int,default = 30,help = 'refresh rate in seconds, defauly:30'
                        )
    parser.add_argument('seed',
                        type=str, default=30,help='seed announce server, e.g.: ws://localhost:9000/ws')
    args, _ = parser.parse_known_args()
    setup_log(level=logging.DEBUG if args.debug else logging.INFO)
    Tracker().run(args.seed,args.sleep)
