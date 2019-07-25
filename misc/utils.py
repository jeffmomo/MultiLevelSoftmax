from contextlib import contextmanager 
from datetime import datetime
import logging


@contextmanager
def time_it(stat_name: str):
    before_fn = datetime.now().timestamp()
    yield
    print('time_it', stat_name, str(datetime.now().timestamp() - before_fn))