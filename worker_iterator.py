from config import Config
import oci
import logs

logger = logs.logger


class Worker:
    def __init__(self, config, compartment):
        Worker.compartment = compartment
        self.percent = 100
        self.source_config = config
        self.work_request_client = oci.work_requests.WorkRequestClient(
            config=self.source_config, retry_strategy=oci.retry.DEFAULT_RETRY_STRATEGY
        )
        self.image_worker = dict()

    def get_worker_request_from_image_id(self, image_id):
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
        except Exception as e:
            logger.warning(e)
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
        except oci.exceptions.ConnectTimeout as e:
            logger.warning(e)
