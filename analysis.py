from pathlib import Path
import json
import pandas as pd
import argparse
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime

parser = argparse.ArgumentParser(description = "Program description to put")
parser.add_argument('-m', '--mode', required=True, choices=['basic_mode', 'interval_mode'], help='Choose program mode results to analyse')
args = parser.parse_args()
folder_path = args.mode

timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
Path("analysis/basic_mode").mkdir(parents=True, exist_ok=True)
Path("analysis/interval_mode").mkdir(parents=True, exist_ok=True)

def load_results(folder_path):
    results_folder = Path('analysis') / folder_path
    json_files = results_folder.glob("*.json")
    folder_data = []

    for file in json_files:
        with open(file, 'r') as f:
            data = json.load(f)

        file_record = {}

        if data.get('mode') == 'interval':
            file_record = {
                "scenario": data["scenario"],
                "tool": data["tool"],
                "count": data["configuration"]["count"],
                "runs": data["configuration"]["runs"],
                "interval": data["configuration"]["interval"],
                "avg_deploy_time": data["summary"]["avg_deploy_time"],
                "avg_destroy_time": data["summary"]["avg_destroy_time"],
                "avg_total_time": data["summary"]["avg_total_time"],
                "fastest_total_time": data["summary"]["fastest_total_time"],
                "slowest_total_time": data["summary"]["slowest_total_time"],
                "success_rate": data["summary"]["success_rate"]
            }
        else:
            file_record = {
                "scenario": data["scenario"],
                "tool": data["tool"],
                "count": data["metadata"]["resource_count"],
                "init_time": data["metadata"]["timing_breakdown"]["init_time"],
                "avg_deploy_time": data["deploy_time"],
                "avg_destroy_time": data["cleanup_time"],
                "avg_total_time": data["total_time"],
            }
        
        folder_data.append(file_record)
    
    return folder_data

results = load_results(folder_path)
df = pd.DataFrame(results)

def plot_tool_comparison(df, folder_path):
    Path("graphs/").mkdir(exist_ok=True)
    sns.barplot(x = 'scenario', y = 'avg_total_time', hue = 'tool', data = df)
    plt.savefig(f'graphs/tool_comparison_{folder_path}_{timestamp}.png')
    print(f"Graph saved to graphs/tool_comparison_{folder_path}_{timestamp}.png")
    plt.close()

def plot_tool_scaling(df, folder_path):
    Path("graphs/").mkdir(exist_ok=True)
    fig, ax = plt.subplots()

    for scenario in df['scenario'].unique():
        for tool in df['tool'].unique():
            subset = df[(df['scenario'] == scenario) & (df['tool'] == tool)]
            ax.plot(subset['count'], subset['avg_total_time'], label=f'{scenario} {tool}', marker = 'o')

    ax.set(xlabel = "Resource Count", ylabel = "Total Time (seconds)", title = 'Scaling Efficiency')
    ax.legend()
    ax.grid()
    plt.savefig(f'graphs/scaling_efficiency_{folder_path}_{timestamp}.png')
    print(f"Graph saved to graphs/scaling_efficiency_{folder_path}_{timestamp}.png")
    plt.close()

def plot_tool_complexity_tf(df, folder_path):
    Path("graphs/").mkdir(exist_ok=True)
    terraform_df = df[df['tool'] == 'terraform']
    melted = terraform_df[['scenario', 'init_time', 'avg_deploy_time']].melt(
        id_vars='scenario',
        var_name='metric',
        value_name='seconds'
    )

    sns.barplot(x = 'scenario', y = 'seconds', hue = 'metric', data = melted)
    plt.title('Terraform Complexity Overhead')
    plt.ylabel('Time(Seconds)')
    plt.savefig(f'graphs/complexity_overhead_tf_{folder_path}_{timestamp}.png')
    print(f"Graph saved to graphs/complexity_overhead_tf_{folder_path}_{timestamp}.png")
    plt.close()

def plot_interval_analysis(df, folder_path):
    Path("graphs/").mkdir(exist_ok=True)
    fig, ax = plt.subplots()
    x_pos = 0
    labels = []

    for scenario in df['scenario'].unique():
        for tool in df['tool'].unique():
            subset = df[(df['scenario'] == scenario) & (df['tool'] == tool)]
            avg = subset['avg_total_time'].values[0]
            fastest = subset['fastest_total_time'].values[0]
            slowest = subset['slowest_total_time'].values[0]
            yerr = [[avg - fastest], [slowest - avg]]
            ax.bar(x_pos, avg, yerr=yerr, capsize=5, color='steelblue', ecolor='red')
            labels.append(f'{scenario} {tool}')
            x_pos += 1

    ax.set_xticks(range(x_pos))
    ax.set_xticklabels(labels)
    ax.set(ylabel='Total Time (seconds)', title='Interval Timings Analysis')
    ax.grid(axis='y')
    plt.savefig(f'graphs/interval_analysis_{folder_path}_{timestamp}.png')
    print(f"Graph saved to graphs/interval_analysis_{folder_path}_{timestamp}.png")
    plt.close()

if df.duplicated(subset=['scenario', 'tool']).any():
    print("Warning: duplicate scenario/tool combinations detected in results folder. Remove duplicates before running analysis.")
    exit(1)

if args.mode == 'basic_mode':
    print("Generating tool comparison graph...")
    plot_tool_comparison(df, folder_path)
    print("Generating scaling efficiency graph...")
    plot_tool_scaling(df, folder_path)
    print("Generating total complexity graph for Terraform...")
    plot_tool_complexity_tf(df, folder_path)
else:
    print("Generating interval analysis graph...")
    plot_interval_analysis(df, folder_path)
