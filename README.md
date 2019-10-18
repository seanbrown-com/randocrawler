# randocrawler
Multithreaded Random Website Crawler in Python using Google and Seleneum

A multithread capable website crawler that utilizes random word generator and google search to obtain random URLs to visit.

Usage:
rand_crawl.py 1 2 3
1: Number of threads to create (for best performance, 1 less than the number of threads available on the system)
2: Number of searches to perform
3: Number of top hits to visit from the result of the random google search

Output:
CSV with the following format:
URL, desktop browser results, mobile browser results
