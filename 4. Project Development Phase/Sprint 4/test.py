import ibm_boto3
from ibm_botocore.client import Config

COS_ENDPOINT="https://s3.tok.ap.cloud-object-storage.appdomain.cloud"
COS_API_KEY_ID="Rn7yT8V81grCqj7fP1R33bi9ENOza2XF0wqjoV3XOZQH"
COS_INSTANCE_CRN="crn:v1:bluemix:public:cloud-object-storage:global:a/640be09080b0456c8f013b1b42ceb249:5818c20b-0847-4f5c-b78e-08c75250ff51:bucket:foodbucket"


cos = ibm_boto3.client(service_name="s3",
    ibm_api_key_id=COS_API_KEY_ID,
    ibm_service_instance_id=COS_INSTANCE_CRN,
    config=Config(signature_version="oauth"),
    endpoint_url=COS_ENDPOINT)

try:
    cos.upload_file(Filename="pizza.jpg",Bucket="foodbucket",Key="pizza.jpg")
except Exception as e:
    print(Exception,e)
else:
    print('File uploaded')