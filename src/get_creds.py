import sys
from subprocess import check_output 
import json
import getopt
import getpass

def put_credentials_to_file(key):
  try:
    f = open('globus_key.txt', 'w')
    f.write(key)
    f.close()
  except:
    print "Failure."
  return True

def get_credentials(username, password):
  print "start program"
  URL = "https://nexus.api.globusonline.org/goauth/token?grant_type=client_credentials"
  status = json.loads(check_output(["curl", "--user", "%s:%s" % (username, password), "%s" % URL]))
  
  if status.has_key("access_token"):
    key = status["access_token"]
    print "API Key is %s" % key
    return key
  else:
    print "Error when getting credentials. Status is: %s" % status
    return None

def main(argv):
  print "start program"
  username, password = None, None
  try:
    opts, args = getopt.getopt(argv, "hu:p:", ["help", "username=", "password="])
  except:
    print "Failed to initialized argument parser"
    sys.exit(0)

  for opt, arg in opts:
    if opt in ("-h", "--help"):
      print "You requested help."
      sys.exit(0)
    elif opt in ("-u", "--username"):
      username = arg
    elif opt in ("-p", "--password"):
      password = arg

  if (username is None) :
    username = getpass.getpass("Enter your username: ")

  # If the user didn't enter a password, we request hidden password using getpass
  if password is None:
    password = getpass.getpass("Enter your password: ")

  #we have arguments, now try to get a credential
  key = get_credentials(username, password)
  put_credentials_to_file(key)

def usage():
  print ""

if __name__=="__main__":
  main(sys.argv[1:])