from colliberation.serializer import DiskSerializer

class SublimeSerializer(DiskSerializer):
	"""A DiskSerializer which either uses temporary files
	
	SublimeSerializer is a variant of the DiskSerializer which ensures that all documents are saved as temporary files and folders.
	
	return
	"""