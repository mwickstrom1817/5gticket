import boto3
import streamlit as st
import uuid
from datetime import datetime


def get_r2_client():
    """Return a boto3 S3 client pointed at Cloudflare R2."""
    return boto3.client(
        "s3",
        endpoint_url=st.secrets["R2_ENDPOINT_URL"],           # https://<account_id>.r2.cloudflarestorage.com
        aws_access_key_id=st.secrets["R2_ACCESS_KEY_ID"],
        aws_secret_access_key=st.secrets["R2_SECRET_ACCESS_KEY"],
        region_name="auto"
    )


def upload_ticket_photo(file_bytes: bytes, content_type: str, customer_id: int) -> str:
    """
    Upload a ticket photo to R2.
    Returns the public URL of the uploaded object.
    """
    client = get_r2_client()
    bucket = st.secrets["R2_BUCKET_NAME"]

    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    unique_id = str(uuid.uuid4())[:8]
    key = f"tickets/customer_{customer_id}/{timestamp}_{unique_id}.jpg"

    client.put_object(
        Bucket=bucket,
        Key=key,
        Body=file_bytes,
        ContentType=content_type
    )

    # Build public URL (requires R2 bucket to have public access or custom domain)
    public_base = st.secrets.get("R2_PUBLIC_URL", "").rstrip("/")
    if public_base:
        return f"{public_base}/{key}"

    # Fallback: presigned URL (72 hours)
    url = client.generate_presigned_url(
        "get_object",
        Params={"Bucket": bucket, "Key": key},
        ExpiresIn=259200
    )
    return url


def delete_object(key: str):
    """Delete an object from R2 by key."""
    client = get_r2_client()
    bucket = st.secrets["R2_BUCKET_NAME"]
    client.delete_object(Bucket=bucket, Key=key)
