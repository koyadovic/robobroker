def execution_with_attempts(attempts=3):
    def decorator(func):
        def wrapper(*args, **kwargs):
            n = 0
            while True:
                try:
                    n += 1
                    return func(*args, **kwargs)
                except Exception as e:
                    if n >= attempts:
                        raise e
        return wrapper
    return decorator
