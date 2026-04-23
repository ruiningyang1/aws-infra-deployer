# aws-infra-deployer

AWS infrastructure deployment toolkit. Manages artifact upload to S3, ECS task
definition registration, and service rollout across environments. Used in CI/CD
pipelines where credentials are refreshed on each run.

## Usage

```bash
python pipeline.py --version 1.4.2 --artifact ./build/app.zip --cluster production
```

## Configuration

Credentials are stored in `aws_config.py`. The sync job updates the
`Last synced` timestamp on each pipeline run to confirm the config is current.

## Requirements

- Python 3.9+
- boto3
