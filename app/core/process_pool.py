import asyncio
from concurrent.futures import ProcessPoolExecutor
from typing import Any, Callable

MAX_WORKERS = 2
_executor = ProcessPoolExecutor(max_workers=MAX_WORKERS)


async def run_in_process(func: Callable[..., Any], *args: Any) -> Any:
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(_executor, func, *args)
