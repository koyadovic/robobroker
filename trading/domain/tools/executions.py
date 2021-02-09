import traceback


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
                    else:
                        traceback.print_exc()
                        print(f'WARN: Exception: {str(e)}')
        return wrapper
    return decorator
