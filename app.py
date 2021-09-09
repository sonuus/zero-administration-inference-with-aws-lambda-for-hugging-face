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
    aws_autoscaling as autoscaling
)


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

        base_api = api_gw.RestApi(self, 'ApiGatewayWithCors',
                                  rest_api_name='ApiGatewayWithCors')
        example_entity = base_api.root.add_resource(
            'example',
            default_cors_preflight_options=api_gw.CorsOptions(
                allow_methods=['GET', 'OPTIONS', 'POST'],
                allow_origins=api_gw.Cors.ALL_ORIGINS)
        )

        # %%
        # iterates through the Python files in the docker directory
        docker_folder = os.path.dirname(
            os.path.realpath(__file__)) + "/inference"
        pathlist = Path(docker_folder).rglob('*.py')
        counter=1
        for path in pathlist:
            base = os.path.basename(path)
            filename = os.path.splitext(base)[0]
            # Lambda Function from docker image
            function = lambda_.DockerImageFunction(
                self, filename,
                code=lambda_.DockerImageCode.from_image_asset(docker_folder,
                                                              cmd=[
                                                                  filename+".handler"]
                                                              ),
                memory_size=8096,
                timeout=cdk.Duration.seconds(600),
                vpc=vpc,
                filesystem=lambda_.FileSystem.from_efs_access_point(
                    access_point, '/mnt/hf_models_cache'),
                environment={
                    "TRANSFORMERS_CACHE": "/mnt/hf_models_cache"}
            )
<<<<<<< HEAD

            # function.current_version.add_alias(
            #     "live", provisioned_concurrent_executions=2)
            # version = function.add_version("1", "", f"integ-test")

            alais = lambda_.Alias(self, "Alias", provisioned_concurrent_executions=2,
                                    alias_name='live', version=function.current_version)
            as_ = alais.add_auto_scaling(max_capacity=5)
            as_.scale_on_utilization(utilization_target=0.5)
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

            # adds method for the function
            # lambda_integration = api_gw.LambdaIntegration(function, proxy=False, integration_responses=[
            #     api_gw.IntegrationResponse(status_code='200',
            #                                response_parameters={
            #                                    'method.response.header.Access-Control-Allow-Origin': "'*'"
            #                                })
            # ])

            break

=======
            
            lambda_.Alias(self, f"Alias{counter}",
                     alias_name="prod",
                     version=function.latest_version,
                     provisioned_concurrent_executions=2
                    )
            
           

            # adds method for the function
            lambda_integration = api_gw.LambdaIntegration(function, proxy=False, integration_responses=[
                api_gw.IntegrationResponse(status_code='200',
                                           response_parameters={
                                               'method.response.header.Access-Control-Allow-Origin': "'*'"
                                           })
            ])
            
            counter=counter +1 
>>>>>>> 5a60060b7754185100c1219817723b00f5c931e3

app = cdk.App()

ServerlessHuggingFaceStack(app, "ServerlessHuggingFaceStack")

app.synth()
# %%
