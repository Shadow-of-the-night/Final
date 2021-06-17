import argparse
import json
import logging
import pickle
import time
import traceback

from redis import Redis
from wrenchbox.logging import setup_log

from blockchain import Block

class Builder:
    def __init__(self,url):
        self.db=Redis(url)

    def run(self,k_size,cool_down):
        while True:
            pool = pickle.loads(self.db.get('pool'))
            if len(pool) >= k_size:
                self.db.set('pool',pickle.dumps(set([])))
                logging.info('Pool is cleared.')
                logging.info('Packing %d transactions...',len(pool))
                ledger = pickle.loads(self.db.get('ledger'))
                block = Block()
                for transaction in pool:
                    if transaction.sender == "00000000-0000-0000-0000-000000000000" \
                            or ledger.count_balance(transaction.sender)>=transaction.amount:
                        block.add(transaction)
                    else:
                        logging.warning('Dropped transaction due to not enough balance:%s',transaction)
                logging.info('Block is created with %d records.',len(block.items))
                if len(block.items):
                    try:
                        block.validate()
                    except AssertionError:
                        logging.error('Block is invalid and dropped.')
                        if args.debug:
                            traceback.print_exc()
                    else:
                        ledger.add(block)
                        self.db.set('ledger',pickle.dumps(ledger))
                        logging.info('Block is added to the blockchain.')
            else:
                logging.debug('Currently %d record,require :%d',len(pool),k_size)
            time.sleep(cool_down)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--debug',
                        action='store_true',default=False,
                        help='show debug information'
                        )

    parser.add_argument(
        '-r','--redis',
        type=str,default='localhost',
        help='redis database file, default:redis.db'
    )
    parser.add_argument(
        '-k','--size',
        type=int,default=3,
        help='# of minimum packed transations, default: 3'
    )
    parser.add_argument(
        '-t','--sleep',
        type=int,default=3,
        help='refresh rate in seconds, default:3'
    )
    args, _ = parser.parse_known_args()
    setup_log(level=logging.DEBUG if args.debug else logging.INFO)
    print(args)
    Builder(args.redis).run(args.size,args.sleep)