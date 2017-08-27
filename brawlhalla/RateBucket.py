"""
This class implements a token bucket, allowing for requests to be made without being ratelimited.
"""

import time


class RateBucket:
    def __init__(self, requests_per_15_minutes, requests_per_second):
        self.requests_per_15_minutes = requests_per_15_minutes
        self.requests_per_second = requests_per_second
