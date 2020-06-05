from migrate import Migrate





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
	parser.add_argument('--import_image', help="Only import images which are failed previously")
	
	
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
	m.move_images()
	print("Completed")