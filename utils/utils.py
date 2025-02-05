import random
import string


def generate_random_string(length):
    return ''.join(random.choices(string.ascii_letters, k=length))


def generate_random_isbn():
    return ''.join(random.choices(string.digits, k=13))
