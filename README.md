# Parallel Cloud Research

This project allows to run parallel computing jobs on an AWS infrastructure based on the "AWS Batch" Service.

# Installation
Create the cloudformation stack with **infrastructure/cloudformation.yaml**.

Note the stack outputs.

Apply the user groups from the stack output to the desired users.

The stack uses p2.xlarge instances. Make sure to request a service quota that fits your desired computing capacity.

# Usage
### Deploy your application as a docker container.

The following environment variables are available:

* S3_JOB_BUCKET - The S3 bucket for in- and outputs
* S3_JOB_CONFIG_KEY - The JSON input configuration
* S3_JOB_PREFIX - S3 object key prefix for additional job data
* S3_OUTPUT_OJBECT_KEY - S3 object key for the JSON outputs
* BATCH_ID - ID of the current job batch

You find an example in the **example/** folder.

### Push your docker image to the repository (ECR)

You can find the necessary commands within the AWS Console if you select the repository in the "ECR" service and click "View push commands".
You can use tags for different applications and versions.

Example:

```
aws ecr get-login-password --region eu-central-1 | docker login --username AWS --password-stdin <account>.dkr.ecr.eu-central-1.amazonaws.com
docker build -t example-v1 ./example/worker
docker tag example-v1 <account>.dkr.ecr.eu-central-1.amazonaws.com/<repository>:example-v1
docker push <account>.dkr.ecr.eu-central-1.amazonaws.com/<repository>:example-v1`
```

### Start jobs with the PCR library

Install the PCR package. You can do this for example with the '-e' option of pip.

The documentation of the library can be found in [api-documentation.md](api-documentation.md)

Use the PCR library to write your script that starts the jobs. You can find an example in **example/start_job.py** The example file needs to be configured with the created infrastructure endpoints.

```
python3 -m pip install -e .
python3 example/start_job.py
```


### Wait for all jobs to finish and gather your results from S3.
Example:
```
Registered Job Definition: example_c6bc6ee9-96c2-4a52-ad3c-9761aac63858
Created input data: s3://example-jobbucket-2ivzdyi4rufj/jobs/example_c6bc6ee9-96c2-4a52-ad3c-9761aac63858/000000/config.json
Job ID: 7fbbc9bb-2aa4-4c78-8407-84d4512b6543
Waiting for jobs to finish.
Jobs finished: 0/1
Jobs finished: 0/1
Jobs finished: 1/1
All jobs finished.
Job definition deregistered.
[{'x+y': 5, 'x*y': 6}]
```

# Maintenance
The following section contains suggestions about maintaining the infrastructure after stack installation.

## Check for unused resources
Possible locations of unused data that should be deleted regularly:
* job data in S3
* cloud watch logs
* batch job definitions

## Check costs
 The costs of multiple running gpu instances can accumulate quickly. Daily monitoring of costs is recommended.
 
# Customization
Documentation of the system architecture can be found in [documentation/architecture-documentation.md](documentation/architecture-documentation.md).

The python library provides a convenient way to use the computing infrastructure. 
Nevertheless, the infrastructure can be accessed in other ways, e.g. via
* AWS Console, 
* AWS CLI
* other programming libraries

The python "PCR" package uses it's own conventions to create and identify batch jobs. E.g. it uses UUIDs to create unique names and puts JSON files to S3 to pass configuration to docker containers.
Customization deviations from those conventions are possible, e.g. input parameters could be passed exclusively via environment variables without JSON files or YAML files could be used.
