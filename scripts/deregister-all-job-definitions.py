# This script deregisters all active job definitions.
# Requires a properly set up AWS CLI or other source of credentials.

import boto3

awsBatch = boto3.client('batch')
paginator = awsBatch.get_paginator('describe_job_definitions')

for response in paginator.paginate(maxResults=100, status='ACTIVE'):
    for job_definition in response['jobDefinitions']:
        awsBatch.deregister_job_definition(
            jobDefinition=job_definition['jobDefinitionArn'],
        )
        
        print('Deregistered job definition ' + job_definition['jobDefinitionArn'])
