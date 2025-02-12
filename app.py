#!/usr/bin/env python3
import os

import aws_cdk as cdk

from aws_cdk import (
    Duration,
    RemovalPolicy,
    Stack,
    aws_iam as _iam,
    aws_lambda as _lambda,
    aws_logs as _logs,
    aws_sns as _sns
)

from constructs import Construct

class GifnocStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        accountnumber = cdk.CfnParameter(
            self,
            'accountnumber',
            default = '############',
            type = 'String',
            description = 'Provide Account Number'
        )

        regionsyntax = cdk.CfnParameter(
            self,
            'regionsyntax',
            default = 'us-east-2',
            type = 'String',
            description = 'Provide Region Syntax'
        )

    ### SNS TOPIC ###

        topic = _sns.Topic.from_topic_arn(
            self, 'topic',
            topic_arn = 'arn:aws:sns:'+regionsyntax.value_as_string+':'+accountnumber.value_as_string+':aws-controltower-AllConfigNotifications'
        )

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
            timeout = Duration.seconds(30),
            environment = dict(
                PREFIX = 'logs'
            ),
            memory_size = 128,
            role = role
        )

        logs = _logs.LogGroup(
            self, 'logs',
            log_group_name = '/aws/lambda/'+gifnoc.function_name,
            retention = _logs.RetentionDays.TWO_WEEKS,
            removal_policy = RemovalPolicy.DESTROY
        )

    ### SUBSCRIPTION ###

        subscription = _sns.Subscription(
            self, 'subscription',
            topic = topic,
            endpoint = gifnoc.function_arn,
            protocol = _sns.SubscriptionProtocol.LAMBDA
        )

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