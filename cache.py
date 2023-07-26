import functools


class VKCache:
    def __init__(self, func):
        self.func = func
        self.cache = {}

    def __call__(self, *args):
        if args in self.cache:
            return self.cache[args]
        result = self.func(*args)
        self.cache[args] = result
        return result


# Кэширование результатов запросов VK API
def cache_vk_api(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        cache_key = (func.__name__, args, frozenset(kwargs.items()))
        if cache_key in cache:
            return cache[cache_key]
        result = func(*args, **kwargs)
        cache[cache_key] = result
        return result

    cache = {}
    return wrapper

# Декоратор для кэширования результатов запросов VK API
def cache_vk_api_decorator(func):
    cache = {}  # Move the cache dictionary outside the wrapper function

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        cache_key = (func.__name__, args, frozenset(kwargs.items()))
        if cache_key in cache:
            return cache[cache_key]
        result = func(*args, **kwargs)
        cache[cache_key] = result
        return result

    return wrapper