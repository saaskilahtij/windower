"""
File: perftester_windower.py
Authors: Johan Sääskilahti, Atte Rajavaara, Minna Repo, Topias Hämäläinen
Description: Compares performance and memory usage of windower functions using perftester
"""

import os
import time
import json
import random
import argparse
import pandas as pd
import orjson
import tracemalloc
import statistics
from typing import Dict, List, Any
from windower import create_windows, filter_and_process_data
import psutil

def generate_synthetic_data(size):
    """
    Generate synthetic data that mimics the structure of can_dump.json.
    
    Args:
        size (int): Number of entries to generate
        
    Returns:
        list: List of dictionaries containing synthetic data
    """
    print(f"Generating {size:,} synthetic data entries...")
    
    # ECU names to use in the synthetic data
    ecu_names = ["BRAKE", "ENGINE", "TRANSMISSION", "STEERING", "SUSPENSION", 
                "BATTERY", "CLIMATE", "NAVIGATION", "AUDIO", "SECURITY"]
    
    # Start time for timestamps
    start_time = time.time()
    
    # Generate synthetic data
    data = []
    for i in range(size):
        # Select a random ECU
        ecu_name = random.choice(ecu_names)
        
        # Generate a timestamp (incrementing from start_time)
        timestamp = start_time + (i * 0.01)  # 10ms intervals
        
        # Generate a random ID (16-bit CAN ID)
        can_id = random.randint(0, 0x7FF)
        
        # Generate synthetic data based on ECU type
        if ecu_name == "BRAKE":
            brake_amount = random.randint(0, 100)
            brake_pedal = random.randint(0, 100)
            data_str = json.dumps({"BRAKE_AMOUNT": brake_amount, "BRAKE_PEDAL": brake_pedal})
        elif ecu_name == "ENGINE":
            rpm = random.randint(500, 7000)
            throttle = random.randint(0, 100)
            data_str = json.dumps({"RPM": rpm, "THROTTLE": throttle})
        elif ecu_name == "TRANSMISSION":
            gear = random.randint(0, 8)
            speed = random.randint(0, 200)
            data_str = json.dumps({"GEAR": gear, "SPEED": speed})
        elif ecu_name == "STEERING":
            angle = random.randint(-900, 900)
            torque = random.randint(-100, 100)
            data_str = json.dumps({"ANGLE": angle, "TORQUE": torque})
        elif ecu_name == "SUSPENSION":
            height = random.randint(0, 100)
            pressure = random.randint(0, 100)
            data_str = json.dumps({"HEIGHT": height, "PRESSURE": pressure})
        elif ecu_name == "BATTERY":
            voltage = random.uniform(11.0, 14.0)
            current = random.uniform(-100.0, 100.0)
            data_str = json.dumps({"VOLTAGE": voltage, "CURRENT": current})
        elif ecu_name == "CLIMATE":
            temp = random.uniform(15.0, 30.0)
            fan = random.randint(0, 10)
            data_str = json.dumps({"TEMP": temp, "FAN": fan})
        elif ecu_name == "NAVIGATION":
            lat = random.uniform(59.0, 61.0)
            lon = random.uniform(24.0, 26.0)
            data_str = json.dumps({"LAT": lat, "LON": lon})
        elif ecu_name == "AUDIO":
            volume = random.randint(0, 100)
            bass = random.randint(-10, 10)
            data_str = json.dumps({"VOLUME": volume, "BASS": bass})
        else:  # SECURITY
            locked = random.choice([True, False])
            alarm = random.choice([True, False])
            data_str = json.dumps({"LOCKED": locked, "ALARM": alarm})
        
        # Generate a random raw CAN data (8 bytes)
        raw_data = ''.join([f"{random.randint(0, 255):02x}" for _ in range(8)])
        
        # Create the entry
        entry = {
            "name": ecu_name,
            "timestamp": timestamp,
            "id": can_id,
            "data": data_str,
            "raw": f"0x{raw_data}"
        }
        
        data.append(entry)
    
    print(f"Generated {len(data):,} synthetic data entries")
    return data

def print_bmresults(function_name, time_results, memory_results):
    """Helper function to print time and memory benchmark results."""
    print(f"\n{function_name} time benchmark:")
    print(f"  Min: {time_results['min']:.6f} s")
    print(f"  Max: {time_results['max']:.6f} s")
    print(f"  Mean: {time_results['mean']:.6f} s")
    print(f"  Median: {time_results['median']:.6f} s")

    print(f"\n{function_name} memory usage benchmark:")
    print(f"  Mean memory usage: {memory_results['mean']:.2f} MB")
    print(f"  Max memory usage: {memory_results['max']:.2f} MB")
    print(f"  Peak memory usage: {memory_results['peak']:.2f} MB")

def benchmark_memory_usage(func, *args, **kwargs):
    """
    Measure the memory usage of a function.
    
    Args:
        func: The function to benchmark
        *args, **kwargs: Arguments to pass to the function
        
    Returns:
        float: Memory usage in MB
    """
    # Start tracking memory
    tracemalloc.start()
    
    # Get the current process to measure memory usage
    process = psutil.Process(os.getpid())
    
    # Record starting memory usage
    start_memory = process.memory_info().rss / (1024 * 1024)  # Convert to MB
    
    # Execute the function
    result = func(*args, **kwargs)
    
    # Record ending memory usage
    end_memory = process.memory_info().rss / (1024 * 1024)  # Convert to MB
    
    # Get peak memory usage
    peak_memory, _ = tracemalloc.get_traced_memory()
    peak_memory = peak_memory / (1024 * 1024)  # Convert to MB
    
    # Stop tracking memory
    tracemalloc.stop()
    
    memory_used = end_memory - start_memory
    
    return {
        'memory_used': memory_used,
        'peak_memory': peak_memory
    }, result

def benchmark_execution_time(func, *args, **kwargs):
    """
    Measure the execution time of a function.
    
    Args:
        func: The function to benchmark
        *args, **kwargs: Arguments to pass to the function
        
    Returns:
        float: Execution time in seconds
    """
    # Record starting time
    start_time = time.time()
    
    # Execute the function
    result = func(*args, **kwargs)
    
    # Record ending time
    end_time = time.time()
    
    execution_time = end_time - start_time
    
    return execution_time, result

def benchmark_complete_pipeline(data_size, window_length=1.0, step=None, iterations=3):
    """
    Benchmark the complete windower pipeline from raw data to windows.
    
    Args:
        data_size: Number of entries to generate
        window_length: Length of each window in seconds
        step: How many seconds the window moves forward
        iterations: Number of iterations for time benchmarks
        
    Returns:
        dict: Benchmark results
    """
    print(f"\n=== Benchmarking complete pipeline with {data_size:,} entries ===")
    
    # Generate synthetic data
    data = generate_synthetic_data(data_size)
    
    # Benchmark filter_and_process_data
    print("\nBenchmarking filter_and_process_data...")
    filter_time_results = []
    filter_memory_results = []
    
    filtered_data = None
    
    for i in range(iterations):
        print(f"  Iteration {i+1}/{iterations}")
        
        # Benchmark memory usage
        memory_info, filtered_data = benchmark_memory_usage(filter_and_process_data, data)
        filter_memory_results.append(memory_info)
        
        # Benchmark execution time
        execution_time, _ = benchmark_execution_time(filter_and_process_data, data)
        filter_time_results.append(execution_time)
    
    # Benchmark create_windows
    print("\nBenchmarking create_windows...")
    create_windows_time_results = []
    create_windows_memory_results = []
    
    windows_df = None
    
    for i in range(iterations):
        print(f"  Iteration {i+1}/{iterations}")
        
        # Benchmark memory usage
        memory_info, windows_df = benchmark_memory_usage(create_windows, filtered_data, window_length, step)
        create_windows_memory_results.append(memory_info)
        
        # Benchmark execution time
        execution_time, _ = benchmark_execution_time(create_windows, filtered_data, window_length, step)
        create_windows_time_results.append(execution_time)
    
    # Calculate final results
    filter_time_stats = {
        'min': min(filter_time_results),
        'max': max(filter_time_results),
        'mean': statistics.mean(filter_time_results),
        'median': statistics.median(filter_time_results)
    }
    
    filter_memory_stats = {
        'mean': statistics.mean([r['memory_used'] for r in filter_memory_results]),
        'max': max([r['memory_used'] for r in filter_memory_results]),
        'peak': max([r['peak_memory'] for r in filter_memory_results])
    }
    
    create_windows_time_stats = {
        'min': min(create_windows_time_results),
        'max': max(create_windows_time_results),
        'mean': statistics.mean(create_windows_time_results),
        'median': statistics.median(create_windows_time_results)
    }
    
    create_windows_memory_stats = {
        'mean': statistics.mean([r['memory_used'] for r in create_windows_memory_results]),
        'max': max([r['memory_used'] for r in create_windows_memory_results]),
        'peak': max([r['peak_memory'] for r in create_windows_memory_results])
    }
    
    # Print results
    print_bmresults("filter_and_process_data", filter_time_stats, filter_memory_stats)
    print_bmresults("create_windows", create_windows_time_stats, create_windows_memory_stats)
    
    # Return results
    return {
        'data_size': data_size,
        'window_length': window_length,
        'step': step,
        'iterations': iterations,
        'filter_time_stats': filter_time_stats,
        'filter_memory_stats': filter_memory_stats,
        'create_windows_time_stats': create_windows_time_stats,
        'create_windows_memory_stats': create_windows_memory_stats,
        'windows_generated': len(windows_df) if windows_df is not None else 0
    }

def run_benchmarks(sizes, window_length=1.0, step=None, iterations=3, output_file=None):
    """
    Run benchmarks for different data sizes and save results.
    
    Args:
        sizes: List of data sizes to benchmark
        window_length: Length of each window in seconds
        step: How many seconds the window moves forward
        iterations: Number of iterations for time benchmarks
        output_file: File to save results (optional)
    """
    print(f"Running benchmarks with window_length={window_length}, step={step or window_length}")
    print(f"Running {iterations} iterations for each size")
    
    results = []
    
    for size in sizes:
        try:
            result = benchmark_complete_pipeline(size, window_length, step, iterations)
            results.append(result)
            
            # Print summary for this size
            print(f"\n=== Summary for {size:,} entries ===")
            print(f"filter_and_process_data: {result['filter_time_stats']['mean']:.6f} s, {result['filter_memory_stats']['mean']:.2f} MB")
            print(f"create_windows: {result['create_windows_time_stats']['mean']:.6f} s, {result['create_windows_memory_stats']['mean']:.2f} MB")
            print(f"Windows generated: {result['windows_generated']}")
            
        except Exception as e:
            print(f"Error benchmarking size {size}: {e}")
            traceback.print_exc()
    
    # Save results to file if specified
    if output_file:
        try:
            with open(output_file, 'w') as f:
                json.dump(results, f, indent=2)
            print(f"\nResults saved to {output_file}")
        except Exception as e:
            print(f"Error saving results to {output_file}: {e}")
    
    # Print final comparison
    print("\n=== Benchmark Comparison ===")
    print("Data Size | filter_time | filter_memory | windows_time | windows_memory | Windows")
    print("----------|-------------|---------------|--------------|----------------|--------")
    
    for result in results:
        size = result['data_size']
        filter_time = result['filter_time_stats']['mean']
        filter_memory = result['filter_memory_stats']['mean']
        windows_time = result['create_windows_time_stats']['mean']
        windows_memory = result['create_windows_memory_stats']['mean']
        windows = result['windows_generated']
        
        print(f"{size:10,d} | {filter_time:11.6f} | {filter_memory:13.2f} | {windows_time:12.6f} | {windows_memory:14.2f} | {windows:7d}")
    
    return results

if __name__ == "__main__":
    # Set up argument parser
    parser = argparse.ArgumentParser(description="Performance tester for windower functions")
    parser.add_argument("-s", "--sizes", nargs='+', type=int, 
                       default=[1000, 10000, 100000, 1000000, 10000000],
                       help="Data sizes to benchmark (default: 1000 10000 100000 1000000 10000000)")
    parser.add_argument("-i", "--iterations", type=int, default=3,
                       help="Number of iterations for time benchmarks (default: 3)")
    parser.add_argument("-w", "--window-length", type=float, default=1.0,
                       help="Window length in seconds (default: 1.0)")
    parser.add_argument("-t", "--step", type=float, default=None,
                       help="Step size in seconds (default: same as window length)")
    parser.add_argument("-o", "--output", type=str, default="benchmark_results.json",
                       help="Output file for benchmark results (default: benchmark_results.json)")
    args = parser.parse_args()
    
    # Run benchmarks
    run_benchmarks(
        sizes=args.sizes,
        window_length=args.window_length,
        step=args.step,
        iterations=args.iterations,
        output_file=args.output
    )
