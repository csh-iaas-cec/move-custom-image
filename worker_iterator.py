from config import Config
import oci



image_id = "ocid1.image.oc1.phx.aaaaaaaa6zszjawqcyefbrwisdvpr5d6z3ppfsqpgrpayv3tlyu44mdnlmkq"
COMPARTMENT = "ocid1.compartment.oc1..aaaaaaaaeyztjbsz5yaonksmqzsb7xy6sukjrxai452ciraf7bdhu7tcceqa"


class Worker:
	def __init__(self, profile):
		self.percent = 100
		self.config = Config(profile)
		self.source_config = self.config.get_config()
		self.source_region = self.source_config["region"]
		self.source_compute_client = oci.core.ComputeClient(self.source_config)
		self.source_composite_compute_client=oci.core.ComputeClientCompositeOperations(self.source_compute_client)
		self.work_request_client = oci.work_requests.WorkRequestClient(self.source_config)


	def get_worker_request_from_image_id(self, image_id):
		work_request_id = ""
		for work_request in self.list_work_request():
			worker_state = self.get_worker_state(work_request.id)
			if self.get_worker_state(work_request.id).resources[0].identifier == image_id:
				if(worker_state.status == "IN_PROGRESS"):
					work_request_id = work_request.id
					break
		return work_request_id

	def get_percent_complete(self, work_request_id):
		return self.get_worker_state(work_request_id).percent_complete

	def get_percent_complete_from_image_id(self, image_id):
		work_request_id = self.get_worker_request_from_image_id(image_id)
		try:
			return self.get_percent_complete(work_request_id)
		except Exception as e:
			print(e)
			
		



	def list_work_request(self):
		return self.work_request_client.list_work_requests(COMPARTMENT).data

	def get_worker_state(self, worker_id):
		return self.work_request_client.get_work_request(worker_id).data
		

