Plans
-----
Have simple-server spawn in seperate process for client-to-client connection

Integrate server with twistd plugin
Enable client to use 

NOTE - THE INFORMATION BELOW CONTAINS PLANS, WHICH MAY OR MAY NOT BE IMPLEMENTED

Git Conventions
---------------
	Branches
		- Create a branch for each major change/goal.
		- Use the format <core element>/<action>/... for branch names.

-----------
Unit Tests
-----------
	Unit Tests are in place to test core features and functions.

	- Document
	    - Interface Conformance
		- Initialization
		- Opening/Closing
			- Redundant Opening
			- Redundant Closing
		- Changing/Deleting Text
			- Invalid Positions
		- Comparisons
		- Updating

	- Workspace
		- Interface Conformance
		- Initialization
		- Adding a file
			- Adding a duplicate file
		- Deleting a file
			- Deleting a nonexistant file
		- Retrieving a file

	- Serializer
		- Saving/Loading
			- Load from nonexistant file



---------------------
Protocol Version 0.2
---------------------
	
	Templates
	----------

		- Document Header
			- Document ID (Int)
			- Workspace ID (Int)
			- Hash (Int)

	General Packets
	----------------
		
		- Error Packet
			- Message (String)

		- Message Packet
			- Message (String)


	Document Oriented Packets
	--------------------------

		- Document added to workspace
			- Document Header (Template)
			- Name (String)
			- URL (String)

		- Document removed from workspace
			- Document Header (Template)

		- Document opened
			- Document Header (Template)

		- Document closed
			- Document Header (Template)

		- Document saved
			- Document Header (Template)

		- Document content modified
			- Document Header (Template)
			- Patches (String)

		- Document name modified
			- Document Header (Template)
			- New Name (String)
			
		- Document version modified
			- Document Header (Template)
			
		- Document url modified
			- Document Header (Template)
			- New URL (String)
			
		- Document metadata modified
			- Document Header (Template)


	Workspace Packets
	------------------

		- Workspace created
			- Workspace ID (Int)

		- Workspace deleted
			- Workspace ID (Int)

		- Workspace opened
			- Workspace ID (Int)
			
		- Workspace closed
			- Workspace ID (Int)

		- Workspace renamed
			- Workspace ID (Int)
			


----------------
*Connection Modes*
----------------

Client-to-Client Connection Mode
---------------------------------
	The Client-to-Client connection mode is designed for fast, impromptu 
	collaboration of documents between users. Users are able to directly 
	connect to each other, sharing and collaboration on documents within a 
	single workspace.

	Please note that this mode is intentionally simple and inherently less 
	secure than Client-to-Server mode. Users seeking a more persistant, flexible 
	solution should instead use the Client-to-Server connection mode.

	Commands available in Client-to-Client mode:
	- Start accepting connections
	- Stop accepting connections

	- Connect to client
	- Disconnect from client

	- Create document
		- From new file
		- From existing file
		- From currently open view

	- Modify Document
		- Duplicate
		- Merge
		- Rename

	- Remove Document
	- List available documents
	- View as project
	- Open document


Client-to-Server Connection Mode
---------------------------------
	The Client-to-Server connection mode is designed for persistant group usage 
	and flexibility. Users connect to a central server, adding and modifying 
	documents in workspaces. This mode allows for features such as user 
	permissions, multiple workspaces, and multiple authentication.

	Please note that there is some setup needed to enable this mode, as a
	seperate server program must be run and configured to needed parameters.
	Users seeking for a quick and simple collaborative solution should instead
	use Client-to-Client mode.

	Commands available in Client-to-Server mode:
	- Connect to server
	- Disconnect from server

	- Create new document
		- From new file
		- From existing file
		- From currently open file

	- Modify Document
		- Merge
		- Duplicate
		- Rename
	
	- Permissions
		- Change document permissions
		- Change workspace permissions
		- Change folder permissions

	- Switch workspaces
	- List Workspaces
	- Modify workspace
		- Rename workspace
		- 

---------------------
*Authentication Modes*
---------------------

Username-Password
PrivateKey-PublicKey
Anonymous-Access

---------
*Features*
---------

Workspaces
----------
	Workspaces are analagous to git repositories, Eclipse projects, etc. 
	They are collections of documents that clients and servers can access.

Versioning
----------
	Past versions of documents may be kept for easy recovery, depending on the 
	serializer and plugins used.

Permissions
-----------
	Workspaces, folders, and files all support per-user and per-group
	permissions, depending on selected plugins

