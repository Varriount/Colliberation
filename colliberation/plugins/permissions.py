class UserPermissions(object):
	def pre_open_document(self, document, protocol):
		protocol_groups = protocol.groups
		document_groups = document.groups
		if not protocol_groups.disjoint(document_groups):

