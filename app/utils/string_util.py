import string, random
from app.utils.result_util import Result, Error, Ok

class StringUtil:
    
    def generate_random(self, min_length: int, max_length: int) -> Result[str, Exception]:
        try:
            random_length = random.randint(min_length, max_length)
            character_pool = string.ascii_lowercase + string.digits
            value = ''.join(random.choice(character_pool) for _ in range(random_length))
            return Ok(value)
        except Exception as e:
            return Error(e)
