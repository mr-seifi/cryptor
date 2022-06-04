import os

if os.environ.get('ENV') == 'pro':
    from .pro import *
else:
    from .local import *
