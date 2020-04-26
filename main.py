import oci
import pickle
from oci.config import validate_config
import sys
import threading
from multiprocessing.pool import ThreadPool as Pool
import os
import datetime
from datetime import timedelta

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


# config_lasya = {
#     "user":"ocid1.user.oc1..aaaaaaaapm7g722n5zaobichqozwbey7jkduth56pdjgo4dikhtaqcjzchiq",
#     "key_file":"~/.oci/oci_lasya.pem",
#     "fingerprint":"34:2e:e9:f7:a2:ea:52:2f:23:4f:c2:41:54:ff:46:ba",
#     "tenancy":"ocid1.tenancy.oc1..aaaaaaaapf32iocmevidwi4ujtrnfvq456dp4elubzvw564v6lh2sby24uua",
#     "region": "us-ashburn-1"
# }

config = {
    "user": "ocid1.user.oc1..aaaaaaaaz4drojh2wnfiisjnadclxifm7k5v2nk2a3lkoqjfdnk67s6rqocq",
    "fingerprint": "48:2f:51:7e:69:ef:c3:e8:55:11:a3:4d:e9:2f:3c:3e",
    "key_file": "~/.oci/ravello.pem",
    "tenancy": "ocid1.tenancy.oc1..aaaaaaaavijeuzmg3qs5sgvrkg3mlv4ndg6ejss3lhu3qbyslacfpa2uprhq",
    "region": "us-phoenix-1",
}


validate_config(config)


BUCKET = "CustomImages"
NAMESPACE = "idnsgznaeqlg"
COMPARTMENT = "ocid1.compartment.oc1..aaaaaaaaeyztjbsz5yaonksmqzsb7xy6sukjrxai452ciraf7bdhu7tcceqa"
comp = "ocid1.compartment.oc1..aaaaaaaac4zmgwwe2pg2iraydy7lutqyugj22udiku5feq6inwfcrg6lyaja"


def export_image(image_id, image_name):
    print("Exporting " + image_name)
    export_image_details = oci.core.models.ExportImageViaObjectStorageTupleDetails(
        bucket_name=BUCKET,
        destination_type="objectStorageTuple",
        namespace_name=NAMESPACE,
        object_name=image_name,
    )
    res = cis.export_image(image_id, export_image_details).data


def create_par(object_name):
    par_name = object_name + "_par"
    expirytime = later.strftime("%Y-%m-%dT%H:%M:%S+00:00")
    print("Creating par " + par_name)
    par_details = oci.object_storage.models.CreatePreauthenticatedRequestDetails(
        access_type="ObjectRead",
        name=par_name,
        object_name=object_name,
        time_expires=expirytime,
    )
    par_request = co.create_preauthenticated_request(
        namespace_name=NAMESPACE,
        bucket_name=BUCKET,
        create_preauthenticated_request_details=par_details,
    ).data
    par = "https://objectstorage.us-phoenix-1.oraclecloud.com" + par_request.access_uri
    return par


def import_image(par, object_name, cid):
    print("Importing Image " + object_name)
    source_details = oci.core.models.ImageSourceViaObjectStorageUriDetails(
        source_type="objectStorageUri", source_uri=par
    )
    image_details = oci.core.models.CreateImageDetails(
        compartment_id=COMPARTMENT,
        image_source_details=source_details,
        display_name=object_name,
    )
    image_details = cid.create_image(create_image_details=image_details)


#############
# Waits for the image to be exported
# creates par and initiates import of image


def is_image_available(image_id, object_name, cicd):
    print("Waiting for image to be exported")
    image_response = cis.get_image(image_id)
    oci.wait_until(cis, image_response, "lifecycle_state", "AVAILABLE")
    print(image_response.data.lifecycle_state)
    print("Image Exported " + object_name)
    par = create_par(object_name)
    print("PAR created " + par)
    image_export = import_image(par, object_name, cicd)


source_config = config
cis = oci.core.ComputeClient(source_config)
cics = oci.core.ComputeClientCompositeOperations(cis)
co = oci.object_storage.ObjectStorageClient(source_config)


image_file = sys.argv[1]
f = open(image_file, "r")
f1 = f.readlines()
f.close()
later = datetime.datetime.now() + timedelta(days=7)
expirytime = later.strftime("%Y-%m-%dT%H:%M:%S+00:00")
pool_size = 5
pool = Pool(pool_size)
image_export = []
for i in f1:
    image_details = cis.get_image(image_id=i.strip()).data
    image_export.append(image_details)
    pool.apply_async(export_image, (image_details.id, image_details.display_name,))

pool.close()
pool.join()
pool1 = Pool(pool_size)
for i in image_export:
    print(i.display_name)

    for j in range(2, len(sys.argv)):
        region_short_input = sys.argv[j]
        region_destination = REGIONS_SHORT_NAMES[region_short_input]
        config["region"] = region_destination
        dest_config = config
        validate_config(dest_config)

        cid = oci.core.ComputeClient(dest_config)
        pool1.apply_async(is_image_available, args=(i.id, i.display_name, cid))
pool1.close()
pool1.join()
