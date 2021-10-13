def print_progress(func):
    """ print the progress of the func running"""

    def wrapper(*args, **kwargs):
        print("Running {} ({})...".format(func.__name__, args and args[0] or ""))
        result = func(*args, **kwargs)
        print("Running {} done".format(func.__name__))
        return result

    return wrapper
