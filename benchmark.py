import subprocess
import time
import argparse
import json
import yaml
from datetime import datetime
from pathlib import Path
import importlib.util
import statistics

"""
New Todo:
Measure in complexity of software engineering, code complexity, etc... code maintainability, code usability...
Other possible solutions, software engineering domain specific implementations, maybe code scanner etc...

Generate a yaml config file for cloudformation instead of hardcoding it, this enables count for cloudformation

Scenario complexity: Breadth vs Depth - Depth is count
breadth - multiple resources in one deployment
couple of scenarios that represent certain workload (microservice benchmarks, cloud benchmarks, etc...) 
source the complex scenario from somewhere, eg.. this is a common server deployment structure, or commonly used web server deployment structure

evaluation: depth individual resource multiple deployments(4-6, graph it with counts), breadth complex scenarios(contrast to baseline scenarios, simplified version of the same, 2-3)
, usability (code complexity)
"""

with open('config.yaml') as file:
    config = yaml.safe_load(file)

parser = argparse.ArgumentParser(description = "Program description to put")
parser.add_argument('-v', '--verbose', action='store_true', help = 'Show detailed verbose output')
parser.add_argument('-s', '--scenario', required = True, help = 'Select a scenario you want to test')
parser.add_argument('-t', '--tool', required = True, choices = ['terraform', 'boto3', 'cloudformation'], help = 'Select a IaC tool you want to use')
parser.add_argument('-c', '--count', type = int, default = 1, metavar = 'COUNT', help = 'Select a resource count to test, Default = 1')
parser.add_argument('-r', '--runs', type = int, default = None, help = 'Choose the amount of repeat deployment runs to make')
parser.add_argument('-i', '--interval', type = int, default = 0, help = 'Choose the amount of seconds each interval will take between repeats, Default = 0')
args = parser.parse_args()
scenario_name = args.scenario
tool_name = args.tool

def verbose_print(message):
    if args.verbose:
        print(message)

if scenario_name not in config['scenarios']:
    print(f"Error: Scenario '{scenario_name}' not found in scenarios list")
    print(f"Available scenarios: {config['scenarios']}")
    exit(1)

scenario_config = config['scenarios'][scenario_name]

if 'tools' in scenario_config and tool_name not in scenario_config['tools']:
    print(f"Error: Tool '{tool_name}'not found in tools list for this scenario")
    print(f"Available tools: {scenario_config['tools']}")
    exit(1)

if 'allowed_counts' in scenario_config:
    if args.count is None:
        print(f"Allowed counts for this scenario are: {scenario_config['allowed_counts']}")
        print(f"In order to run this test, pass a --count or -c argument with desired amount")
        exit(1)
    if args.count not in scenario_config['allowed_counts']:
        print("The desired resource count is not valid")
        print(f"Allowed counts for this scenario are: {scenario_config['allowed_counts']}")
        exit(1)

    print(f"Confirmed desired resource count: {args.count}")

if 'allowed_counts' not in scenario_config:
    if args.count is not None:
        print("Warning: This scenario does not support a resource count parameter")

if args.runs:
    if args.runs < 1:
        print("Error: Invalid run amount")
        exit(1)
    if args.interval < 1:
        print("Error: Invalid interval amount")
        exit(1)
    if args.count != 1:
        print("Warning: This interval mode is designed for single resource deployments") #ask about this

print(f"Running selected scenario '{scenario_config['description']}' using '{tool_name}'")

def get_working_dir(tool, scenario):
    if tool == 'terraform':
        return Path('scenarios') / 'terraform' / scenario
    elif tool == 'boto3':
        return Path('scenarios') / 'boto3' / scenario
    elif tool == 'cloudformation':
        return Path('scenarios') / 'cloudformation'
    else:
        print(f"Error: Invalid tool type")
        print(f"Available tools: {scenario_config['tools']}")
        exit(1)

def get_resource_count(outputs):
    resource_count = outputs.get("bucket_count", outputs.get("instance_count", len(outputs.get("bucket_names", outputs.get("instance_ids", [])))))
    return resource_count

def parse_tf_outputs(tf_output: str):
    outputs = {}
    found_outputs = False
    current_key = None
    accumulator = []

    for line in tf_output.split('\n'):
        if line.startswith("Outputs:"):
            found_outputs = True
            continue

        if found_outputs:
            if current_key is not None:
                if "]" in line:
                    outputs[current_key] = accumulator
                    current_key = None
                    accumulator = []
                else:
                    strip_line = line.strip(" ,\"")
                    if strip_line:
                        accumulator.append(strip_line)

            elif " = " in line:
                split_line = line.split("=", 1)
                name = split_line[0].strip()
                value = split_line[1].strip()

                if value.startswith("["):
                    if "]" in value:
                        outputs[name] = []
                    else:
                        current_key = name
                        accumulator = []
                else:
                    stripped_value = value.strip(" \"")
                    outputs[name] = stripped_value 

    return outputs

def parse_cf_outputs(cf_output: str):
    key_mapping = {
        'BucketNames': 'bucket_names',
        'BucketCount': 'bucket_count',
        'BucketRegion': 'bucket_region',
        'InstanceIDs': 'instance_ids',
        'InstanceCount': 'instance_count',
        'InstancePublicIPs': 'instance_public_ips',
        'SecurityGroupId': 'security_group_id',
        'FeaturesEnabled': 'features_enabled'
    }

    data = json.loads(cf_output)
    outputs_list = data["Stacks"][0]["Outputs"]
    outputs = {}

    for output in outputs_list:
        key = output["OutputKey"]
        value = output["OutputValue"]
        outputs[key_mapping.get(key, key)] = value

    return outputs

def validate_outputs(outputs, scenario_name, config):
    if tool_name == 'cloudformation' and 'expected_outputs_cloudformation' in config['scenarios'][scenario_name]:
        expected_outputs = config['scenarios'][scenario_name]['expected_outputs_cloudformation']
    else:
        expected_outputs = config['scenarios'][scenario_name]['expected_outputs']

    validation_passed = False

    missing_outputs = []
    for output in expected_outputs: 
        if output not in outputs:
            missing_outputs.append(output)

    unexpected_outputs = []
    for output in outputs:
        if output not in expected_outputs:
            unexpected_outputs.append(output)

    if missing_outputs:
        print(missing_outputs)

    if unexpected_outputs:
        print(unexpected_outputs)

    if not missing_outputs:
        validation_passed = True
    
    return(validation_passed, missing_outputs, unexpected_outputs)

def verify_cleanup_success(destroy_output, expected_resource_count):
    if 'Destroy complete!' not in destroy_output:
        print("Caution: Destroy was not successful, check for dormant resources!")
        return False

    destroyed_count = destroy_output.count("Destruction complete")

    if abs(destroyed_count - expected_resource_count) <= 2:
        return (True, f"Success: Destroyed {destroyed_count} resources")
    elif destroyed_count > expected_resource_count:
        return (True, f"Warning: Destroyed {destroyed_count} resources, expected {expected_resource_count}!")
    else:
        return (False, f"Error: Destroyed {destroyed_count} resources, expected {expected_resource_count}!")
    
def run_interval_scenario(scenario_name, tool_type, count, runs, interval):
    run_results = []
    run_count = 1

    for i in range(1, runs + 1):
        print(f"Run number: {run_count}")

        (outputs, apply_time, destroy_time, validation_passed, missing, unexpected, 
        cleanup_verified, cleanup_message, init_time, total_operation_time) = run_scenario(tool_name, scenario_name, args.count)

        run_entry = {
            "run_number": run_count,
            "init_time": round(init_time, 2),
            "deploy_time": round(apply_time, 2),
            "destroy_time": round(destroy_time, 2),
            "total_time": round(total_operation_time, 2),
            "validation_passed": validation_passed,
            "cleanup_verified": cleanup_verified
        }

        run_count += 1

        run_results.append(run_entry)

        if i < runs + 1:
            print(f"Interval wait: {interval}")
            time.sleep(interval)

    if run_results:
        summary_statistics = {
            "avg_deploy_time": round(statistics.mean([run["deploy_time"] for run in run_results]), 2),
            "avg_destroy_time": round(statistics.mean([run["destroy_time"] for run in run_results]), 2),
            "avg_total_time": round(statistics.mean([run["total_time"] for run in run_results]), 2),
            "fastest_total_time": min(run_results, key=lambda x: x['total_time'])['total_time'],
            "slowest_total_time": max(run_results, key=lambda x: x['total_time'])['total_time'],
            "success_rate": (sum(1 for run in run_results if run["validation_passed"]) / len(run_results)) * 100
        }
    else:
        summary_statistics = {}

    return (run_results, summary_statistics)
    
def log_result(scenario, deploy_time, cleanup_time, total_operation_time, extra_info = None):
    timestamp = datetime.now()

    result = {
        "scenario": scenario,
        "tool": tool_name,
        "mode": 'non_interval',
        "timestamp": timestamp.isoformat(),
        "deploy_time": round(deploy_time, 2),
        "cleanup_time": round(cleanup_time, 2),
        "total_time": round(total_operation_time, 2),
        "date": timestamp.strftime("%Y-%m-%d"),
        "time": timestamp.strftime("%H:%M:%S")
    }

    if extra_info:
        result["metadata"] = extra_info

    Path("Test results/basic_mode").mkdir(exist_ok=True)

    resource_count = extra_info.get("resource_count", "unknown") if extra_info else "unknown"

    filename = f"Test results/basic_mode/{scenario}_{tool_name}_{resource_count}_resources_{result['date']}_{result['time'].replace(':', '-')}.json"
    with open(filename, 'w') as file:
        json.dump(result, file, indent = 2)
    
    return (result, f"Result logged in: {filename}")

def log_interval_result(scenario_name, runs, interval, run_results, summary_statistics):
    timestamp = datetime.now()

    interval_result = {
        "scenario": scenario_name,
        "tool": tool_name,
        "mode": 'interval',
        "date": timestamp.strftime("%Y-%m-%d"),
        "time": timestamp.strftime("%H:%M:%S"),
        "configuration": {
            "runs": runs,
            "interval": interval,
            "count": len(run_results)
        },
        "individual_runs": run_results,
        "summary": summary_statistics
    }

    Path("Test results/interval_mode").mkdir(exist_ok=True)
    filename = f"Test results/interval_mode/{scenario_name}_{tool_name}_{runs}_runs_{interval}_{interval}_{interval_result['date']}_{interval_result['time'].replace(':', '-')}.json"
    with open(filename, 'w') as file:
        json.dump(interval_result, file, indent = 2)

    return (interval_result, f"Result logged in: {filename}")

def generate_cf_template(scenario_name, count):
    if scenario_name in ['s3_basic', 's3_complex']:
        resources = {}
        for i in range(count):
            resources[f'S3Bucket{i}'] = {
                'Type': 'AWS::S3::Bucket',
                'Properties': {
                    'Tags': [
                        {'Key': 'Environment', 'Value': 'test'},
                        {'Key': 'Purpose', 'Value': 'benchmarking'},
                        {'Key': 'Index', 'Value': str(i)}
                    ]
                }
            }
            if scenario_name == 's3_complex':
                resources[f'S3Bucket{i}']['Properties']['VersioningConfiguration'] = {'Status': 'Enabled'}
                resources[f'S3Bucket{i}']['Properties']['BucketEncryption'] = {
                    'ServerSideEncryptionConfiguration': [{
                        'ServerSideEncryptionByDefault': {'SSEAlgorithm': 'AES256'}
                    }]
                }

        outputs = {
            'BucketCount': {'Value': str(count)},
            'BucketRegion': {'Value': {'Ref': 'AWS::Region'}}
        }

    elif scenario_name in ['ec2_basic', 'ec2_complex']:
        resources = {}
        if scenario_name == 'ec2_complex':
            resources['SecurityGroup'] = {
                'Type': 'AWS::EC2::SecurityGroup',
                'Properties': {
                    'GroupDescription': 'EC2 complex benchmarking security group',
                    'SecurityGroupIngress': [{
                        'IpProtocol': 'tcp',
                        'FromPort': 22,
                        'ToPort': 22,
                        'CidrIp': '10.0.0.0/8'
                    }]
                }
            }

        for i in range(count):
            instance = {
                'Type': 'AWS::EC2::Instance',
                'Properties': {
                    'InstanceType': 't3.micro',
                    'ImageId': '{{resolve:ssm:/aws/service/ami-amazon-linux-latest/amzn2-ami-hvm-x86_64-gp2}}',
                    'Tags': [
                        {'Key': 'Environment', 'Value': 'test'},
                        {'Key': 'Purpose', 'Value': 'benchmarking'},
                        {'Key': 'Index', 'Value': str(i)}
                    ]
                }
            }
            if scenario_name == 'ec2_complex':
                instance['Properties']['SecurityGroupIds'] = [{'Ref': 'SecurityGroup'}]
            resources[f'EC2Instance{i}'] = instance

        outputs = {
            'InstanceCount': {'Value': str(count)},
        }
        if scenario_name == 'ec2_complex':
            outputs['SecurityGroupId'] = {'Value': {'Ref': 'SecurityGroup'}}

    template = {
        'AWSTemplateFormatVersion': '2010-09-09',
        'Description': f'{scenario_name} benchmarking scenario - {count} resources',
        'Resources': resources,
        'Outputs': outputs
    }

    temp_path = Path(f'scenarios/cloudformation/temp_{scenario_name}_{count}.yaml')
    with open(temp_path, 'w') as f:
        yaml.dump(template, f, default_flow_style=False)

    return temp_path

def run_tf_scenario(scenario_name, count):
    working_directory = get_working_dir("terraform", scenario_name)
    print("Initializing Terraform...")
    init_start_time = time.time()

    tf_init = subprocess.run(['terraform', 'init', '-no-color'], 
                                   cwd = working_directory, capture_output = True, text = True)
    
    init_end_time = time.time()
    init_time = init_end_time - init_start_time

    if tf_init.returncode != 0:
        print("Terraform Initialization failed")
        print(tf_init.stderr)
        exit(1)
    else:
        print("Terraform successfully initialized")

    print("Applying Terraform configuration...")

    apply_start_time = time.time()
    tf_apply = subprocess.run(['terraform', 'apply', '-auto-approve', f'-var=resource_count={count}', '-no-color'],
                              capture_output = True, text = True, cwd = working_directory)
    
    apply_end_time = time.time()
    apply_time = apply_end_time - apply_start_time

    if tf_apply.returncode != 0:
        print("Terraform Apply failed.")
        print(tf_apply.stderr)
        exit(1)
    else:
        print(f"Selected resources applied successfully in {apply_time:.2f} seconds")
        verbose_print(tf_apply.stdout)

    outputs = parse_tf_outputs(tf_apply.stdout)
    validation_passed, missing_outputs, unexpected_outputs = validate_outputs(outputs, scenario_name, config)

    if args.verbose:
        if outputs:
            print("Created resources: ")
            for name, value in outputs.items():
                print(f" {name}: {value}")

    print(f"Deployed {get_resource_count(outputs)} resources successfully")
    print("Destroying Terraform configuration...")

    destroy_start_time = time.time()
    tf_destroy = subprocess.run(['terraform', 'destroy', '-auto-approve', f'-var=resource_count={count}', '-no-color'],
                                capture_output = True, text = True, cwd = working_directory)
    destroy_end_time = time.time()
    destroy_time = destroy_end_time - destroy_start_time
    total_operation_time = init_time + apply_time + destroy_time

    if tf_apply.returncode == 0 and tf_destroy.returncode != 0:
        print("Warning: Apply operation succeeded but Destroy operation failed!")
        print("Warning: Cleanup any remaining resources in AWS console manually!")
    
    if tf_destroy.returncode != 0:
        print(f"Error: Terraform destroy failed")
        print(tf_destroy.stderr)
        exit(1)
    else:
        print(f"Terraform Destroy successful in {destroy_time:.2f} seconds")
        verbose_print(tf_destroy.stdout)
        print(f"Destroyed {get_resource_count(outputs)} resources successfully")
        cleanup_verified, cleanup_message = verify_cleanup_success(tf_destroy.stdout, len(outputs))

        if not cleanup_verified:
            print("Warning: Cleanup verification failed, check for leftover resources!")
        else: 
            print("Cleanup verification successful")
    
    if args.verbose:
        print(tf_destroy.stdout)

    return (outputs, apply_time, destroy_time, validation_passed, missing_outputs, unexpected_outputs, 
            cleanup_verified, cleanup_message, init_time, total_operation_time)
    
def run_boto3_scenario(scenario_name, count):
    module_path = f"scenarios/boto3/{scenario_name}.py"
    spec = importlib.util.spec_from_file_location(scenario_name, module_path)
    scenario_module = importlib.util.module_from_spec(spec)

    try:
        spec.loader.exec_module(scenario_module)
    except FileNotFoundError:
        print(f"Boto3 scenario not found {module_path}.")
        exit(1)

    print("Deployment is starting...")
    deploy_start_time = time.time()

    try:
        outputs = scenario_module.deploy(count)
        deploy_end_time = time.time()
        apply_time = deploy_end_time - deploy_start_time

        if outputs is None:
            print("Error: Deployment failed or returned no outputs")
            exit(1)

        print(f"Resources deployed successfully in {apply_time:.2f} seconds")
        print(f"Deployed {get_resource_count(outputs)} resources successfully")

        validation_passed, missing_outputs, unexpected_outputs = validate_outputs(outputs, scenario_name, config)

        if args.verbose:
            if outputs:
                print("Created resouces:")
                for name, value in outputs.items():
                    print(f" {name}: {value}")

        print("Cleaning up resources...")
        destroy_start_time = time.time()

        cleanup_success = scenario_module.destroy(outputs, args.verbose)
        destroy_end_time = time.time()
        destroy_time = destroy_end_time - destroy_start_time

        if cleanup_success:
            print(f"Resources cleaned up successfully in {destroy_time:.2f} seconds")
            print(f"Destroyed {get_resource_count(outputs)} resources successfully")
            cleanup_verified = True
            cleanup_message = "Boto3 cleanup successful"
        else:
            print("Error: Cleanup failed!")
            cleanup_verified = False
            cleanup_message = "Boto3 cleanup reported failure"
        
        init_time = 0.0
        total_operation_time = apply_time + destroy_time

        print(f"Total operation time took {total_operation_time:.2f} seconds")
        
        return (outputs, apply_time, destroy_time, validation_passed, missing_outputs, unexpected_outputs,
                cleanup_verified, cleanup_message, init_time, total_operation_time)
    
    except Exception as e:
        print(f"Error: Boto3 scenario failed: {e}")
        exit(1)

def run_cf_scenario(scenario_name, count):
    import uuid
    stack_name = f"benchmark-{scenario_name.replace('_', '-')}-{str(uuid.uuid4())[:8]}"
    template_path = generate_cf_template(scenario_name, count)

    print("Deploying CloudFormation stack...")
    apply_start_time = time.time()

    cf_create = subprocess.run([
        'aws', 'cloudformation', 'create-stack',
        '--stack-name', stack_name,
        '--template-body', f'file://{template_path}',
        '--region', 'eu-north-1'
    ], capture_output=True, text=True)

    if cf_create.returncode != 0:
        print("CloudFormation stack creation failed")
        print(cf_create.stderr)
        exit(1)

    cf_wait = subprocess.run([
        'aws', 'cloudformation', 'wait', 'stack-create-complete',
        '--stack-name', stack_name,
        '--region', 'eu-north-1'
    ], capture_output=True, text=True)

    apply_end_time = time.time()
    apply_time = apply_end_time - apply_start_time

    if cf_wait.returncode != 0:
        print("CloudFormation stack wait failed")
        print(cf_wait.stderr)
        exit(1)

    print(f"Stack deployed successfully in {apply_time:.2f} seconds")

    cf_describe = subprocess.run([
        'aws', 'cloudformation', 'describe-stacks',
        '--stack-name', stack_name,
        '--region', 'eu-north-1'
    ], capture_output=True, text=True)

    if cf_describe.returncode != 0:
        print("CloudFormation describe-stacks failed")
        print(cf_describe.stderr)
        exit(1)

    outputs = parse_cf_outputs(cf_describe.stdout)
    validation_passed, missing_outputs, unexpected_outputs = validate_outputs(outputs, scenario_name, config)

    if args.verbose:
        if outputs:
            print("Created resources:")
            for name, value in outputs.items():
                print(f" {name}: {value}")

    print("Destroying CloudFormation stack...")
    destroy_start_time = time.time()

    cf_delete = subprocess.run([
        'aws', 'cloudformation', 'delete-stack',
        '--stack-name', stack_name,
        '--region', 'eu-north-1'
    ], capture_output=True, text=True)

    if cf_delete.returncode != 0:
        print("CloudFormation stack deletion failed")
        print(cf_delete.stderr)
        exit(1)

    cf_wait_delete = subprocess.run([
        'aws', 'cloudformation', 'wait', 'stack-delete-complete',
        '--stack-name', stack_name,
        '--region', 'eu-north-1'
    ], capture_output=True, text=True)

    destroy_end_time = time.time()
    destroy_time = destroy_end_time - destroy_start_time

    if cf_wait_delete.returncode != 0:
        print("CloudFormation stack deletion wait failed")
        print(cf_wait_delete.stderr)
        exit(1)

    print(f"Stack destroyed successfully in {destroy_time:.2f} seconds")

    total_operation_time = apply_time + destroy_time
    print(f"Total operation time took {total_operation_time:.2f} seconds")

    init_time = 0.0
    cleanup_verified = True
    cleanup_message = "CloudFormation stack deleted successfully"
    template_path.unlink(missing_ok=True)
    print(f"Temporary template cleaned up")

    return (outputs, apply_time, destroy_time, validation_passed, missing_outputs, unexpected_outputs,
            cleanup_verified, cleanup_message, init_time, total_operation_time)

def run_scenario(tool_name, scenario_name, count):
    if tool_name == 'terraform':
        return run_tf_scenario(scenario_name, count)
    elif tool_name == 'boto3':
        return run_boto3_scenario(scenario_name, count)
    elif tool_name == 'cloudformation':
        return run_cf_scenario(scenario_name, count)
    else:
        raise ValueError(f"Unknown tool type: {tool_name}")
        
if args.runs is not None:
    results, summary = run_interval_scenario(scenario_name, tool_name, args.count, args.runs, args.interval)
    log_interval_result(scenario_name, args.runs, args.interval, results, summary)
else:
    (outputs, apply_time, destroy_time, validation_passed, missing, unexpected,
     cleanup_verified, cleanup_message, init_time, total_operation_time) = run_scenario(tool_name, scenario_name, args.count)
    log_result(scenario_name, apply_time, destroy_time, total_operation_time, {
        "outputs": outputs,
        "resource_count": args.count,
        "validation_passed": validation_passed,
        "missing_outputs": missing,
        "unexpected_outputs": unexpected,
        "cleanup_verified": cleanup_verified,
        "cleanup_message": cleanup_message,
        "timing_breakdown": {
            "init_time": round(init_time, 2),
            "apply_time": round(apply_time, 2),
            "destroy_time": round(destroy_time, 2),
            "total_time": round(total_operation_time, 2)
        }
    })