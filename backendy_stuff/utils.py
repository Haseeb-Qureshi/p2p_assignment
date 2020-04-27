import functools

def only_if_awake(state):
    '''
    Decorator that ensures a function only runs when the node is awake.
    If not, the node drops the request.
    '''
    def callable(f):
    	@functools.wraps(f)
    	def wrapped(*args, **kwargs):
    		if state["awake"]:
    			return f(*args, **kwargs)
    		else:
    			return "Asleep"
    	return wrapped
    return callable
