#!/usr/bin/python
import requests 
import json 
import urllib 
import sys
import getopt

'''

TODO:

-- check endpoint validity before sending the transfer
-- monitor transfer?
  - unsure if we want this kind of feature for the script.
  - if so we'd probably set up a while loop, keep polling the transfer list for all transfers, 
    check the one that matches our transfer id, and only quit the while loop once we
    receive a poll with an exit condition met.
-- other things?

'''

def read_token():
  try: 
    f = open('globus_key.txt')
    key = f.read()
    #print "read key is %s" % key
  except:
    key = None
  return key

def activate_endpoint(base_url, headers, endpoint_name):

  r = requests.get(base_url + "/endpoint/%s" % urllib.quote_plus(endpoint_name), headers=headers)
  print "Getting info about %s" % endpoint_name
  info = json.loads(r.text)
  #print info
  #print info
  if (not info.has_key("activated")) or not info["activated"] :
    print "%s not activated... Activating"
    r1 = requests.post(base_url + "/endpoint/%s/autoactivate" % urllib.quote_plus(endpoint_name), 
      headers=headers, data=None)
    print r1.text
    # TODO: need logic here to handle a request failure (activation fails)
    return True
  else:
    print "Activated on %s" % endpoint_name
    return True

def get_submission_id(base_url, headers):
  r = requests.get(base_url + "/submission_id", headers=headers)
  print "Requested transfer id and got %s" % r.text
  result = json.loads(r.text)
  if result.has_key("value"):
    submission_id = json.loads(r.text)["value"]
    return submission_id
  else:
    print "Error getting submission ID"
    return None

def submit_transfer(base_url, headers, submission_id, sync_level, source_endpoint, 
    destination_endpoint, source_path, destination_path, recursive):

  #Note: globus won't accept punctuation in the transfer label field, so we'll strip
  #the # from endpoint names.

  transfer_label = "Transfer from %s to %s" % (source_endpoint.replace('#', ' '), 
    destination_endpoint.replace('#', ' '))

  payload = json.dumps({
    "submission_id" : submission_id,
    "DATA_TYPE" : "transfer",
    "sync_level" : sync_level,
    "source_endpoint" : source_endpoint,
    "label" : transfer_label, 
    "length" : 1,
    "destination_endpoint" : destination_endpoint,
    "DATA" : [{
      "source_path" : source_path,
      "destination_path" : destination_path, 
      "verify_size" : None, 
      "recursive" : recursive,
      "DATA_TYPE" : "transfer_item"
      }]
    })
  r = requests.post(base_url + "/transfer", headers=headers, data=payload)
  result = json.loads(r.text)
  if result.has_key("code"):
    if result["code"] == "Accepted":
      print "Success! Transfer accepted and queued."
    else:
      print "Transfer was not accepted. We got: %s" % r.text
      return None
  else:
    print "There was an error making the transfer request. We got: %s " % r.text
    return None
  return True

def usage():
  print """
      -----------------------------
      GLOBUS MIRROR SCRIPT -- USAGE
      -----------------------------

      This is a Python script designed to let you easily transfer files or directories between
      endpoints on the Globus network.

      In order to use this script, you must be a valid Globus user and have a Globus Transfer API 
      key. Obtain one by running the companion get_creds.py script. Said script will generate 
      your API key and place it in a file on your machine, and this script will read your key 
      from that file.

      -----------------------------
      USAGE
      -----------------------------

      python mirror.py -S [source_endpoint] -D [source_destination] -s [source_file_or_directory]
        -d [destination_file_or_directory]  [optional: [-r, -y [sync_level] ] ]

      -----------------------------
      ARGUMENTS
      -----------------------------

      -S --source_endpoint 

        The name of the source endpoint, e.g. xyz#123. Is a string.
      
      -D --dest_endpoint  

        The name of the destination endpoint, e.g. 123#xyz. Is a string.
    
      -s --source_transfer

        The name of the source file or directory. Is a string. If the source is a directory, the 
        -r flag must also be provided, else the transfer will fail.

      -d --dest_transfer  

        The name of the target file or directory. Is a string. If the target is a directory, the 
        -r flag must also be provided, else the transfer will fail.

      -y --sync_level  

        An integer from 0-3 representing the transfer's sync_level, as defined by Globus. Here are 
        the sync levels from the Globus Transfer API:

        0 - Copy files that do not exist at the destination
        1 - Copy files if the size of the destination does not match the size of the source
        2 - Copy files if the timestamp of the destination is older than the timestamp of the source (recommended default)
        3 - Copy files if checksums of the source and destination do not match

        Default is 2, as per recommendation. 

        See https://transfer.api.globusonline.org/v0.10/document_type/transfer/field/sync_level?format=html for more
        details.

      -r --recursive   

        If you want to transfer an entire directory, you must transfer in recursive mode.

      -h --help 

        Prints out this wonderful document.

    """

def main(argv):
  BASE_URL = "https://transfer.api.globusonline.org/v0.10"
  TOKEN = "Globus-Goauthtoken %s" % read_token()
  source_endpoint, dest_endpoint, source_transfer, dest_transfer = "", "", "", ""
  sync_level = 2
  recursive = False

  if TOKEN is None:
    print "Error retrieving token. Did you run get_creds.py to obtain a globus API key?"
    sys.exit(0)
  headers = {"Authorization" : TOKEN, 
  "Content-Type" : "application/json"}

  try:
    opts, args = getopt.getopt(argv, "hS:D:s:d:y:r", ["help", "source_endpoint=", 
      "dest_endpoint=", "source_transfer=", "dest_transfer=", "sync_level=", "recursive"])
  except:
    print "Failed to initialized argument parser"
    sys.exit(0)

  for opt, arg in opts:
    if opt in ("-h", "--help"):
      usage()
      sys.exit(0)
    elif opt in ("-S", "--source_endpoint"):
      source_endpoint = arg
    elif opt in ("-D", "--destination_endpoint"):
      dest_endpoint = arg
    elif opt in ("-s", "--source_transfer"):
      source_transfer = arg
    elif opt in ("-d", "--dest_transfer"):
      dest_transfer = arg
    elif opt in ("-y", "--sync_level"):
      if arg not in (0, 1, 2, 3):
        print "Sync level must be an integer from 0-3 inclusive.\n\n"
        usage()
      sync_level = arg
    elif opt in ("-r", "--recursive"):
      recursive = True

  if "" in (source_endpoint, dest_endpoint, source_transfer, dest_transfer):
    print """You MUST enter a source endpoint, destination endpoint, source file/directory, 
      and destination file/directory.\n\n"""
    usage()
    sys.exit(0)

  activate_endpoint(BASE_URL, headers, source_endpoint)
  activate_endpoint(BASE_URL, headers, dest_endpoint)
  submission_id = get_submission_id(BASE_URL, headers)

  submit_transfer(BASE_URL, headers, submission_id, sync_level, source_endpoint, dest_endpoint, 
    source_transfer, dest_transfer, recursive)

if __name__=="__main__":
  main(sys.argv[1:])