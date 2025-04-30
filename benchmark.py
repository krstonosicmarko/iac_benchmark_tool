import subprocess
import time
import argparse

parser = argparse.ArgumentParser(description='Benchmark Terraform S3 bucket deployment')
parser.add_argument('-v', '--verbose', action='store_true', help='Show detailed Terraform output')
args = parser.parse_args()

working_dir = "/mnt/c/Users/Marko/Desktop/thesis/s3_script"

def vprint(message):
    if args.verbose:
        print(message)

#terraform initialize
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

#terraform apply

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
    print(f"S3 bucket deployed successfully in {deploy_time:.2f} seconds")
    if args.verbose:
        print(tf_apply_process.stdout)
    else:
        bucket_name = None
        bucket_region = None
        for line in tf_apply_process.stdout.split('\n'):
            if "bucket_name" in line:
                bucket_name = line.strip()
            if "bucket_region" in line:
                bucket_region = line.strip()

        if bucket_name and bucket_region:
            print(f"Created: {bucket_name}, {bucket_region}")

#terraform destroy
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

if tf_destroy_process.returncode != 0:
    print("Terraform destroy failed:")
    print(tf_destroy_process.stderr)
    exit(1)
else:
    print(f"Resources cleaned up successfully in {cleanup_time:.2f} seconds")
    if args.verbose:
        print(tf_destroy_process.stdout)

print("\nBenchmark Summary:")
print(f"Deployment Time: {deploy_time:.2f} seconds")
print(f"Cleanup Time: {cleanup_time:.2f} seconds")
print(f"Total Operation Time: {deploy_time + cleanup_time:.2f} seconds")

#make it reusable and adaptable to other resources, not just s3_bucket