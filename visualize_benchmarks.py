"""
File: visualize_benchmarks.py
Description: Visualizes benchmark results from the windower benchmarks
"""

import argparse
import json
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import os
from matplotlib.ticker import FuncFormatter

def format_number(x, pos):
    """Format large numbers with commas."""
    return f'{int(x):,}'

def format_time(x, pos):
    """Format time values based on magnitude."""
    if x < 0.001:
        return f'{x*1000:.2f} μs'
    elif x < 1:
        return f'{x*1000:.2f} ms'
    else:
        return f'{x:.2f} s'

def load_results(filename):
    with open(filename, 'r') as f:
        results = json.load(f)
    return results

def create_comparison_dataframe(results):
    data = []
    for result in results:
        data.append({
            'data_size': result['data_size'],
            'filter_time': result['filter_time_stats']['mean'],
            'filter_memory': result['filter_memory_stats']['mean'],
            'windows_time': result['create_windows_time_stats']['mean'],
            'windows_memory': result['create_windows_memory_stats']['mean'],
            'windows_generated': result['windows_generated'],
            'total_time': result['filter_time_stats']['mean'] + result['create_windows_time_stats']['mean'],
            'peak_memory': max(result['filter_memory_stats']['peak'], result['create_windows_memory_stats']['peak'])
        })
    return pd.DataFrame(data)

def plot_time_comparison(df, output_file=None):
    plt.figure(figsize=(12, 8))
    
    x = np.arange(len(df))
    width = 0.35
    
    ax = plt.subplot(111)
    
    filter_bars = ax.bar(x - width/2, df['filter_time'], width, label='filter_and_process_data()')
    windows_bars = ax.bar(x + width/2, df['windows_time'], width, label='create_windows()')
    
    ax.set_title('Execution Time Comparison')
    ax.set_xlabel('Data Size')
    ax.set_ylabel('Time (seconds)')
    ax.set_xticks(x)
    ax.set_xticklabels([f"{size:,}" for size in df['data_size']])
    ax.legend()
    
    # Add the time values on top of each bar
    def add_labels(bars):
        for bar in bars:
            height = bar.get_height()
            if height < 0.001:
                label = f"{height*1000:.2f} μs"
            elif height < 1:
                label = f"{height*1000:.2f} ms"
            else:
                label = f"{height:.2f} s"
            ax.annotate(label,
                        xy=(bar.get_x() + bar.get_width() / 2, height),
                        xytext=(0, 3),  # 3 points vertical offset
                        textcoords="offset points",
                        ha='center', va='bottom', rotation=90)
    
    add_labels(filter_bars)
    add_labels(windows_bars)
    
    plt.tight_layout()
    
    if output_file:
        plt.savefig(output_file)
    
    plt.show()

def plot_memory_comparison(df, output_file=None):
    plt.figure(figsize=(12, 8))
    
    x = np.arange(len(df))
    width = 0.35
    
    ax = plt.subplot(111)
    
    filter_bars = ax.bar(x - width/2, df['filter_memory'], width, label='filter_and_process_data()')
    windows_bars = ax.bar(x + width/2, df['windows_memory'], width, label='create_windows()')
    
    ax.set_title('Memory Usage Comparison')
    ax.set_xlabel('Data Size')
    ax.set_ylabel('Memory Usage (MB)')
    ax.set_xticks(x)
    ax.set_xticklabels([f"{size:,}" for size in df['data_size']])
    ax.legend()
    
    # Add the memory values on top of each bar
    def add_labels(bars):
        for bar in bars:
            height = bar.get_height()
            ax.annotate(f"{height:.1f} MB",
                        xy=(bar.get_x() + bar.get_width() / 2, height),
                        xytext=(0, 3),  # 3 points vertical offset
                        textcoords="offset points",
                        ha='center', va='bottom', rotation=90)
    
    add_labels(filter_bars)
    add_labels(windows_bars)
    
    plt.tight_layout()
    
    if output_file:
        plt.savefig(output_file)
    
    plt.show()

def plot_scaling(df, output_file=None):
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))
    
    # Time scaling plot
    ax1.plot(df['data_size'], df['filter_time'], 'o-', label='filter_and_process_data()')
    ax1.plot(df['data_size'], df['windows_time'], 's-', label='create_windows()')
    ax1.plot(df['data_size'], df['total_time'], '^-', label='Total')
    
    ax1.set_title('Time Scaling')
    ax1.set_xlabel('Data Size')
    ax1.set_ylabel('Time (seconds)')
    ax1.set_xscale('log')
    ax1.set_yscale('log')
    ax1.xaxis.set_major_formatter(FuncFormatter(format_number))
    ax1.yaxis.set_major_formatter(FuncFormatter(format_time))
    ax1.grid(True, which="both", ls="-", alpha=0.2)
    ax1.legend()
    
    # Memory scaling plot
    ax2.plot(df['data_size'], df['filter_memory'], 'o-', label='filter_and_process_data()')
    ax2.plot(df['data_size'], df['windows_memory'], 's-', label='create_windows()')
    ax2.plot(df['data_size'], df['peak_memory'], '^-', label='Peak')
    
    ax2.set_title('Memory Scaling')
    ax2.set_xlabel('Data Size')
    ax2.set_ylabel('Memory Usage (MB)')
    ax2.set_xscale('log')
    ax2.set_yscale('log')
    ax2.xaxis.set_major_formatter(FuncFormatter(format_number))
    ax2.grid(True, which="both", ls="-", alpha=0.2)
    ax2.legend()
    
    plt.tight_layout()
    
    if output_file:
        plt.savefig(output_file)
    
    plt.show()

def main():
    parser = argparse.ArgumentParser(description="Visualize windower benchmark results")
    parser.add_argument("-f", "--file", type=str,
                        help="Input benchmark results file (default: benchmark_results.json)")
    parser.add_argument("-o", "--output-dir", type=str, default="benchmark_images",
                        help="Output directory for visualization files (default: benchmark_images)")
    args = parser.parse_args()
    
    # Ensure output directory exists
    os.makedirs(args.output_dir, exist_ok=True)
    
    results = load_results(args.file)
    df = create_comparison_dataframe(results)
    
    # Print tabular results
    print("\n=== Benchmark Results ===")
    print(df.to_string(index=False, float_format=lambda x: f"{x:.6f}" if x < 1 else f"{x:.2f}"))
    
    # Create visualizations and save to output directory
    plot_time_comparison(df, os.path.join(args.output_dir, "time_comparison.png"))
    plot_memory_comparison(df, os.path.join(args.output_dir, "memory_comparison.png"))
    plot_scaling(df, os.path.join(args.output_dir, "scaling.png"))
    
    print(f"\nVisualizations saved to directory: {args.output_dir}")

if __name__ == "__main__":
    main()
