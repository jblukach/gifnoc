import boto3
import gzip
import json
import os

def handler(event, context):

    s3 = boto3.client('s3')

    for records in event['Records']:
        j = json.loads(records['body'])
        for record in j['Records']:
            print(record['s3']['object']['key'])

            if 'ConfigHistory' in record['s3']['object']['key']:
                s3.download_file(os.environ['INPUT'], record['s3']['object']['key'], '/tmp/temp.json.gz')
                with gzip.open('/tmp/temp.json.gz', 'rb') as f:
                    content = f.read().decode('utf-8')
                f.close()
                with gzip.open('/tmp/hold.json.gz', 'wb') as g:
                    j = json.loads(content)
                    for item in j['configurationItems']:
                        temp = {}
                        temp['fileVersion'] = j['fileVersion']
                        temp['configurationItem'] = item
                        g.write((str(temp)+str('\n')).encode())
                g.close()
                s3.upload_file('/tmp/hold.json.gz', os.environ['OUTPUT'], record['s3']['object']['key'])

            if 'ConfigSnapshot' in record['s3']['object']['key']:
                s3.download_file(os.environ['INPUT'], record['s3']['object']['key'], '/tmp/temp.json.gz')
                with gzip.open('/tmp/temp.json.gz', 'rb') as f:
                    content = f.read().decode('utf-8')
                f.close()
                with gzip.open('/tmp/hold.json.gz', 'wb') as g:
                    j = json.loads(content)
                    for item in j['configurationItems']:
                        temp = {}
                        temp['fileVersion'] = j['fileVersion']
                        temp['configSnapshotId'] = j['configSnapshotId']
                        temp['configurationItem'] = item
                        g.write((str(temp)+str('\n')).encode())
                g.close()
                s3.upload_file('/tmp/hold.json.gz', os.environ['OUTPUT'], record['s3']['object']['key'])

    return {
        'statusCode': 200,
        'body': json.dumps('Shipped!')
    }