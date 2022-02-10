import boto3
import json
from custom_encoder import CustomEncoder
import logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

dynamodb_table_name = 'patients-management-cloud'
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(dynamodb_table_name)

get_method = 'GET'
post_method = 'POST'
patch_method = 'PUT'
delete_method = 'DELETE'
patients = '/patients'
patient = '/patient'


def lambda_handler(event, context):
    logger.info(event)
    httpMethod = event['httpMethod']
    path = event['path']
    # if httpMethod == get_method and path == patients:
    #     response = build_response(200)
    if httpMethod == get_method and path == patient:
        response = get_product(event['queryStringParameters']['id'])
    elif httpMethod == get_method and path == patients:
        response = get_products()
    elif httpMethod == post_method and path == patient:
        response = save_product(json.loads(event['body']))
    elif httpMethod == patch_method and path == patient:
        request_body = json.loads(event['body'])
        response = modify_product(
            request_body['id'], request_body['updateKey'], request_body['updateValue'])
    elif httpMethod == delete_method and path == patient:
        request_body = json.loads(event['body'])
        response = delete_product(request_body['id'])
    else:
        response = build_response(404, 'Not Found.')

    return response


def build_response(status_code, body=None):
    if body is not None:
        body = json.dumps(body, cls=CustomEncoder)

    response = {
        'statusCode': status_code,
        'headers': {
            "Access-Control-Allow-Origin": "*",
            "Content-Type": "application/json",
        },
        'body': body
    }
    return response


def get_product(id):
    try:
        response = table.get_item(
            Key={
                'id': id
            }
        )
        if 'Item' in response:
            return build_response(200, response['Item'])
        else:
            return build_response(404, f'id {id} not found.')

    except:
        logger.exception('Something went wrong')


def get_products():
    try:
        response = table.scan()
        result = response['Items']

        while 'LastValuatedKey' in response:
            response = table.scan(
                ExclusiveStartKey=response['LastValuatedKey'])
            result.extend(response['Items'])

        body = result
        return build_response(200, body)
    except:
        logger.exception('Something went wrong')


def save_product(request_body):

    table.put_item(Item=request_body)
    body = {
        'Operation': 'SAVE',
        'Message': 'SUCCESS',
        'Item': request_body
    }
    return build_response(201, body)


def modify_product(id, updateKey, updateValue):
    try:
        response = table.update_item(
            Key={
                'id': id,
            },
            UpdateExpression='set %s = :v' % updateKey,
            ExpressionAttributeValues={
                ':v': updateValue
            },
            ReturnValues='UPDATED_NEW'
        )

        body = {
            'Operation': 'UPDATE',
            'Message': 'SUCCESS',
            'Item': response
        }

        return build_response(200, body)

    except:
        logger.exception('Something went wrong')


def delete_product(id):
    try:
        response = table.delete_item(Key={
            'id': id
        },
            ReturnValues='ALL_OLD')

        body = {
            'Operation': 'DELETE',
            'Message': 'SUCCESS',
            'deletedItem': response
        }
        return build_response(200, body)
    except:
        logger.exception('Something went wrong')
