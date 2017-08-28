"""
This class implements a token bucket, allowing for requests to be made without being ratelimited.
"""

import time


class RateBucket:
    def __init__(self, requests_per_15_minutes, requests_per_second):
        self.requests_per_15_minutes = requests_per_15_minutes
        self.requests_per_second = requests_per_second

        self.__allowed_requests_per_15_minutes = requests_per_15_minutes
        self.__allowed_requests_per_second = requests_per_second

        self.__last_check_time = time.time()
        self.__elapsed_time = 0

    def can_request(self):
        self.__add_requests()

        if self.__allowed_requests_per_15_minutes >= 1 and self.__allowed_requests_per_second >= 1:
            return True
        else:
            return False

    def get_next_request(self):
        if self.can_request():
            return 0
        else:
            #  We return the maximum duration to be sure we don't hit the ratelimit
            if self.__allowed_requests_per_15_minutes < 1:
                return 5
            elif self.__allowed_requests_per_second < 1:
                return 1
        raise Exception("Request should be allowed.")  # This should never be reached

    def do_request(self):
        self.__allowed_requests_per_15_minutes -= 1
        self.__allowed_requests_per_second -= 1

    def __add_requests(self):
        current_time = time.time()
        self.__elapsed_time += current_time - self.__last_check_time
        self.__last_check_time = current_time

        if self.__elapsed_time > 1:
            elapsed_seconds = int(self.__elapsed_time)
            self.__elapsed_time -= elapsed_seconds

            #  Add up new requests that we can make since the last time we've checked
            self.__allowed_requests_per_15_minutes += (1 / 900) * elapsed_seconds * self.requests_per_15_minutes
            self.__allowed_requests_per_second += elapsed_seconds * self.requests_per_second

            # We can't have more than the max number of requests
            if self.__allowed_requests_per_15_minutes > self.requests_per_15_minutes:
                self.__allowed_requests_per_15_minutes = self.requests_per_15_minutes
            if self.__allowed_requests_per_second > self.requests_per_second:
                self.__allowed_requests_per_second = self.requests_per_second
