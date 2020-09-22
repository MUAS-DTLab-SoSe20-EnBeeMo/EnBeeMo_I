# This script is an example how to start a batch of computing jobs with the PCR system.
# Requires a properly set up AWS CLI or other source of credentials.
#
# Usage:
#   - copy this script to your machine (optional)
#   - install the PCR python package (see readme.md)
#   - prepare and push your example docker image
#   - replace the placeholders in the parameters below with your endpoints
#   - read and comprehend  the script
#   - run the script
#   - wait until finished
#   - check results

import json

from PCR.JobSubmitter import JobSubmitter

# infrastructure parameters
containerImage = '<your manually pushed docker image>'
job_queue = '<the aws batch queue - SEE CLOUDFORMATION STACK OUTPUT>'
job_bucket = '<the job bucket name - SEE CLOUDFORMATION STACK OUTPUT>'

batch_name = 'example'

# Initialize job submitter
job_submitter = JobSubmitter(
    batch_name=batch_name,
    container=containerImage,
    job_queue=job_queue,
    job_bucket=job_bucket,
)

job_id = job_submitter.submit_job(input_data={
    'x': 2,
    'y': 3
})

job_submitter.wait_until_jobs_finished()

json_outputs = job_submitter.get_all_outputs()

outputs = []

for json_output in json_outputs:
    output = json.loads(json_output)
    outputs.append(output)

print(outputs)
