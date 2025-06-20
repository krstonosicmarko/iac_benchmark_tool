import subprocess
import time
import argparse
import json
import yaml
from datetime import datetime
from pathlib import Path

with open('config.yaml', 'r',) as file:
    config = yaml.safe_load(file)

parser = argparse.ArgumentParser(description='Benchmark Terraform deployment')
parser.add_argument('-v', '--verbose', action='store_true', help='Show detailed output')
parser.add_argument('--scenario', required=True, help='Scenario to run')
args = parser.parse_args()
scenario_name = args.scenario

if scenario_name not in config['scenarios']:
    print(f"Error: Scenario '{scenario_name}' does not exist")
    print(f"Available scenarios: {list(config['scenarios'].keys())}")
    exit(1)

print(f"Running scenario: {config['scenarios'][scenario_name]['description']}")

working_dir = f"/mnt/c/Users/Marko/Desktop/thesis/s3_script/scenarios/{scenario_name}"

def vprint(message):
    if args.verbose:
        print(message)

def log_result (scenario, deploy_time, cleanup_time, extra_info = None):
    timestamp = datetime.now()

    result = {
        "scenario": scenario,
        "timestamp": timestamp.isoformat(),
        "deploy_time": deploy_time,
        "cleanup_time": cleanup_time,
        "total_time": total_operation_time,
        "date": timestamp.strftime("%Y-%m-%d"),
        "time": timestamp.strftime("%H:%M:%S")
    }

    if extra_info:
        result["metadata"] = extra_info

    Path("results").mkdir(exist_ok=True)

    filename = f"results/{scenario}_{timestamp.strftime('%Y%m%d_%H%M%S')}.json"
    with open(filename, 'w') as f:
        json.dump(result, f, indent=2)
    
    print(f"Results logged to: {filename}")
    return result

def parse_tf_outputs(terraform_output):
    outputs = {}
    found_outputs = False

    for line in terraform_output.split('\n'):
        if line.startswith("Outputs:"):
            found_outputs = True
            continue
        
        if found_outputs and " = " in line:
            parts = line.split(" = ")
            name = parts[0]
            value = parts[1]
            clean_value = value.strip('"')
            outputs[name] = clean_value

    return outputs

vprint("Initializing Terraform...")
tf_init = subprocess.run(
    ['terraform', 'init'], 
    cwd = working_dir,
    capture_output = True,
    text = True
)

if tf_init.returncode != 0:
    print("Terraform initialization failed:")
    print(tf_init.stderr)
    exit(1)
else:
    vprint("Terraform initialized successfully")

print ("Applying Terraform configuration...")
start_time = time.time()

tf_apply_process = subprocess.run(
    ['terraform', 'apply', '-auto-approve'],
    cwd = working_dir,
    capture_output = True,
    text = True
)

end_time = time.time()
deploy_time = end_time - start_time

if tf_apply_process.returncode != 0:
    print("Terraform apply failed:")
    print(tf_apply_process.stderr)
    exit(1)
else:
    print(f"Selected resources deployed successfully in {deploy_time:.2f} seconds")
    if args.verbose:
        print(tf_apply_process.stdout)
    else:
        bucket_name = None
        bucket_region = None
        
        outputs = parse_tf_outputs(tf_apply_process.stdout)

        if outputs:
            print("Created resources: ")
            for name, value in outputs.items():
                print(f" {name}: {value}")

print("Cleaning up resources...")
start_cleanup_time = time.time()

tf_destroy_process = subprocess.run(
    ['terraform', 'destroy', '-auto-approve'],
    cwd = working_dir,
    capture_output = True,
    text = True
)

end_cleanup_time = time.time()
cleanup_time = end_cleanup_time - start_cleanup_time
total_operation_time = deploy_time + cleanup_time

if tf_destroy_process.returncode != 0:
    print("Terraform destroy failed:")
    print(tf_destroy_process.stderr)
    exit(1)
else:
    print(f"Resources cleaned up successfully in {cleanup_time:.2f} seconds")
    if args.verbose:
        print(tf_destroy_process.stdout)

log_result(scenario_name, deploy_time, cleanup_time, {
    "outputs": outputs,
    "resource_count": len(outputs)
})