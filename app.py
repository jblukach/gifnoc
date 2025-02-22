#!/usr/bin/env python3
import os

import aws_cdk as cdk

from aws_cdk import (
    Duration,
    RemovalPolicy,
    Stack,
    aws_iam as _iam,
    aws_lambda as _lambda,
    aws_lambda_event_sources as _eventsource,
    aws_logs as _logs,
    aws_s3 as _s3,
    aws_s3_notifications as _notifications,
    aws_sqs as _sqs
)

from constructs import Construct

class GifnocStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        inputbucketname = cdk.CfnParameter(
            self,
            'inputbucketname',
            default = '<input>',
            type = 'String',
            description = 'Input Bucket Name'
        )

        outputbucketname = cdk.CfnParameter(
            self,
            'ouputbucketname',
            default = '<output>',
            type = 'String',
            description = 'Output Bucket Name'
        )

    ### S3 BUCKETS ###

        inputbucket = _s3.Bucket.from_bucket_name(
            self, 'inputbucket',
            bucket_name = inputbucketname.value_as_string
        )

        outputbucket = _s3.Bucket.from_bucket_name(
            self, 'outputbucket',
            bucket_name = outputbucketname.value_as_string
        )

    ### SQS QUEUE ###

        queue = _sqs.Queue(
            self, 'queue',
            visibility_timeout = Duration.seconds(900)
        )

    ### RESOURCE POLICY ###

        resource = _iam.PolicyStatement(
            actions = [
                'sqs:SendMessage'
            ],
            resources = [
                queue.queue_arn
            ],
            effect = _iam.Effect.ALLOW,
            principals = [
                _iam.ServicePrincipal('s3.amazonaws.com')
            ],
            conditions = {
                'ArnLike': {
                    'aws:SourceArn': inputbucket.bucket_arn
                }
            }
        )

        queue.add_to_resource_policy(resource)

    ### S3 NOTIFICATION ###

        #inputbucket.add_event_notification(
        #    _s3.EventType.OBJECT_CREATED,
        #    _notifications.SqsDestination(queue)
        #)

    ### IAM ROLE ###

        role = _iam.Role(
            self, 'role', 
            assumed_by = _iam.ServicePrincipal(
                'lambda.amazonaws.com'
            )
        )

        role.add_managed_policy(
            _iam.ManagedPolicy.from_aws_managed_policy_name(
                'service-role/AWSLambdaBasicExecutionRole'
            )
        )

        role.add_to_policy(
            _iam.PolicyStatement(
                actions = [
                    's3:GetObject'
                ],
                resources = [
                    inputbucket.arn_for_objects('*')
                ]
            )
        )

        role.add_to_policy(
            _iam.PolicyStatement(
                actions = [
                    's3:PutObject'
                ],
                resources = [
                    outputbucket.arn_for_objects('*')
                ]
            )
        )

    ### LAMBDA FUNCTION ####

        with open('gifnoc.py', encoding="utf8") as f:
            code = f.read()
        f.close()

        gifnoc = _lambda.Function(
            self, 'gifnoc',
            handler = 'index.handler',
            code = _lambda.InlineCode(code),
            runtime = _lambda.Runtime.PYTHON_3_13,
            architecture = _lambda.Architecture.ARM_64,
            timeout = Duration.seconds(900),
            environment = dict(
                INPUT = inputbucket.bucket_name,
                OUTPUT = outputbucket.bucket_name
            ),
            memory_size = 512,
            role = role
        )

        logs = _logs.LogGroup(
            self, 'logs',
            log_group_name = '/aws/lambda/'+gifnoc.function_name,
            retention = _logs.RetentionDays.TWO_WEEKS,
            removal_policy = RemovalPolicy.DESTROY
        )

    ### LAMBDA EVENT SOURCE ###

        #gifnoc.add_event_source(
        #    _eventsource.SqsEventSource(queue)
        #)

### GIFNOC APPLICATION ###

app = cdk.App()

GifnocStack(
    app, 'GifnocStack',
    env = cdk.Environment(
        account = os.getenv('CDK_DEFAULT_ACCOUNT'),
        region = os.getenv('CDK_DEFAULT_REGION')
    ),
    synthesizer = cdk.DefaultStackSynthesizer(
        qualifier = '4n6ir'
    )
)

cdk.Tags.of(app).add('GitHub','https://github.com/jblukach/gifnoc')

app.synth()