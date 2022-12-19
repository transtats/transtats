# this place is to process stuffs

import hashlib


HASH_ALGO = {
    'md5': hashlib.md5,
    'sha1': hashlib.sha1,
    'sha256': hashlib.sha256,
    'sha3_256': hashlib.sha3_256,
    'shake_256': hashlib.shake_128,
}


def get_hash(string_value, algorithm):
    """Create hash for the given string and algorithm"""
    if not isinstance(string_value, str) and not algorithm:
        return string_value
    hash_object = HASH_ALGO.get(algorithm)(string_value.encode())
    if not hash_object:
        return string_value
    hex_dig = hash_object.hexdigest()
    return hex_dig[::-1][:10]
