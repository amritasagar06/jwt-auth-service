from slowapi import Limiter
from slowapi.util import get_remote_address

# Define the limiter in this neutral "shared" file
limiter = Limiter(key_func=get_remote_address)