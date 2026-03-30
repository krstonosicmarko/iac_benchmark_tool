IaC benchmarking tool READMME

Contents:
1. About the tool
2. Installation guide
3. Running the tests

1. This tool is supposed to be used for running benchmarks for resource deployment. Its main use case is comparison. Of different resources, of different tools, of different providers, and anything in between.
The tests are ran and saved locally, using your IaC provider account. You input the desired resource and type of test, and the tool will run a timed deployment test of the provisioning and deprovisioning time.
After that you can find your results in the results folder. A result contains a text version of the test results in the form of a JSON file.

SUPPORTED TOOLS

Terraform — declarative, cloud-agnostic, HCL syntax. Manages state locally via state files.
Includes an initialization phase which contributes to total deployment time.

Boto3 — imperative, AWS-native Python SDK. Makes direct API calls with no initialization
overhead. Requires more implementation code than declarative tools.

AWS CloudFormation — declarative, AWS-native, YAML templates. Resources are provisioned
server-side by AWS with no local initialization phase. Configuration files are generated
dynamically at runtime based on the requested resource count. 

2. This program was developed and tested on a Windows machine using WSL2, likely compatible with Linux and macOS with minor adjustments, but not tried or tested. 

The list of dependencies necessary to install this tool is the following:

WSL2 (Windows users)
Python 3.10+
Terraform
AWS CLI
Git
An AWS account with credentials configured via aws configure

PREREQUISITES Installation:

Installing WSL2 and Git

wsl --install
winget install -e --id Git.Git
(likely necessary to install the computer after WSL2 installation is finished)

Install AWS CLI and Terraform

winget install -e --id Amazon.AWSCLI
winget install -e --id HashiCorp.Terraform

ENVIRONMENT SETUP inside WSL (or Linux for users of other OS's)

Install Python

sudo apt update
sudo apt install python3 python3-pip -y

Configure AWS credentials

aws configure
(follow Amazon's own guide for setting up your credentials -> https://docs.aws.amazon.com/cli/latest/userguide/getting-started-quickstart.html)

VERIFICATION

python3 --version; terraform --version; aws --version; git --version

CLONING THE REPOSITORY

Open the WSL terminal and run the following:

cd ~

git clone https://github.com/krstonosicmarko/iac_benchmark_tool.git

cd iac_benchmark_tool

FINAL ENVIRONMENT CHECK

python3 -m venv venv

source venv/bin/activate

pip install -r requirements.txt

This will install any final Python dependencies that you might be missing out on from the included requirements.txt file.

3. After everything is set up you can run your first test. This tool allows you to set different testing parameters using flags inside the main command.
The list of flags is the following:

'--scenario' or '-s' -> Select the scenario you want to test
'--tool' or '-t' -> Select the tool you want to use
'--verbose' or -'v' -> Select if you want to run in verbose mode(detailed output, no structure) or not (curated output)
'--count' or '-c' -> Select the quantity of a resource you want to test (Default is 1)
'--runs' or '-r' -> Select how many consecutive runs you want to do in one test 
'--interval' or '-i' -> Select the amount of seconds each interval will take between consecutive runs (Default is 0)

For a full list of options for scenarios, tools and count options, open the config.yaml file or input 'python3 benchmark.py --help' into the terminal. 

Before running your first test, navigate to the iac_benchmark_tool folder inside your terminal and run the following:

python3 benchmark.py -s s3_basic -t terraform -c 25

This command will launch a test that will provision and deprovision 25 instances of the AWS S3 bucket. After finishing the test, a 'Test results' folder will
be created (iac_benchmark_tool/Test results) where you can find test results inside JSON files. Each test will have a scenario name, tool used, resource count, time and date, additionally run count is
also included inside the file name if said test included the '--runs' flag. Inside the created JSON results file you can find initialization, deploy, destroy times of each 
resource provisioning, alongside a final summary of results like success rate, average times, fastest and slowest times. 

NOTE: This tool was made using the AWS Free Tier subscription, thus certain limitations apply. To find our more details on the limitations of this subscription tier, 
open the config.yaml file and / or type 'python3 benchmark.py --help'. 

For example, with the Free Tier subscription, it is possible to provision up to 25 'S3 buckets' reliably. The '25' amount is what I tested and could replicate reliably.
Similar restrictions are set to all scalable resources, but are not strict AWS Free Tier limitations. You are allowed to configure custom amounts, but I do not guarantee
a problem free experience and it falls beyond this projects scope. Thus following the limitations set inside this tool need to be followed if you are using a 
Free Tier subscription for a problem free testing. 

RESULTS ANALYSIS

After collecting test results, analysis.py can be used to generate graphs from your results.

Before running analysis.py, manually copy the result files you want to analyse into the appropriate folder:
- Analysis/basic_mode/ — for standard single deployment results
- Analysis/interval_mode/ — for interval mode results

Note: analysis.py is a plotting tool, not a data management tool. It does not automatically select or filter results. The user is responsible for placing only the desired result files in the Analysis folder before running. This is a known limitation and intentional design decision — automated result management is possible but out of scope for this project.

Run analysis.py with the following command:
python3 analysis.py -m basic_mode
python3 analysis.py -m interval_mode

Flags:
'-m' or '--mode' -> Select the mode of results to analyse (basic_mode or interval_mode)

basic_mode produces three graphs:
- Tool comparison — average total time per scenario grouped by tool
- Scaling efficiency — total time vs resource count per tool and scenario
- Terraform complexity overhead — init time vs deploy time for basic and complex scenarios

interval_mode produces one graph:
- Interval timings analysis — average total time per scenario/tool with fastest/slowest range shown as error bars

All graphs are saved to the graphs/ folder with a timestamp in the filename.
