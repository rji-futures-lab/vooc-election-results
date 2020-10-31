# vooc-election-results

Pipeline infrastructure for live 2020 general election results for the [Voice of Orange County](https://github.com/rji-futures-lab/vooc-election-results.git).

## Proposed pipeline plan

1. **Fetch** the results

    a. From each County Registrar of Voters
    b. From each relevant endpoint of the Secretary of States API

2. **Compare** the new results to the previous results.

    a. If different, **store** a "latest" copy and a datetime-stamped copy.

3. **Parse** out results for individual contests

    a. *Every* contest in OC
    b. Just the contests with supplementary results for OC contests
    c. The SoS results are already parsed out.

4. **Compare** and **store** parsed results

5. **Compile** final json for each contest with new parsed results

    a. For the vast majority of the OC contests, we will simply update the datetime stamp and the vote counts
    b. For contests, we will combine vote counts as well.


## Bootstrapping

To set up your local dev environment, you need to install both sets of requirements:

```sh
pip install -r requirements.txt
```

```sh
pip install -r requirements-dev.txt
```

You'll also need to set a few environment variables. For this, I'm using [direnv](https://direnv.net/).

## Deploying

Here's the stack:

- Code is is hosted in an [AWS Lambda](https://aws.amazon.com/lambda/) function.
- Data and cached HTML are stored in an [AWS S3](https://aws.amazon.com/s3/) bucket.
- Scheduling is handled via [AWS EventBridge](https://aws.amazon.com/eventbridge/).

To deploy:

```sh
source deploy.sh
```

Which will:

- Make the bucket (if it doesn't already exist)
- Set the bucket's [CORS](https://docs.aws.amazon.com/AmazonS3/latest/dev/cors.html) policy (necessary to load the data in [Observable](https://observablehq.com/))
- Package the source code 
- Create the lambda function
- Set the environment variables in the lambda function
- Schedule the frequency of function calls

## Managing the deployment

To update the deployment:

```sh
source update.sh
```

Note that:

- New files that need to be in the deployment should be specified in [`package.sh`](package.sh)
- New environment variables that need to be set in the lambda function should be specified in [`set-env-vars.sh`](set-env-vars.sh)

If your update fails, you might try tearing down the entire deployment (except the S3 bucket):

```sh
source teardown.sh
```

And then re-deploying:

```sh
source deploy.sh
```

Updates will also reset the function call frequency. If you just need to modify the schedule, then:

```sh
source schedule.sh
```
