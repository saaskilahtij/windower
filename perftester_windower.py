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

    # JSON file used for testing, replace with the desired test file.
    TEST_FILE = "can_dump_orig.json"
    CSV_FILENAME = "output.csv"
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

    def perftester_read_file():
        """Tests the performance and memory usage of windower.read_file()"""
        return windower.read_file(TEST_FILE)

    def perftester_dict_to_csv():
        """Tests the performance and memory usage of windower.json_to_csv()"""
        #json_data = windower.read_file(TEST_FILE)  # Read JSON file
        #pylint:disable=no-value-for-parameter
        return windower.dict_to_csv(json_data, WINDOW_LENGTH, CSV_FILENAME)  # Convert to CSV

    def perftester_filter_and_process_data():
        """Tests the performance and memory usage of windower.filter_and_process_data()"""
        return windower.filter_and_process_data(json_data, ecu_name=["brake"])

    # Run performance test for the read_file function
    time_bm_results_read_file = perftester.time_benchmark(perftester_read_file, Number=2, Repeat=2)

    # Run memory usage test for the read_file function
    memory_bm_results_read_file = perftester.memory_usage_benchmark(perftester_read_file)

    # Run time benchmark test for the dict_to_csv function. The function test is not working yet.
    #time_bm_results_dict_to_csv = perftester.time_benchmark(
    #    perftester_dict_to_csv, Number=2, Repeat=2
    #)

    # Run memory usage test for the dict_to_csv function
    #memory_bm_results_dict_to_csv = perftester.memory_usage_benchmark(perftester_dict_to_csv)

    # Run performance test for the filter_and_process_data function
    # Read the data before testing to ensure the benchmark only measures the performance
    # of the filter_and_process_data function, not the file reading process.
    json_data = windower.read_file(TEST_FILE)
    time_bm_results_filter = perftester.time_benchmark(
        perftester_filter_and_process_data, Number=2, Repeat=2
    )

    # Run memory usage test for the filter_and_process_data function
    memory_bm_results_filter = perftester.memory_usage_benchmark(perftester_filter_and_process_data)

    # Print results for the read_file function
    print_bmresults(
        perftester_read_file.__name__, time_bm_results_read_file, memory_bm_results_read_file
    )

    # Print results for the dict_to_csv function
    #print_bmresults(
    #    perftester_dict_to_csv.__name__, time_bm_results_dict_to_csv, memory_bm_results_dict_to_csv
    #)

    # Print results for the filter_and_process_data function
    print_bmresults(
        perftester_filter_and_process_data.__name__,
         time_bm_results_filter,
         memory_bm_results_filter
    )
