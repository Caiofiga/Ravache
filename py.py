import boto3.session

s3 = boto3.Session(profile_name="Ravache")
client = s3.client('s3')

print(client.upload_file("static\img\logo.png", "ravache", "logo.png"))