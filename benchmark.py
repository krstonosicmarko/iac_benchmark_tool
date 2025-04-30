import subprocess
import time

working_dir = "/mnt/c/Users/Marko/Desktop/thesis/s3_script"

#terraform initialize

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
    print("Terraform initialized successfully")

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
    print(tf_apply_process.stdout)

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
    print(tf_destroy_process.stdout) #possibly filter the output so only main information is displayed
    # and catch any errors, if they appear, and log them