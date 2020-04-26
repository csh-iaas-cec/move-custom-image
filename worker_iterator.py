from config import Config
import oci


class Worker:
    def __init__(self, profile, compartment):
        Worker.compartment = compartment
        self.percent = 100
        self.config = Config(profile)
        self.source_config = self.config.get_config()
        self.source_region = self.source_config["region"]
        self.source_compute_client = oci.core.ComputeClient(self.source_config)
        self.source_composite_compute_client = oci.core.ComputeClientCompositeOperations(
            self.source_compute_client
        )
        self.work_request_client = oci.work_requests.WorkRequestClient(
            self.source_config
        )
        self.image_worker = dict()

    def get_worker_request_from_image_id(self, image_id):
        # work_request_id = ""
        for work_request in self.list_work_request():
            worker_state = self.get_worker_state(work_request.id)
            if (
                self.get_worker_state(work_request.id).resources[0].identifier
                == image_id
            ):
                if worker_state.status == "IN_PROGRESS":
                    work_request_id = work_request.id
                    return work_request_id

    def get_percent_complete(self, work_request_id):
        try:
            return self.get_worker_state(work_request_id).percent_complete
        except Exception:
            raise Exception

    def get_percent_complete_from_image_id(self, image_id):
        try:
            work_request_id = self.image_worker["image_id"]
        except Exception:
            work_request_id = self.get_worker_request_from_image_id(image_id)
            self.image_worker["image_id"] = work_request_id
        return self.get_percent_complete(work_request_id)

    def list_work_request(self):
        return self.work_request_client.list_work_requests(Worker.compartment).data

    def get_worker_state(self, worker_id):
        try:
            return self.work_request_client.get_work_request(worker_id).data
        except Exception:
            raise
