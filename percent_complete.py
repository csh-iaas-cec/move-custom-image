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
            self.res = self.worker.get_percent_complete_from_image_id(self.image_id)
            return int(self.res)
        else:
            raise StopIteration

if __name__ == "__main__":
    image_id = "ocid1.image.oc1.phx.aaaaaaaav6ue3pjrakbmeonq62lrwethg6yuxirg5sov2zaq7p7cjjgshuwa"
    per = PercentComplete("informatica-phoenix", image_id)
    image_details = per.worker.get_images_details(image_id)
    per.worker.export_image(image_details)
    time.sleep(10)
    for i in per:
        print(i)