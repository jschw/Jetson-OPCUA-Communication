from opcua import Client
from opcua import ua
import json

def getOpcConnection(ConfigFilePath: str) ->None:
	# Load json config file
	f = open(ConfigFilePath,) 
	config = json.load(f) 
	f.close()

	# Get network settings
	protocol = config['network_settings'][0]['protocol']
	host = config['network_settings'][0]['host']
	port = config['network_settings'][0]['port']
	address = protocol + '://' + host + ':' + port

	# Configure connection
	OpcConnection = Client(address)

	# Open connection and try to get all nodes
	try:
		OpcConnection.connect()

		ClientNodes = {}

		# Get nodes
		for node in config['opc_nodes']: 
		    ClientNodes[node['name']] = OpcConnection.get_node('ns=' + node['namespace_index'] + ';s=' + node['string_id'])

		return OpcConnection, ClientNodes
	except:
		return None, None
