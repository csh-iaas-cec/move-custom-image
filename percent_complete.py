from worker_iterator import Worker
import time
class PercentComplete:
    def __init__(self, profile, image_id, size_in_mbs=0):
        self.size_in_mbs = size_in_mbs
        self.percent = 100
        self.worker = Worker(profile)
        self.image_id = image_id
        self.temp = 0

    def __iter__(self):
        self.res = 0
        return self

    def __next__(self):
        if self.res < self.percent:
            try:
                self.res = self.worker.get_percent_complete_from_image_id(self.image_id)
            except Exception:
                self.res = self.percent
            
            return int(self.res)
        else:
            raise StopIteration

