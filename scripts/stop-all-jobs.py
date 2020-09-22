# This script stops all jobs in "runnable" state of a job queue.
# Requires a properly set up AWS CLI or other source of credentials.
#
# Usage:
#   - first argument has to be the job queue ARN

import boto3
import sys

job_queue_arn = sys.argv[1]
aws_batch = boto3.client('batch')
paginator = aws_batch.get_paginator('list_jobs')

job_paginator = paginator.paginate(
    jobQueue=job_queue_arn,
    jobStatus='RUNNABLE',
    PaginationConfig={
        'PageSize': 50,
    }
)

for jobs_response in job_paginator:
    for job in jobs_response['jobSummaryList']:
        jobId = job['jobId']
        jobName = job['jobName']

        response = aws_batch.terminate_job(
            jobId=jobId,
            reason='Manual cancellation.'
        )
        
        print('Killed job ' + jobId + ' ' + jobName)
