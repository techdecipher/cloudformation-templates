#!/usr/bin/python3.9
import boto3
import os
import datetime
import pytz

BUCKET_NAME = 'my-logs-8853'
S3_FOLDER = 'httpd-logs/'
LOG_FILE_PATH = '/var/log/httpd/access_log'
SNS_TOPIC_ARN = 'arn:aws:sns:us-east-1:495599762731:My-SNS-for-logs'
REGION_NAME = 'us-east-1'

s3 = boto3.client('s3')
sns = boto3.client('sns', region_name=REGION_NAME)

def upload_logs():
    if os.path.exists(LOG_FILE_PATH):
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        s3_file_name = f"{S3_FOLDER}error_log_{timestamp}.log"
        s3.upload_file(LOG_FILE_PATH, BUCKET_NAME, s3_file_name)
        print(f"Uploaded {LOG_FILE_PATH} to s3://{BUCKET_NAME}/{s3_file_name}")
    else:
        print(f"Log file {LOG_FILE_PATH} does not exist.")

def delete_old_logs():
    utc = pytz.UTC
    cutoff_date = utc.localize(datetime.datetime.now() - datetime.timedelta(days=7))
    response = s3.list_objects_v2(Bucket=BUCKET_NAME, Prefix=S3_FOLDER)
    deleted_files = []

    if 'Contents' in response:
        for objects in response['Contents']:
            last_modified = objects['LastModified']
        
            if last_modified < cutoff_date:
                s3.delete_object(Bucket=BUCKET_NAME, Key=objects['Key'])
                deleted_files.append(objects['Key'])
                print(f"Deleted: {objects['Key']}")
                print("Past 7 days logs are deleted")
    else:
        print("No logs found in the S3 bucket.")

    if deleted_files:
        send_sns_notification(deleted_files)
    else:
        print("No logs were deleted.")

def send_sns_notification(deleted_files):
    message = f"The following logs have been deleted:\n" + "\n".join(deleted_files)
    sns_response =  sns.publish(
        TopicArn=SNS_TOPIC_ARN,
        Message=message,
        Subject='Log Deletion Notification'
    )
    print(f"SNS notification sent.{sns_response}")

upload_logs()
delete_old_logs()
