"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: MIT-0
"""

import os
from pathlib import Path
from aws_cdk import (
    aws_lambda as lambda_,
    aws_apigateway as api_gw,
    aws_efs as efs,
    aws_ec2 as ec2,
    core as cdk,
    aws_autoscaling as autoscaling,
    aws_sqs as sqs,
    aws_iam as iam,
)
from aws_cdk.aws_lambda_event_sources import SqsEventSource


class ServerlessHuggingFaceStack(cdk.Stack):
    def __init__(self, scope: cdk.Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        # EFS needs to be setup in a VPC
        vpc = ec2.Vpc(self, 'Vpc', max_azs=2)

        # creates a file system in EFS to store cache models
        fs = efs.FileSystem(self, 'FileSystem',
                            vpc=vpc,
                            removal_policy=cdk.RemovalPolicy.DESTROY)
        access_point = fs.add_access_point('MLAccessPoint',
                                           create_acl=efs.Acl(
                                               owner_gid='1001', owner_uid='1001', permissions='750'),
                                           path="/export/models",
                                           posix_user=efs.PosixUser(gid="1001", uid="1001"))
        #Base API
        base_api = api_gw.RestApi(self, 'ApiGatewayWithCors',
                                  rest_api_name='ApiGatewayWithCors')

        example_entity = base_api.root.add_resource(
            'example',
            default_cors_preflight_options=api_gw.CorsOptions(
                allow_methods=['GET', 'OPTIONS', 'POST'],
                allow_origins=api_gw.Cors.ALL_ORIGINS)
        )

        # Lambda Function from docker image
        function = lambda_.DockerImageFunction(
            self,'sentiment.py' ,
            code=lambda_.DockerImageCode.from_image_asset('inference', cmd=["sentiment.handler"]),
            memory_size=8096,
            timeout=cdk.Duration.seconds(600),
            vpc=vpc,
            tracing=lambda_.Tracing.ACTIVE,
            filesystem=lambda_.FileSystem.from_efs_access_point(
                access_point, '/mnt/hf_models_cache'),
            environment={
                "TRANSFORMERS_CACHE": "/mnt/hf_models_cache"}
        )


        alais = lambda_.Alias(self, "Alias",
                                    provisioned_concurrent_executions=1,
                                    alias_name='live',
                                    version=function.current_version)


        as_ = alais.add_auto_scaling(max_capacity=10,min_capacity=1)

        as_.scale_on_utilization(utilization_target=0.4)

        # as_.scale_on_schedule("ScaleUpInTheMorning", schedule=autoscaling.Schedule.cron(
        #     hour="8", minute="0"), min_capacity=2)

        example_entity_lambda_integration = api_gw.LambdaIntegration(
            alais,
            proxy=False,
            integration_responses=[{
                        'statusCode': '200',
                        'responseParameters': {
                            'method.response.header.Access-Control-Allow-Origin': "'*'",
                        }
                    }]
                )

        example_entity.add_method(
            'ANY', example_entity_lambda_integration,
            method_responses=[{
                'statusCode': '200',
                'responseParameters': {
                    'method.response.header.Access-Control-Allow-Origin': True,
                }
            }]
        )

        # SQS
        order_queue=sqs.Queue(self,"orderQueue",visibility_timeout=cdk.Duration.seconds(70))

        post_order_function = lambda_.Function(
            self,'testConncurrent' ,
            code=lambda_.Code.asset('./order_post'),
            handler='app.handler',
            runtime=lambda_.Runtime.PYTHON_3_7,
            timeout=cdk.Duration.seconds(600),
            tracing=lambda_.Tracing.ACTIVE,
            environment={
                "ORDER_QUEUE_NAME": order_queue.queue_name}
        )

        post_order_function.add_to_role_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "sqs:SendMessage",
                ],
                resources=[order_queue.queue_arn],
            )
        )
        alais2 = lambda_.Alias(self, "Function2Alias",
                                    provisioned_concurrent_executions=1,
                                    alias_name='live',
                                    version=post_order_function.current_version)



        as_ = alais2.add_auto_scaling(max_capacity=5,min_capacity=1)

        as_.scale_on_utilization(utilization_target=0.2)

        example_entity2 = base_api.root.add_resource(
            'order',
            default_cors_preflight_options=api_gw.CorsOptions(
                allow_methods=['OPTIONS', 'POST'],
                allow_origins=api_gw.Cors.ALL_ORIGINS)
        )

        example_entity_lambda_integration2 = api_gw.LambdaIntegration(
            alais2,
            proxy=False,
            integration_responses=[{
                        'statusCode': '200',
                        'responseParameters': {
                            'method.response.header.Access-Control-Allow-Origin': "'*'",
                        }
                    }]
                )

        example_entity2.add_method(
            'ANY', example_entity_lambda_integration2,
            method_responses=[{
                'statusCode': '200',
                'responseParameters': {
                    'method.response.header.Access-Control-Allow-Origin': True,
                }
            }]
        )

        process_order_function = lambda_.Function(
            self,'processOrder' ,
            code=lambda_.Code.asset('./order_process'),
            handler='app.handler',
            runtime=lambda_.Runtime.PYTHON_3_7,
            timeout=cdk.Duration.seconds(60),
            tracing=lambda_.Tracing.ACTIVE
        )
        process_order_function.add_event_source(SqsEventSource(order_queue,
            batch_size=2,
            max_batching_window=cdk.Duration.seconds(5)
        ))



app = cdk.App()

ServerlessHuggingFaceStack(app, "ServerlessHuggingFaceStack")

app.synth()
# %%
