import ibm_boto3
from ibm_botocore.client import Config
import os


credentials = {
  "apikey": "",
  "cos_hmac_keys": {
    "access_key_id": "",
    "secret_access_key": ""
  },
  "endpoints": "https://cos-service.bluemix.net/endpoints",
  "iam_apikey_description": "",
  "iam_apikey_name": "auto-generated-apikey-8d9bbbd2-fa92-4e23-8045-fd9dcfffd92a",
  "iam_role_crn": "crn:v1:bluemix:public:iam::::serviceRole:Manager",
  "iam_serviceid_crn": "crn:v1:bluemix:public:iam-identity::a/32b7e26636a8b1af308ee6b24f52f147::serviceid:ServiceId-28c8ba3d-9f18-48ec-9377-37f2ce82feb5",
  "resource_instance_id": "crn:v1:bluemix:public:cloud-object-storage:global:a/32b7e26636a8b1af308ee6b24f52f147:306dbe88-ece9-47ac-904c-53e98283833a::"
}

bucket_name = 'gradepredictionproject-donotdelete-pr-2blogqs6na5gkq'

auth_endpoint = 'https://iam.bluemix.net/oidc/token'#'https://iam.ng.bluemix.net/oidc/token'
service_endpoint = 'https://s3.eu-geo.objectstorage.softlayer.net'


def initConnection():
    global resource
    resource = ibm_boto3.resource('s3',
                              ibm_api_key_id=credentials['apikey'],
                              ibm_service_instance_id=credentials['resource_instance_id'],
                              ibm_auth_endpoint=auth_endpoint,
                              config=Config(signature_version='oauth'),
                              endpoint_url=service_endpoint)


########################################
##LIST BUCKETS
def listBuckets():
    global resource
    for bucket in resource.buckets.all():
        print(bucket)
    
########################################
##LIST FILES (KEYS) IN BUCKET

def get_keys_from_bucket(bucket_name):
    global resource
    bucket = resource.Bucket(bucket_name)
    keys = list()
    for o in bucket.objects.all():
        keys.append(o.key)
    return keys


##UPLOAD
def upload_file(filename):
    global resource
    resource.Bucket(name=bucket_name).upload_file(Filename=filename,Key=filename)
    print(filename +' sent')