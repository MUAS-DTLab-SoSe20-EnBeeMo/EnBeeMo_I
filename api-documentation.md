<a name="PCR"></a>
# PCR

<a name="PCR.JobSubmitter"></a>
# PCR.JobSubmitter

<a name="PCR.JobSubmitter.JobSubmitter"></a>
## JobSubmitter Objects

```python
class JobSubmitter()
```

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

<a name="PCR.JobSubmitter.JobSubmitter.__init__"></a>
#### \_\_init\_\_

```python
 | __init__(batch_name: str, job_queue: str, container: str, job_bucket: str, memory_in_mb: int = 1024, aws_region: str = None, aws_access_key_id: str = None, aws_secret_access_key: str = None, timeout_in_hours: int = 20, polling_interval_seconds: int = 60, request_throttling_milliseconds: int = 200)
```

**Arguments**:

- `batch_name`: 
Human readable name of the set of jobs.
The name is used for job folder paths in S3.
The first character must be alphanumeric.
Up to 90 letters.
Numbers, hyphens, and underscores are allowed.
- `container`: 
Location of the docker container to use for this batch.
- `job_bucket`: 
S3 bucket name to use for persisting in- and output data.
- `memory_in_mb`: 
Memory for the docker container.
- `aws_access_key_id`: optional
AWS CLI access key.
- `aws_secret_access_key`: optional
AWS CLI secret key.
- `aws_region`: 
AWS region, has to match the region of the job queue.
- `job_queue`: 
Name of the job queue to submit jobs to.

<a name="PCR.JobSubmitter.JobSubmitter.get_all_outputs"></a>
#### get\_all\_outputs

```python
 | get_all_outputs() -> []
```

Fetches output of all jobs from S3.

**Returns**:

List of job outputs as JSON string.
:rtype: list

<a name="PCR.JobSubmitter.JobSubmitter.get_batch_id"></a>
#### get\_batch\_id

```python
 | get_batch_id() -> str
```

Returns the batch id for this JobSubmitter instance.
It is used in the S3 prefix for job data and for the job definition name.

**Returns**:

id of the job batch
:rtype: str

<a name="PCR.JobSubmitter.JobSubmitter.get_job_directory"></a>
#### get\_job\_directory

```python
 | get_job_directory(job_id: str) -> str
```

Returns the S3 prefix for the data of a job.

**Arguments**:

- `job_id`: the job id
:type job_id: str

**Returns**:

S3 prefix for the job data
:rtype: str

<a name="PCR.JobSubmitter.JobSubmitter.get_output"></a>
#### get\_output

```python
 | get_output(job_id: str) -> str
```

Fetches output of a job from S3.

**Arguments**:

- `job_id`: the job id
:type job_id: str

**Returns**:

job output as JSON string
:rtype: str

<a name="PCR.JobSubmitter.JobSubmitter.submit_job"></a>
#### submit\_job

```python
 | submit_job(input_data: dict, depends_on_job_ids: List[str] = None, callback: Callable = None) -> str
```

Submits a job that will automatically be processed. Returns the ID of the created job.

**Arguments**:

- `input_data`: 
JSON serializable job configuration
Can contain resource links to additional input data (e.g. serialized numpy data)
:type input_data: dict
- `depends_on_job_ids`: optional
List of ids of jobs that need to be finished before this job starts
:type depends_on_job_ids: list
- `callback`: optional
Function without parameters that will be called when the job has either succeeded or failed.
Will only be triggered while wait_until_jobs_finished() is running.
Is not guaranteed to be called in the actual finishing order of jobs.
:type callback: List[str]

**Returns**:


The ID of the created job.
:rtype: str

<a name="PCR.JobSubmitter.JobSubmitter.wait_until_jobs_finished"></a>
#### wait\_until\_jobs\_finished

```python
 | wait_until_jobs_finished()
```

Polls the status of all unfinished jobs until all are done.
Prints progress to stdout.

