# python migrate.py images.txt iad lhr bom fra
# Check the logs in migrate.log folder
# Wait for the progress bar to finish to 100%
# Check whether the image has been imported in all regions once the code is executed

import sys
import logging
import datetime
from datetime import timedelta
import time
from tqdm import tqdm
from config import Config
from oci.config import validate_config
import oci
import concurrent.futures

from percent_complete import PercentComplete

logging.basicConfig(filename='migrate.log',level=logging.INFO, format='%(levelname)s:%(name)s %(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')
logger = logging.getLogger("test")
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

    BUCKET = "CustomImages"
    ACCESS_TYPE = "ObjectRead"
    COMPARTMENT = "ocid1.compartment.oc1..aaaaaaaaeyztjbsz5yaonksmqzsb7xy6sukjrxai452ciraf7bdhu7tcceqa"

    def __init__(self, profile, image_file, regions):
        self.config = Config(profile)
        self.source_config = self.config.get_config()
        self.source_region = self.source_config["region"]
        self.source_compute_client = oci.core.ComputeClient(self.source_config)
        self.source_composite_compute_client = oci.core.ComputeClientCompositeOperations(
            self.source_compute_client
        )
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

    # Request to return image details
    def get_images_details(self, image_id):
        return self.source_compute_client.get_image(image_id=image_id).data

    # Store all image details
    def store_image_details_list(self, images_list):
        images_details = list()
        for i in images_list:
            images_details.append(self.get_images_details(i))
        return images_details

    def migrate_images(self):

        percents = list()
        names = list()
        pos = list()
        for count, image_detail in enumerate(self.images_details, start=1):
            try:
                image = self.export_image(image_detail)
                percents.append(
                    PercentComplete(self.source_config, image.id, Migrate.COMPARTMENT)
                )
                names.append(image.display_name)
                pos.append(count)
            except Exception as e:
                logger.warning("Error in the image " + image_detail.display_name)
                logger.warning(e)

        time.sleep(15)
        self.show_progress_and_import(percents, names, pos)

    def export_image(self, image):
        export_image_details = oci.core.models.ExportImageViaObjectStorageTupleDetails(
            bucket_name=Migrate.BUCKET,
            destination_type="objectStorageTuple",
            namespace_name=self.namespace,
            object_name=image.display_name,
        )
        try:
            self.source_compute_client.export_image(image.id, export_image_details)
            logger.info(image.display_name+" started exporting")
        except oci.exceptions.ServiceError as e:
            logger.warning(e.code)
            raise

        return image

    def create_expiry_time(self):
        day_late = datetime.datetime.now() + timedelta(days=7)
        self.expiry_time = day_late.strftime("%Y-%m-%dT%H:%M:%S+00:00")

    def create_PAR(self, object_name):
        par_name = object_name + "_par"
        logger.info("Creating par " + par_name)
        par_details = oci.object_storage.models.CreatePreauthenticatedRequestDetails(
            access_type=Migrate.ACCESS_TYPE,
            name=par_name,
            object_name=object_name,
            time_expires=self.expiry_time,
        )
        par_request = self.object_storage_client.create_preauthenticated_request(
            namespace_name=self.namespace,
            bucket_name=Migrate.BUCKET,
            create_preauthenticated_request_details=par_details,
        ).data
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
        destination_compute_clients = self.list_destination_compute_clients(
            self.regions
        )
        par = self.create_PAR(object_name)
        logger.info("Importing Image " + object_name)
        for cid in destination_compute_clients:
            self.import_image(par, object_name, cid)

    def import_image(self, par, object_name, cid):
        source_details = oci.core.models.ImageSourceViaObjectStorageUriDetails(
            source_type="objectStorageUri", source_uri=par
        )
        image_details = oci.core.models.CreateImageDetails(
            compartment_id=Migrate.COMPARTMENT,
            image_source_details=source_details,
            display_name=object_name,
        )
        image_details = cid.create_image(create_image_details=image_details)

    def prog(self, per, name, pos):
        with tqdm(total=100, desc=name, bar_format='{desc}: {percentage:3.0f}%|{bar} | {n_fmt}/{total_fmt}', position=pos) as progress_bar:
            temp = 0
            for i in per:
                progress_bar.update(i - temp)
                temp = i
        return name

    def show_progress_and_import(self, percent, names, position):
        with concurrent.futures.ThreadPoolExecutor() as executor:
            res = [
                executor.submit(self.prog, p, n, pos)
                for p, n, pos in zip(percent, names, position)
            ]

            for f in concurrent.futures.as_completed(res):
                object_name = f.result()
                self.import_image_all_regions(object_name)


if __name__ == "__main__":
    image_file = sys.argv[1]
    regions = list()
    for j in range(2, len(sys.argv)):
        region_short_input = sys.argv[j]
        region_destination = REGIONS_SHORT_NAMES[region_short_input]
        regions.append(region_destination)
    m = Migrate("informatica-phoenix", image_file, regions)
    print("\n\n\n\n\n\n")

