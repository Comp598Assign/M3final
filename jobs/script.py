#Code referenced from TA Alek Bedard
import requests
import time

ip_to_curl = ""

def curl_loop(iterations, gap_time):
    while(iterations > 0):
        requests.get(ip_to_curl)
        time.sleep(gap_time)
        iterations = iterations - 1

def the_input():
    while True:
        iterations = input("num of curling?\n")
        gap_time = input("num of delay>\n")
        curl_loop(int(iterations), float(gap_time))

if __name__ == "__main__":
    the_input()

