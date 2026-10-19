import asyncio

from database.model import cache, connection
from models import ExecuteResult
from network.aof import append_to_aof
from network.execute.commands import execute
from network.resp2 import error_response

async def write(write_queue, aof_type: str, batch_size: int = 2000, batch_delay= 0.002):
    while True:
        batch = await collect_batch(write_queue, batch_size, batch_delay)

        try:
            responses = process_batch(batch, aof_type)
        except Exception:
            error_result = ExecuteResult(error_response("Batch write failed"))
            for request in batch:
                if not request.future.done():
                    request.future.set_result(error_result)

        else:
            for request, resp in zip(batch, responses):
                if not request.future.done():
                    request.future.set_result(resp)
        finally:
            for _ in batch:
                write_queue.task_done()

async def collect_batch(write_queue, batch_size, batch_delay):
    first = await write_queue.get()
    batch = [first]

    loop = asyncio.get_running_loop()
    deadline = loop.time() + batch_delay

    while len(batch) < batch_size:
        remaining = deadline - loop.time()
        if remaining <= 0: break

        try:
            request = await asyncio.wait_for(
                write_queue.get(),
                timeout=remaining
            )
        except asyncio.TimeoutError:
            break

        batch.append(request)
    return batch

def process_batch(batch, aof_type):
    responses = []

    connection.execute("BEGIN")
    try:
        for request in batch:
            resp = execute(request.command, cache_size=request.cache_size, auto_commit=False)

            if resp.response == (b"-ERR Database connection failed\r\n"):
                raise ConnectionError("Database connection failed")

            responses.append(resp)

            if aof_type != "no":
                entries = [
                    (request.command, resp)
                    for request, resp in zip(batch, responses)
                ]
                append_to_aof(entries,sync=aof_type=="always")
                
        connection.commit()
        return responses
    except Exception:
        connection.rollback()
        cache.clear()
        raise