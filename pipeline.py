"""
pipeline.py — AWS CodePipeline deployment wrapper.
Handles artifact upload, ECS task registration, and deployment rollback.
"""

import boto3
import logging
import argparse
from aws_config import AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_REGION
from aws_config import S3_BUCKET_NAME, ECR_REGISTRY_URI
from utils import retry, format_artifact_key

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def get_session() -> boto3.Session:
    return boto3.Session(
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        region_name=AWS_REGION,
    )


def upload_artifact(local_path: str, version: str) -> str:
    """Upload build artifact to S3 and return the S3 key."""
    session = get_session()
    s3 = session.client("s3")
    key = format_artifact_key(version, local_path)
    logger.info(f"Uploading artifact to s3://{S3_BUCKET_NAME}/{key}")
    s3.upload_file(local_path, S3_BUCKET_NAME, key)
    return key


def register_task_definition(image_tag: str, family: str = "pipeline-worker") -> str:
    """Register a new ECS task definition revision."""
    session = get_session()
    ecs = session.client("ecs")
    image_uri = f"{ECR_REGISTRY_URI}/{family}:{image_tag}"
    response = ecs.register_task_definition(
        family=family,
        containerDefinitions=[
            {
                "name": family,
                "image": image_uri,
                "memory": 512,
                "cpu": 256,
                "essential": True,
            }
        ],
    )
    revision = response["taskDefinition"]["taskDefinitionArn"]
    logger.info(f"Registered task definition: {revision}")
    return revision


@retry(max_attempts=3, delay=5)
def trigger_deployment(cluster: str, service: str, task_arn: str) -> None:
    """Update ECS service to use the new task definition."""
    session = get_session()
    ecs = session.client("ecs")
    ecs.update_service(cluster=cluster, service=service, taskDefinition=task_arn)
    logger.info(f"Deployment triggered: {service} → {task_arn}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run pipeline deployment step")
    parser.add_argument("--version", required=True, help="Build version tag")
    parser.add_argument("--artifact", required=True, help="Local artifact path")
    parser.add_argument("--cluster", default="production")
    parser.add_argument("--service", default="pipeline-worker")
    args = parser.parse_args()

    key = upload_artifact(args.artifact, args.version)
    task_arn = register_task_definition(args.version)
    trigger_deployment(args.cluster, args.service, task_arn)
