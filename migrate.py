import sys
import datetime
from datetime import timedelta
import logs
from config import Config
from oci.config import validate_config
import oci
import concurrent.futures
import argparse
import time

logger = logs.logger
REGIONS_SHORT_NAMES = {
	"phx": "us-phoenix-1",
	"iad": "us-ashburn-1",
	"fra": "eu-frankfurt-1",
	"zrh": "eu-zurich-1",
	"lhr": "uk-london-1",
	"yyz": "ca-toronto-1",
	"nrt": "ap-tokyo-1",
	"icn": "ap-seoul-1",
	"bom": "ap-mumbai-1",
	"gru": "sa-saopaulo-1",
	"syd": "ap-sydney-1",
	"ltn": "uk-gov-london-1",
	"kix": "ap-osaka-1",
	"mel": "ap-melbourne-1",
	"ams": "eu-amsterdam-1",
	"jed": "me-jeddah-1",
	"yul": "ca-montreal-1",
}


class Migrate:

	BUCKET = "STOREIMAGES"
	ACCESS_TYPE = "ObjectRead"
	COMPARTMENT = "ocid1.compartment.oc1..aaaaaaaaeyztjbsz5yaonksmqzsb7xy6sukjrxai452ciraf7bdhu7tcceqa"
	
	def __init__(self, profile, image_file, regions, compartment_id=None, bucket_name=None):
		self.config = Config(profile)
		self.compartment_id = compartment_id
		self.bucket_name = bucket_name
		self.initialize()
		self.source_config = self.config.get_config()
		self.source_region = self.source_config["region"]
		self.source_compute_client = oci.core.ComputeClient(self.source_config)
		self.source_composite_compute_client=oci.core.ComputeClientCompositeOperations(self.source_compute_client)
		self.object_storage_client = oci.object_storage.ObjectStorageClient(
			self.source_config
		)
		self.namespace = self.object_storage_client.get_namespace().data
		self.regions = regions
		self.create_expiry_time()
		images = self.get_image_ocids(image_file)
		self.images_details = self.store_image_details_list(images)
		self.migrate_images()
		

	# Read the contents of the file and store in a variable and return it

	def get_image_ocids(self, file_name):
		image_ocids = list()
		with open(file_name, "r") as f:
			image_ocids = f.readlines()
		images = list()
		for i in image_ocids:
			images.append(i.strip())
		return images

	def initialize(self):
		self.update_compartment(self.compartment_id)
		self.update_bucket_name(self.bucket_name)
		print("Script started executing")
		logger.info("Script started executing")
	
	@classmethod
	def update_compartment(cls, value):
		if(value):
			cls.COMPARTMENT = value

	@classmethod
	def update_bucket_name(cls, value):
		if(value):
			cls.BUCKET = value

	# Request to return image details
	def get_images_details(self, image_id):
		try:
			return self.source_compute_client.get_image(image_id=image_id).data
		except Exception as e:
			print(f"{image_id} doesn't exist")
			logger.error(f"{image_id} doesn't exist")
			logger.error(e)
			raise

	# Store all image details
	def store_image_details_list(self, images_list):
		images_details = list()
		for i in images_list:
			time.sleep(1)
			try:
				detail = self.get_images_details(i)
				images_details.append(detail)
				print(f"Initializing to start exporting image {detail.display_name}")
				logger.info(f"Initializing to start exporting image {detail.display_name}")
			except Exception as e:
				print(e)
				logger.error(e)
				logger.error(f"Skipping {i} Image as it doesn't exist. \
					Please check the OCID of the image whether it exists in the specified compartment ")
			
			
		return images_details

	def migrate_images(self):
		with concurrent.futures.ThreadPoolExecutor() as executor:
			results = [
				executor.submit(self.export_image, image_detail)
				for image_detail in self.images_details
			]

			for f in concurrent.futures.as_completed(results):
				object_name = f.result()
				try:
					self.import_image_all_regions(object_name)
					logger.info(f"{object_name} successfuly started importing in regions")
				except Exception as e:
					logger.error(f"Importing of image {object_name} cancelled")
					logger.error(e)

			
	def export_image(self, image):
		export_image_details = oci.core.models.ExportImageViaObjectStorageTupleDetails(
			bucket_name=Migrate.BUCKET,
			destination_type="objectStorageTuple",
			namespace_name=self.namespace,
			object_name=image.display_name,
		)
		print(f"Started to export image {image.display_name}")
		logger.info(f"Started to export image {image.display_name}")
		try:
			self.source_composite_compute_client.export_image_and_wait_for_state(image.id, export_image_details,  wait_for_states=["AVAILABLE"], waiter_kwargs={"max_wait_seconds": 7200, "max_interval_seconds": 45})
			name = image.display_name
			print(f"Exported {image.display_name}")
			logger.info(f"Exported {image.display_name}")
		except oci.exceptions.CompositeOperationError as e:
			logger.error(type(e))
			logger.error(e.partial_results)
			logger.error(e.cause)
			print(f"Error exporting the image {image.display_name}")
			logger.error(f"Error exporting the image {image.display_name}")
			name = None
		
			
		return name

	def create_expiry_time(self):
		day_late = datetime.datetime.now() + timedelta(days=7)
		self.expiry_time = day_late.strftime("%Y-%m-%dT%H:%M:%S+00:00")

	def create_PAR(self, object_name):
		par_name = object_name + "_par"
		print("Creating par " + par_name)
		try:
			par_details = oci.object_storage.models.CreatePreauthenticatedRequestDetails(
				access_type=Migrate.ACCESS_TYPE,
				name=par_name,
				object_name=object_name,
				time_expires=self.expiry_time,
			)
		except Exception as e:
			print(e)
			logger.error(e)
			raise
		try:
			par_request = self.object_storage_client.create_preauthenticated_request(
				namespace_name=self.namespace,
				bucket_name=Migrate.BUCKET,
				create_preauthenticated_request_details=par_details,
			).data
		except Exception as e:
			print(e)
			logger.error(e)
			raise
		par = (
			"https://objectstorage."
			+ self.source_region
			+ ".oraclecloud.com"
			+ par_request.access_uri
		)
		return par


	def get_destination_compute_client(self, region):
		self.config.set_region(region)
		config = self.config.get_config()
		return oci.core.ComputeClient(config)

	def list_destination_compute_clients(self, regions):
		destination_compute_clients = [
			self.get_destination_compute_client(i) for i in regions
		]
		return destination_compute_clients

	def import_image_all_regions(self, object_name):
		destination_compute_clients = self.list_destination_compute_clients(self.regions)
		try:
			par = self.create_PAR(object_name)
			print(f"Creation of PAR is successful for image {object_name}")
			logger.info(f"Creation of PAR is successful for image {object_name}")
		except Exception as e:
			logger.error(e)
			logger.error(f"Can't create PAR terminating the process of exporting the image {object_name}")
			raise
		
		for cid,region in zip(destination_compute_clients,self.regions):
			self.import_image(par, object_name, cid, region)

	def import_image(self, par, object_name, cid, region):
		print(f"Importing Image {object_name} in {region} region.")
		source_details = oci.core.models.ImageSourceViaObjectStorageUriDetails(
			source_type="objectStorageUri", source_uri=par
		)
		image_details = oci.core.models.CreateImageDetails(
			compartment_id=Migrate.COMPARTMENT,
			image_source_details=source_details,
			display_name=object_name,
		)
		image_details = cid.create_image(create_image_details=image_details).data
		with open("images_details.txt","w") as f:
			f.write(image_details.id+","+region+"\n")
		print(f"Importing image {object_name} started successfully ")
		logger.info(f"Importing image {object_name} started successfully ")


if __name__ == "__main__":
	description = "\n".join(["Migrates the custom images to given destination regions","pip install -r requirements.txt","python migrate.py <images_list_file_name.txt> iad lhr bom phx"])
	parser = argparse.ArgumentParser(description=description,
									 formatter_class=argparse.RawDescriptionHelpFormatter)
	parser.add_argument('--profile', help='Provide the profile to be used', required=True)
	parser.add_argument('--file',
						help="Provide the text file which contains image ocids. ", required=True)
	parser.add_argument('--regions', nargs='+',
						help="Updates the volume and backups tags from the given instance id", required=True)
	parser.add_argument('--compartment_id', help='Provide the compartment ID where the images exist. (OPTIONAL) If not provided takes default compartment id')
	parser.add_argument('--bucket_name', help="Provide bucket name for the images to be stored. OPTIONAL if not provided takes default bucket")
	
	
	args = parser.parse_args()
	PROFILE = args.profile
	compartment_id = None
	bucket_name = None
	if(args.compartment_id):
		compartment_id = args.compartment_id
	if(args.bucket_name):
		bucket_name = args.bucket_name
	image_file = args.file
	regions_list = args.regions
	regions = list()
	for j in regions_list:
		region_destination = REGIONS_SHORT_NAMES[j]
		regions.append(region_destination)
	m = Migrate(PROFILE, image_file, regions, compartment_id, bucket_name)
	print("Completed")