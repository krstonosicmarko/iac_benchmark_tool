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

def validate_outputs(outputs, scenario_name, config):
    """Validate that received outputs match expected outputs from YAML config"""
    expected = config['scenarios'][scenario_name]['expected_outputs']

    missing = []
    for expected_output in expected:
        if expected_output not in outputs:
            missing.append(expected_output)
    
    unexpected = []
    for actual_output in outputs:
        if actual_output not in expected:
            unexpected.append(actual_output)

    if missing:
        print(f"Missing expected outputs: {missing}")
    if unexpected:
        print(f"Unexpected outputs found: {unexpected}")

    validation_passed = len(missing) == 0
    return validation_passed, missing, unexpected

def verify_cleanup_success(destroy_output, expected_resource_count):
    """Verify that terraform destroy actually worked"""
    
    if "Destroy complete!" not in destroy_output:
        return False, "Terraform destroy did not report success"

    destroyed_count = destroy_output.count("Destruction complete")
    if destroyed_count != expected_resource_count:
        return False, f"Expected {expected_resource_count} resources destroyed, got {destroyed_count}"
    
    return True, "Cleanup verified successful"

vprint("Initializing Terraform...")
init_start_time = time.time()

tf_init = subprocess.run(
    ['terraform', 'init'], 
    cwd = working_dir,
    capture_output = True,
    text = True
)

init_end_time = time.time()
init_time = init_end_time - init_start_time

if tf_init.returncode != 0:
    print("Terraform initialization failed:")
    print(tf_init.stderr)
    exit(1)
else:
    vprint("Terraform initialized successfully")

print ("Applying Terraform configuration...")
apply_start_time = time.time()

tf_apply_process = subprocess.run(
    ['terraform', 'apply', '-auto-approve'],
    cwd = working_dir,
    capture_output = True,
    text = True
)

apply_end_time = time.time()
apply_time = apply_end_time - apply_start_time

if tf_apply_process.returncode != 0:
    print("Terraform apply failed:")
    print(tf_apply_process.stderr)
    exit(1)
else:
    print(f"Selected resources deployed successfully in {apply_time:.2f} seconds")
    if args.verbose:
        print(tf_apply_process.stdout)
        
outputs = parse_tf_outputs(tf_apply_process.stdout)

validation_passed, missing, unexpected = validate_outputs(outputs, scenario_name, config)

if outputs:
    print("Created resources: ")
    for name, value in outputs.items():
        print(f" {name}: {value}")

print("Cleaning up resources...")
destroy_start_time = time.time()

tf_destroy_process = subprocess.run(
    ['terraform', 'destroy', '-auto-approve'],
    cwd = working_dir,
    capture_output = True,
    text = True
)

destroy_end_time = time.time()    
destroy_time = destroy_end_time - destroy_start_time
total_operation_time = init_time + apply_time + destroy_time

if tf_apply_process.returncode == 0 and tf_destroy_process.returncode != 0:
    print("CRITICAL: Resources deployed but cleanup failed!")
    print("Manual cleanup required in AWS console")
    print("Check AWS console for orphaned resources")

if tf_destroy_process.returncode != 0:
    print("Terraform destroy failed:")
    print(tf_destroy_process.stderr)
    exit(1)
else:
    print(f"Resources cleaned up successfully in {destroy_time:.2f} seconds")

    cleanup_verified, cleanup_message = verify_cleanup_success(tf_destroy_process.stdout, len(outputs))
    
    if not cleanup_verified:
        print(f"CLEANUP WARNING: {cleanup_message}")
        print("Manual verification recommended in AWS console")
    else:
        print("Cleanup verification passed")

    if args.verbose:
        print(tf_destroy_process.stdout)


log_result(scenario_name, apply_time, destroy_time, {
    "outputs": outputs,
    "resource_count": len(outputs),
    "validation_passed": validation_passed,    
    "missing_outputs": missing,                
    "unexpected_outputs": unexpected,
    "cleanup_verified": cleanup_verified,
    "cleanup_message": cleanup_message,
    "timing_breakdown": {                 
        "init_time": init_time,
        "apply_time": apply_time,
        "destroy_time": destroy_time,
        "total_time": init_time + apply_time + destroy_time
    }
})