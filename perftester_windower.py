"""
File: perftester_windower.py
Authors: Johan Sääskilahti, Atte Rajavaara, Minna Repo, Topias Hämäläinen
Description: Compares performance and memory usage of windower functions using perftester
"""

# All code is placed under the main block because without this,
# multiprocessing does not work correctly on Windows.
# Previously, without this structure, it caused the error:
# "RuntimeError: An attempt has been made to start a new process
# before the current process has finished its bootstrapping phase".
# Placing the code under if __name__ == "__main__": made it work.

if __name__ == "__main__":
    import perftester
    import windower
    import argparse
    import os
    import time
    import pandas as pd
    import orjson
    import random
    import json

    # Set up argument parser
    parser = argparse.ArgumentParser(description="Performance tester for windower functions")
    parser.add_argument("-s", "--size", type=int, default=10000,
                       help="Number of entries to generate for testing (default: 10000)")
    parser.add_argument("-b", "--buffer-size", type=int, default=1000,
                       help="Buffer size to use for buffered operations (default: 1000)")
    parser.add_argument("-n", "--number", type=int, default=2,
                       help="Number of iterations for time benchmarks (default: 2)")
    parser.add_argument("-r", "--repeat", type=int, default=2,
                       help="Number of repetitions for time benchmarks (default: 2)")
    args = parser.parse_args()
    
    # Configuration
    DATA_SIZE = args.size
    BUFFER_SIZE = args.buffer_size
    NUMBER = args.number
    REPEAT = args.repeat
    
    # Output filenames
    CSV_FILENAME = "output.csv"
    JSON_FILENAME = "output.json"
    WINDOW_LENGTH = 1

    def print_bmresults(function_name, time_results, memory_results):
        """Helper function to print time and memory benchmark results."""
        print(f"\n{function_name} time benchmark:")
        print(f"  Min: {time_results['min']:.6f} s")
        print(f"  Max: {time_results['max']:.6f} s")
        print(f"  Mean: {time_results['mean']:.6f} s")

        print(f"\n{function_name} memory usage benchmark:")
        print(f"  Mean memory usage: {memory_results['mean']:.2f} MB")
        print(f"  Max memory usage: {memory_results['max']:.2f} MB")

    def generate_synthetic_data(size):
        """
        Generate synthetic data that mimics the structure of can_dump.json.
        
        Args:
            size (int): Number of entries to generate
            
        Returns:
            list: List of dictionaries containing synthetic data
        """
        print(f"Generating {size} synthetic data entries...")
        
        # ECU names to use in the synthetic data
        ecu_names = ["BRAKE", "ENGINE", "TRANSMISSION", "STEERING", "SUSPENSION", 
                    "BATTERY", "CLIMATE", "NAVIGATION", "AUDIO", "SECURITY"]
        
        # Start time for timestamps (current time)
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
        
        print(f"Generated {len(data)} synthetic data entries")
        return data

    # ===== JSON READING TESTS =====
    
    def perftester_read_file_unbuffered():
        """Tests the performance and memory usage of windower.read_file() without buffering"""
        # Create a temporary JSON file with the synthetic data
        with open("temp_data.json", "w") as f:
            json.dump(json_data, f)
        
        # Read the file
        result = windower.read_file("temp_data.json", buffered=False)
        
        # Clean up
        os.remove("temp_data.json")
        return result
    
    def perftester_read_file_buffered():
        """Tests the performance and memory usage of windower.read_file() with buffering"""
        # Create a temporary JSON file with the synthetic data
        with open("temp_data.json", "w") as f:
            json.dump(json_data, f)
        
        # Read the file
        result = windower.read_file("temp_data.json", buffered=True, buffer_size=BUFFER_SIZE)
        
        # Clean up
        os.remove("temp_data.json")
        return result
    
    # ===== CSV READING TESTS =====
    
    def perftester_read_csv_unbuffered():
        """Tests the performance and memory usage of windower.read_csv_file() without buffering"""
        # Create a temporary CSV file with the synthetic data
        df = pd.DataFrame(json_data)
        df.to_csv("temp_data.csv", sep=";", index=False)
        
        # Read the file
        result = windower.read_csv_file("temp_data.csv", buffered=False)
        
        # Clean up
        os.remove("temp_data.csv")
        return result
    
    def perftester_read_csv_buffered():
        """Tests the performance and memory usage of windower.read_csv_file() with buffering"""
        # Create a temporary CSV file with the synthetic data
        df = pd.DataFrame(json_data)
        df.to_csv("temp_data.csv", sep=";", index=False)
        
        # Read the file
        result = windower.read_csv_file("temp_data.csv", buffered=True, buffer_size=BUFFER_SIZE)
        
        # Clean up
        os.remove("temp_data.csv")
        return result
    
    # ===== JSON WRITING TESTS =====
    
    def perftester_dict_to_json_unbuffered():
        """Tests the performance and memory usage of windower.dict_to_json() without buffering"""
        return windower.dict_to_json(json_data, JSON_FILENAME, buffered=False)
    
    def perftester_dict_to_json_buffered():
        """Tests the performance and memory usage of windower.dict_to_json() with buffering"""
        return windower.dict_to_json(json_data, JSON_FILENAME, buffered=True, buffer_size=BUFFER_SIZE)
    
    # ===== CSV WRITING TESTS =====
    
    def perftester_dict_to_csv_unbuffered():
        """Tests the performance and memory usage of windower.dict_to_csv() without buffering"""
        return windower.dict_to_csv(json_data, WINDOW_LENGTH, CSV_FILENAME, buffered=False)
    
    def perftester_dict_to_csv_buffered():
        """Tests the performance and memory usage of windower.dict_to_csv() with buffering"""
        return windower.dict_to_csv(json_data, WINDOW_LENGTH, CSV_FILENAME, buffered=True, buffer_size=BUFFER_SIZE)
    
    # ===== FILTER AND PROCESS TESTS =====
    
    def perftester_filter_and_process_data():
        """Tests the performance and memory usage of windower.filter_and_process_data()"""
        return windower.filter_and_process_data(json_data, ecu_name=["brake"])

    # ===== RUN TESTS =====
    
    print(f"Running performance tests with {DATA_SIZE} entries")
    print(f"Buffer size: {BUFFER_SIZE}")
    print(f"Number of iterations: {NUMBER}, Number of repetitions: {REPEAT}")
    
    # Generate synthetic data
    json_data = generate_synthetic_data(DATA_SIZE)
    
    # ===== JSON READING TESTS =====
    print("\n===== JSON READING TESTS =====")
    
    # Run performance test for the read_file function (unbuffered)
    time_bm_results_read_file_unbuffered = perftester.time_benchmark(
        perftester_read_file_unbuffered, Number=NUMBER, Repeat=REPEAT
    )
    memory_bm_results_read_file_unbuffered = perftester.memory_usage_benchmark(
        perftester_read_file_unbuffered
    )
    print_bmresults(
        "read_file_unbuffered", 
        time_bm_results_read_file_unbuffered, 
        memory_bm_results_read_file_unbuffered
    )
    
    # Run performance test for the read_file function (buffered)
    time_bm_results_read_file_buffered = perftester.time_benchmark(
        perftester_read_file_buffered, Number=NUMBER, Repeat=REPEAT
    )
    memory_bm_results_read_file_buffered = perftester.memory_usage_benchmark(
        perftester_read_file_buffered
    )
    print_bmresults(
        "read_file_buffered", 
        time_bm_results_read_file_buffered, 
        memory_bm_results_read_file_buffered
    )
    
    # ===== CSV READING TESTS =====
    print("\n===== CSV READING TESTS =====")
    
    # Run performance test for the read_csv_file function (unbuffered)
    time_bm_results_read_csv_unbuffered = perftester.time_benchmark(
        perftester_read_csv_unbuffered, Number=NUMBER, Repeat=REPEAT
    )
    memory_bm_results_read_csv_unbuffered = perftester.memory_usage_benchmark(
        perftester_read_csv_unbuffered
    )
    print_bmresults(
        "read_csv_unbuffered", 
        time_bm_results_read_csv_unbuffered, 
        memory_bm_results_read_csv_unbuffered
    )
    
    # Run performance test for the read_csv_file function (buffered)
    time_bm_results_read_csv_buffered = perftester.time_benchmark(
        perftester_read_csv_buffered, Number=NUMBER, Repeat=REPEAT
    )
    memory_bm_results_read_csv_buffered = perftester.memory_usage_benchmark(
        perftester_read_csv_buffered
    )
    print_bmresults(
        "read_csv_buffered", 
        time_bm_results_read_csv_buffered, 
        memory_bm_results_read_csv_buffered
    )
    
    # ===== JSON WRITING TESTS =====
    print("\n===== JSON WRITING TESTS =====")
    
    # Run performance test for the dict_to_json function (unbuffered)
    time_bm_results_dict_to_json_unbuffered = perftester.time_benchmark(
        perftester_dict_to_json_unbuffered, Number=NUMBER, Repeat=REPEAT
    )
    memory_bm_results_dict_to_json_unbuffered = perftester.memory_usage_benchmark(
        perftester_dict_to_json_unbuffered
    )
    print_bmresults(
        "dict_to_json_unbuffered", 
        time_bm_results_dict_to_json_unbuffered, 
        memory_bm_results_dict_to_json_unbuffered
    )
    
    # Run performance test for the dict_to_json function (buffered)
    time_bm_results_dict_to_json_buffered = perftester.time_benchmark(
        perftester_dict_to_json_buffered, Number=NUMBER, Repeat=REPEAT
    )
    memory_bm_results_dict_to_json_buffered = perftester.memory_usage_benchmark(
        perftester_dict_to_json_buffered
    )
    print_bmresults(
        "dict_to_json_buffered", 
        time_bm_results_dict_to_json_buffered, 
        memory_bm_results_dict_to_json_buffered
    )
    
    # ===== CSV WRITING TESTS =====
    print("\n===== CSV WRITING TESTS =====")
    
    # Run performance test for the dict_to_csv function (unbuffered)
    time_bm_results_dict_to_csv_unbuffered = perftester.time_benchmark(
        perftester_dict_to_csv_unbuffered, Number=NUMBER, Repeat=REPEAT
    )
    memory_bm_results_dict_to_csv_unbuffered = perftester.memory_usage_benchmark(
        perftester_dict_to_csv_unbuffered
    )
    print_bmresults(
        "dict_to_csv_unbuffered", 
        time_bm_results_dict_to_csv_unbuffered, 
        memory_bm_results_dict_to_csv_unbuffered
    )
    
    # Run performance test for the dict_to_csv function (buffered)
    time_bm_results_dict_to_csv_buffered = perftester.time_benchmark(
        perftester_dict_to_csv_buffered, Number=NUMBER, Repeat=REPEAT
    )
    memory_bm_results_dict_to_csv_buffered = perftester.memory_usage_benchmark(
        perftester_dict_to_csv_buffered
    )
    print_bmresults(
        "dict_to_csv_buffered", 
        time_bm_results_dict_to_csv_buffered, 
        memory_bm_results_dict_to_csv_buffered
    )
    
    # ===== FILTER AND PROCESS TESTS =====
    print("\n===== FILTER AND PROCESS TESTS =====")
    
    # Run performance test for the filter_and_process_data function
    time_bm_results_filter = perftester.time_benchmark(
        perftester_filter_and_process_data, Number=NUMBER, Repeat=REPEAT
    )
    memory_bm_results_filter = perftester.memory_usage_benchmark(
        perftester_filter_and_process_data
    )
    print_bmresults(
        "filter_and_process_data", 
        time_bm_results_filter, 
        memory_bm_results_filter
    )
    
    # ===== SUMMARY =====
    print("\n===== SUMMARY =====")
    print("JSON Reading:")
    print(f"  Unbuffered: {time_bm_results_read_file_unbuffered['mean']:.6f} s, {memory_bm_results_read_file_unbuffered['mean']:.2f} MB")
    print(f"  Buffered:   {time_bm_results_read_file_buffered['mean']:.6f} s, {memory_bm_results_read_file_buffered['mean']:.2f} MB")
    
    print("CSV Reading:")
    print(f"  Unbuffered: {time_bm_results_read_csv_unbuffered['mean']:.6f} s, {memory_bm_results_read_csv_unbuffered['mean']:.2f} MB")
    print(f"  Buffered:   {time_bm_results_read_csv_buffered['mean']:.6f} s, {memory_bm_results_read_csv_buffered['mean']:.2f} MB")
    
    print("JSON Writing:")
    print(f"  Unbuffered: {time_bm_results_dict_to_json_unbuffered['mean']:.6f} s, {memory_bm_results_dict_to_json_unbuffered['mean']:.2f} MB")
    print(f"  Buffered:   {time_bm_results_dict_to_json_buffered['mean']:.6f} s, {memory_bm_results_dict_to_json_buffered['mean']:.2f} MB")
    
    print("CSV Writing:")
    print(f"  Unbuffered: {time_bm_results_dict_to_csv_unbuffered['mean']:.6f} s, {memory_bm_results_dict_to_csv_unbuffered['mean']:.2f} MB")
    print(f"  Buffered:   {time_bm_results_dict_to_csv_buffered['mean']:.6f} s, {memory_bm_results_dict_to_csv_buffered['mean']:.2f} MB")
    
    print("Filter and Process:")
    print(f"  {time_bm_results_filter['mean']:.6f} s, {memory_bm_results_filter['mean']:.2f} MB")
    
    # Clean up output files
    if os.path.exists(CSV_FILENAME):
        os.remove(CSV_FILENAME)
    if os.path.exists(JSON_FILENAME):
        os.remove(JSON_FILENAME)
