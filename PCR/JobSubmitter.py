import math
import re
import time
from typing import List, Callable
import boto3
import uuid
import json


class JobSubmitter:
    """
    Starts a batch of jobs for the PCR infrastructure.
    
    Example usage:
        1. instantiate
        2. submit_job()
        3. wait_until_jobs_finished()
        4. get_all_outputs()
        
    Additional functionality:
        - get_batch_id()
        - get_job_directory()
        - get_output()
    """
    
    def __init__(
            self,
            batch_name: str,
            job_queue: str,
            container: str,
            job_bucket: str,
            memory_in_mb: int = 1024,
            aws_region: str = None,
            aws_access_key_id: str = None,
            aws_secret_access_key: str = None,
            timeout_in_hours: int = 20,
            polling_interval_seconds: int = 60,
            request_throttling_milliseconds: int = 200
    ):
        """
        :param batch_name:
            Human readable name of the set of jobs.
            The name is used for job folder paths in S3.
            The first character must be alphanumeric.
            Up to 90 letters.
            Numbers, hyphens, and underscores are allowed.
        :param container:
            Location of the docker container to use for this batch.
        :param job_bucket:
            S3 bucket name to use for persisting in- and output data.
        :param memory_in_mb:
            Memory for the docker container.
        :param aws_access_key_id: optional
            AWS CLI access key.
        :param aws_secret_access_key: optional
            AWS CLI secret key.
        :param aws_region:
            AWS region, has to match the region of the job queue.
        :param job_queue:
            Name of the job queue to submit jobs to.
        """
        
        self.batch_name = batch_name
        self.batch_id = batch_name + '_' + str(uuid.uuid4())
        self.container = container
        self.job_bucket = job_bucket
        self.aws_access_key_id = aws_access_key_id
        self.aws_secret_access_key = aws_secret_access_key
        self.aws_region = aws_region
        self.job_queue = job_queue
        self.memory_in_mb = memory_in_mb
        self.job_ids = []
        self.job_dirs_by_job_id = {}
        self.job_iterator_by_job_id = {}
        self.job_iterator = 0
        self.output_object_keys_by_job_id = {}
        self.job_states_by_job_id = {}
        self.callbacks_by_job_id = {}
        self.unfinished_jobs = set()
        self.batch_api_batch_size = 100
        self.job_definition_arn = None
        self.timeout_in_seconds = timeout_in_hours * 60 * 60
        self.polling_interval_seconds = polling_interval_seconds
        self.request_throttling_seconds = request_throttling_milliseconds / 1000
        
        # max 90 characters, so that we can append a uuid and still be below 128 characters
        name_validator = re.compile(r'^[a-zA-Z0-9][a-zA-Z0-9\d_-]{0,90}$')
        
        # ensure that batch name is compatible
        if name_validator.match(batch_name) is None:
            raise ValueError(
                'Please choose a machine-friendly batch name: first letter alphanumeric;'
                + ' max 90 characters; numbers, hyphens and underscores allowed'
            )
        
        self.aws_batch = boto3.client(
            'batch',
            region_name=self.aws_region,
            aws_access_key_id=self.aws_access_key_id,
            aws_secret_access_key=self.aws_secret_access_key
        )
        
        self.aws_s3 = boto3.client(
            's3',
            region_name=self.aws_region,
            aws_access_key_id=self.aws_access_key_id,
            aws_secret_access_key=self.aws_secret_access_key
        )
        
        self.__create_job_definition()
    
    def __create_job_definition(self):
        # https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/batch.html#Batch.Client.register_job_definition
        # https://docs.aws.amazon.com/batch/latest/APIReference/API_RegisterJobDefinition.html
        response = self.aws_batch.register_job_definition(
            jobDefinitionName=self.batch_id,
            type='container',
            containerProperties={
                'image': self.container,
                'vcpus': 4,
                'memory': self.memory_in_mb,  # MB
                'resourceRequirements': [
                    {
                        'value': '1',
                        'type': 'GPU'
                    },
                ],
            },
            timeout={
                'attemptDurationSeconds': self.timeout_in_seconds
            }
        )
        
        self.job_definition_arn = response['jobDefinitionArn']
        
        print('Registered Job Definition: ' + self.batch_id)
    
    def __create_job_dir_name(self, job_position: int) -> str:
        return 'jobs/' + self.batch_id + '/' + str(job_position).zfill(6)
    
    def __deregister_job_definition(self):
        self.aws_batch.deregister_job_definition(
            jobDefinition=self.job_definition_arn
        )
        
        self.job_definition_arn = None
        
        print('Job definition deregistered.')
    
    def __get_unfinished_job_id_batches(self):
        batches = []
        id_array = list(self.unfinished_jobs)
        nr_of_unfinished_jobs = len(self.unfinished_jobs)
        nr_of_batches = math.ceil(nr_of_unfinished_jobs / self.batch_api_batch_size)
        
        for batch_nr in range(nr_of_batches):
            start = batch_nr * self.batch_api_batch_size
            end = start + self.batch_api_batch_size
            batch = id_array[start:end]
            batches.append(batch)
        
        return batches
    
    def __log_progress(self):
        nr_of_jobs = len(self.job_ids)
        nr_of_finished_jobs = nr_of_jobs - len(self.unfinished_jobs)
        
        print('Jobs finished: ' + str(nr_of_finished_jobs) + '/' + str(nr_of_jobs))
    
    def __on_job_finished(self, job_id: str):
        self.unfinished_jobs.remove(job_id)
        
        if self.callbacks_by_job_id[job_id] is not None:
            self.callbacks_by_job_id[job_id]()
    
    def get_all_outputs(self) -> []:
        """
        Fetches output of all jobs from S3.
        
        :returns: List of job outputs as JSON string.
        :rtype: list
        """
        
        outputs = []
        
        for job_id in self.job_ids:
            output = None
            
            try:
                output = self.get_output(job_id)
            except:
                print('Unable to get output for job ' + job_id)
            
            outputs.append(output)
        
        return outputs
    
    def get_batch_id(self) -> str:
        """
        Returns the batch id for this JobSubmitter instance.
        It is used in the S3 prefix for job data and for the job definition name.

        :returns: id of the job batch
        :rtype: str
        """
        
        return self.batch_id
    
    def get_job_directory(self, job_id: str) -> str:
        """
        Returns the S3 prefix for the data of a job.

        :param job_id: the job id
        :type job_id: str
        :returns: S3 prefix for the job data
        :rtype: str
        """
        
        return self.job_dirs_by_job_id[job_id]
    
    def get_output(self, job_id: str) -> str:
        """
        Fetches output of a job from S3.

        :param job_id: the job id
        :type job_id: str
        :returns: job output as JSON string
        :rtype: str
        """
        
        output_config_object_key = self.output_object_keys_by_job_id[job_id]
        
        return self.aws_s3.get_object(
            Bucket=self.job_bucket,
            Key=output_config_object_key
        )['Body'].read().decode('utf-8')
    
    def submit_job(
            self,
            input_data: dict,
            depends_on_job_ids: List[str] = None,
            callback: Callable = None
    ) -> str:
        """
        Submits a job that will automatically be processed. Returns the ID of the created job.
        
        :param input_data:
            JSON serializable job configuration
            Can contain resource links to additional input data (e.g. serialized numpy data)
        :type input_data: dict
        :param depends_on_job_ids: optional
            List of ids of jobs that need to be finished before this job starts
        :type depends_on_job_ids: list
        :param callback: optional
            Function without parameters that will be called when the job has either succeeded or failed.
            Will only be triggered while wait_until_jobs_finished() is running.
            Is not guaranteed to be called in the actual finishing order of jobs.
        :type callback: List[str]
        :returns:
            The ID of the created job.
        :rtype: str
        """
        
        if self.job_definition_arn is None:
            self.__create_job_definition()
        
        # put job config to s3
        job_config_json = json.dumps(input_data)
        job_config_binary = bytes(job_config_json, 'utf-8')
        job_number = self.job_iterator
        self.job_iterator += 1
        job_prefix = self.__create_job_dir_name(job_number)
        
        job_config_s3_key = job_prefix + '/config.json'
        self.aws_s3.put_object(Body=job_config_binary, Bucket=self.job_bucket, Key=job_config_s3_key)
        print('Created input data: s3://' + self.job_bucket + '/' + job_config_s3_key)
        
        # define output file
        output_config_object_key = job_prefix + '/output.json'
        
        # prepare dependency config
        dependency_config = []
        
        if depends_on_job_ids is not None:
            for depends_on_job_id in depends_on_job_ids:
                dependency_config.append({
                    'jobId': depends_on_job_id,
                    'type': 'SEQUENTIAL'
                })
        
        submit_response = self.aws_batch.submit_job(
            jobName=self.batch_id,
            jobQueue=self.job_queue,
            jobDefinition=self.job_definition_arn,
            # https://docs.aws.amazon.com/batch/latest/userguide/job_definition_parameters.html#parameters
            parameters={},
            dependsOn=dependency_config,
            containerOverrides={
                'environment': [
                    {
                        'name': 'S3_JOB_BUCKET',
                        'value': self.job_bucket,
                    },
                    {
                        'name': 'S3_JOB_CONFIG_KEY',
                        'value': job_config_s3_key,
                    },
                    {
                        'name': 'S3_JOB_PREFIX',
                        'value': job_prefix,
                    },
                    {
                        'name': 'S3_OUTPUT_OJBECT_KEY',
                        'value': output_config_object_key,
                    },
                    {
                        'name': 'BATCH_ID',
                        'value': self.batch_id,
                    }
                ]
            },
            timeout={
                'attemptDurationSeconds': self.timeout_in_seconds
            }
        )
        
        job_id = submit_response["jobId"]
        
        self.job_ids.append(job_id)
        self.output_object_keys_by_job_id[job_id] = output_config_object_key
        self.job_states_by_job_id[job_id] = 'SUBMITTED'
        self.job_iterator_by_job_id[job_id] = job_number
        self.job_dirs_by_job_id[job_id] = job_prefix
        self.callbacks_by_job_id[job_id] = callback
        self.unfinished_jobs.add(job_id)
        # REFACTOR: clean dependency for those arrays
        
        print('Job ID: ' + job_id)
        
        return job_id
    
    def wait_until_jobs_finished(self):
        """
        Polls the status of all unfinished jobs until all are done.
        Prints progress to stdout.
        """
        
        print('Waiting for jobs to finish.')
        
        while len(self.unfinished_jobs) > 0:
            time.sleep(self.polling_interval_seconds)
            
            query_batches = self.__get_unfinished_job_id_batches()
            
            for query_batch in query_batches:
                time.sleep(self.request_throttling_seconds)
                
                jobs_info = self.aws_batch.describe_jobs(
                    jobs=query_batch  # up to 100
                )
                
                for job_info in jobs_info['jobs']:
                    job_id = job_info["jobId"]
                    status = job_info['status']
                    
                    self.job_states_by_job_id[job_id] = status
                    
                    if status == 'FAILED':
                        print('WARNING: Job ' + job_id + ' failed.')
                        self.__on_job_finished(job_id)
                    
                    if status == 'SUCCEEDED':
                        self.__on_job_finished(job_id)
            
            self.__log_progress()
        
        print('All jobs finished.')
        self.__deregister_job_definition()
