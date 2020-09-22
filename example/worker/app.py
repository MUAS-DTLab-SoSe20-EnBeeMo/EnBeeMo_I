import boto3
import os
import json

S3_JOB_BUCKET = os.environ.get('S3_JOB_BUCKET')
S3_JOB_CONFIG_KEY = os.environ.get('S3_JOB_CONFIG_KEY')
S3_OUTPUT_OJBECT_KEY = os.environ.get('S3_OUTPUT_OJBECT_KEY')

aws_s3 = boto3.client('s3')

config_data = json.loads(
    aws_s3.get_object(Bucket=S3_JOB_BUCKET, Key=S3_JOB_CONFIG_KEY)['Body']
        .read()
        .decode('utf-8')
)

x = config_data.get('x')
y = config_data.get('y')

results = {
    'x+y': x + y,
    'x*y': x * y
}

aws_s3.put_object(Body=bytes(json.dumps(results), 'utf-8'), Bucket=S3_JOB_BUCKET, Key=S3_OUTPUT_OJBECT_KEY)
