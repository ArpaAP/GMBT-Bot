from typing import Dict, Callable

class DataDB:
    def __init__(self):
        self.exp_table = {}
        self.reloader = None
        self.loader = None

    def load_exp_table(self, table: Dict[int, int]):
        self.exp_table = table

    def set_reloader(self, callback: Callable):
        self.reloader = callback

    def set_loader(self, callback: Callable):
        self.loader = callback

    def reload(self):
        self.reloader(self)

class ExpTableDBMgr:
    def __init__(self, datadb: DataDB):
        self.datadb = datadb

    def get_required_exp(self, level: int) -> int:
        try:
            return self.datadb.exp_table[level]
        except KeyError:
            return 0

    def get_accumulate_exp(self, until_level: int) -> int:
        accumulate = [self.get_required_exp(x) for x in range(1, until_level+1)]
        return sum(accumulate)

    def clac_level(self, exp: int) -> int:
        accumulate = 0
        count = 0
        for x in range(1, len(self.datadb.exp_table)+1):
            accumulate += self.get_required_exp(x)
            if exp >= accumulate:
                count += 1
            else:
                break
        return count