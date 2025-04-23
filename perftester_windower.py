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