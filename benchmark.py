import subprocess
import time
import argparse
import json
import yaml
from datetime import datetime
from pathlib import Path
import importlib.util

with open('config.yaml', 'r',) as file:
    config = yaml.safe_load(file)

parser = argparse.ArgumentParser(description='Benchmark Terraform deployment')
parser.add_argument('-v', '--verbose', action='store_true', help='Show detailed output')
parser.add_argument('--scenario', required = True, help='Scenario to run')
parser.add_argument('--tool', required = True, choices = ['terraform', 'boto3'], help = 'IaC tool to use')
args = parser.parse_args()
scenario_name = args.scenario
tool_type = args.tool

def vprint(message):
    if args.verbose:
        print(message)

def log_result (scenario, deploy_time, cleanup_time, extra_info = None):
    timestamp = datetime.now()

    result = {
        "scenario": scenario,
        "tool": tool_type,
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

    filename = f"results/{scenario}_{tool_type}_{timestamp.strftime('%Y%m%d_%H%M%S')}.json"
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

def get_working_dir (tool_type, scenario_name):
    if tool_type == "terraform":
        return f"/mnt/c/Users/Marko/Desktop/thesis/s3_script/scenarios/terraform/{scenario_name}"
    elif tool_type == "boto3":
        return f"/mnt/c/Users/Marko/Desktop/thesis/s3_script/scenarios/boto3"
    else:
        raise ValueError(f"Unknown tool type: {tool_type}")

if scenario_name not in config['scenarios']:
    print(f"Error: Scenario '{scenario_name}' does not exist")
    print(f"Available scenarios: {list(config['scenarios'].keys())}")
    exit(1)

scenario_config = config['scenarios'][scenario_name]

if 'tools' in scenario_config and tool_type not in scenario_config['tools']:
    print(f"Error: Tool '{tool_type}' not supported for scenario '{scenario_name}'")
    print(f"Supported tools: {scenario_config.get('tools', ['terraform'])}")
    exit(1)

print(f"Running scenario: {scenario_config['description']} using {tool_type}")

def run_tf_scenario (scenario_name):
    """Run Terraform-based scenario"""
    working_dir = get_working_dir("terraform", scenario_name)
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

    return (outputs, apply_time, destroy_time, validation_passed, missing, unexpected, 
            cleanup_verified, cleanup_message, init_time, total_operation_time)
    
def run_boto3_scenario(scenario_name):
    """Run Boto3-based scenario - placeholder for now"""
    module_path = f"scenarios/boto3/{scenario_name}.py"
    spec = importlib.util.spec_from_file_location(scenario_name, module_path)
    scenario_module = importlib.util.module_from_spec(spec)

    try:
        spec.loader.exec_module(scenario_module)
    except FileNotFoundError:
        print(f"Boto3 scenario file not found: {module_path}")
        exit(1)

    print("Deploying resources with Boto3...")
    deploy_starts_time = time.time()

    try:
        outputs = scenario_module.deploy()
        deploy_end_time = time.time()
        apply_time = deploy_end_time - deploy_starts_time

        print(f"Resources deployed successfully in {apply_time:.2f} seconds")

        validation_passed, missing, unexpected = validate_outputs(outputs, scenario_name, config)

        if outputs:
            print("Created resources:")
            for name, value in outputs.items():
                print(f"  {name}: {value}")
        
        print("Cleaning up resources...")
        destroy_start_time = time.time()
        
        cleanup_success = scenario_module.destroy(outputs)
        destroy_end_time = time.time()
        destroy_time = destroy_end_time - destroy_start_time
        
        if cleanup_success:
            print(f"Resources cleaned up successfully in {destroy_time:.2f} seconds")
            cleanup_verified = True
            cleanup_message = "Boto3 cleanup successful"
        else:
            print("Cleanup failed!")
            cleanup_verified = False
            cleanup_message = "Boto3 cleanup reported failure"
        
        init_time = 0.0
        total_operation_time = apply_time + destroy_time
        
        return (outputs, apply_time, destroy_time, validation_passed, missing, unexpected,
                cleanup_verified, cleanup_message, init_time, total_operation_time)
                
    except Exception as e:
        print(f"Boto3 scenario failed: {e}")
        exit(1)


def run_scenario(tool_type, scenario_name):
    """Main scenario runner that delegates to tool-specific functions"""
    if tool_type == "terraform":
        return run_tf_scenario(scenario_name)
    elif tool_type == "boto3":
        return run_boto3_scenario(scenario_name)
    else:
        raise ValueError(f"Unknown tool type: {tool_type}")

(outputs, apply_time, destroy_time, validation_passed, missing, unexpected, 
 cleanup_verified, cleanup_message, init_time, total_operation_time) = run_scenario(tool_type, scenario_name)

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