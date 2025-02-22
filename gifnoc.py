import json

def handler(event, context):

    #for records in event['Records']:
    #    j = json.loads(records['body'])
    #    for record in j['Records']:
    #        print(record['s3']['object']['key'])

    return {
        'statusCode': 200,
        'body': json.dumps('Shipped: ')
    }