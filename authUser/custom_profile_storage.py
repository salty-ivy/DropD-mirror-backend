import environ
env = environ.Env()
environ.Env.read_env()

from storages.backends.s3boto3 import S3Boto3Storage
class MediaStorage(S3Boto3Storage):
	bucket_name = "dropd.staging.static"
	location = env('AWS_S3_MEDIA_FOLDER')