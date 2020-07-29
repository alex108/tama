import asyncio as aio
import json
from collections import OrderedDict

__all__ = ["show_tasks_every_10s"]


def show_coroutine(c):
    data = OrderedDict([
        ('txt', str(c)),
        ('type', str(type(c))),
        ('done', c.done()),
        ('cancelled', False),
        ('stack', None),
        ('exception', None),
    ])
    if not c.done():
        data['stack'] = [format_frame(x) for x in c.get_stack()]
    else:
        if c.cancelled():
            data['cancelled'] = True
        else:
            data['exception'] = str(c.exception())
    return data


def format_frame(f):
    keys = ['f_code', 'f_lineno']
    return OrderedDict([(k, str(getattr(f, k))) for k in keys])


async def show_tasks_every_10s():
    with open("aiolog", "w") as f:
        while True:
            await aio.sleep(10)
            j = json.dumps([
                show_coroutine(coro) for coro in aio.all_tasks()
            ], indent=4)
            print(j)
            f.write(j + "\n\n")