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
# Placing the code under main made it work.

if __name__ == "__main__":
    import perftester
    import windower

    # JSON file used for testing, replace with the desired test file.
    TEST_FILE = "test.json"

    def print_bmresults(function_name, time_results, memory_results):
        """Helper function to print time and memory benchmark results."""
        print(f"\n{function_name} time benchmark:")
        print(f"  Min: {time_results['min']:.6f} s")
        print(f"  Max: {time_results['max']:.6f} s")
        print(f"  Mean: {time_results['mean']:.6f} s")

        print(f"\n{function_name} memory usage benchmark:")
        print(f"  Mean memory usage: {memory_results['mean']:.2f} MB")
        print(f"  Max memory usage: {memory_results['max']:.2f} MB")

    def perftester_read_file():
        """Tests the performance and memory usage of windower.read_file()"""
        return windower.read_file(TEST_FILE)

    def perftester_json_to_csv():
        """Tests the performance and memory usage of windower.json_to_csv()"""
        json_data = windower.read_file(TEST_FILE)  # Read JSON file
        csv_filename = "output.csv"  # Specify the output CSV file name
        return windower.json_to_csv(json_data, csv_filename)  # Convert to CSV

    # Run performance test for the read_file fuction
    # You can change arguments Number and Repeat
    time_bm_results_read_file = perftester.time_benchmark(perftester_read_file, Number=2, Repeat=2)
    # Use the following line only for small files with a low number of repetitions
    # if you want to see individual measurements.
    #print("Windower read_file time test result:", time_benchmark_results)

    # Run memory usage test for the read_file function
    memory_bm_results_read_file = perftester.memory_usage_benchmark(perftester_read_file)
    # Use the following line only for small files with a low number of repetitions
    # if you want to see individual measurements.
    #print("Windower read_file memory usage results:", memory_benchmark_results)

    # Run time benchmark test for the json_to_csv function
    # Uncomment next line if you want to test the json_to_csv function
    #time_benchmark_results_csv = perftester.time_benchmark(perftester_json_to_csv,
    #Number=1, Repeat=1)

    # Run memory usage test for the json_to_csv function
    # Uncomment next line if you want to test the json_to_csv function
    # memory_benchmark_results_csv = perftester.memory_usage_benchmark(perftester_json_to_csv)
    # Print results for the read_file function
    print_bmresults(perftester_read_file.__name__,
    time_bm_results_read_file, memory_bm_results_read_file)
    # Print results for the json_to_csv function
    # Uncomment following lines if you want to test the json_to_csv function
    #print_bmresults(perftester_json_to_csv.__name__,
    #time_benchmark_results_csv, memory_benchmark_results_csv)
