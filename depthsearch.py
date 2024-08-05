import sys
import requests
from bs4 import BeautifulSoup
import os
import time
import random
from fake_useragent import UserAgent
import platform
import psutil
from colorama import Fore, Style, init

# Initialize colorama
init(autoreset=True)

sys.dont_write_bytecode = True


class ConsoleConfig:
    # Console colors and styles
    BOLD = Style.BRIGHT
    END = Style.RESET_ALL


class Config:
    ERROR_CODE = -1
    SUCCESS_CODE = 0
    MIN_DATA_RETRIEVE_LENGTH = 1
    USE_PROXY = False

    descriptions = []
    urls = []
    titles = []

    SEARCH_ENGINE_URL = "https://ahmia.fi/search/?q="
    PROXY_API_URLS = [
        "https://api.proxyscrape.com/v2/?request=displayproxies&protocol=http&timeout=10000&country=all&ssl=all&anonymity=elite",
        "https://www.proxy-list.download/api/v1/get?type=https",
        "https://www.proxy-list.download/api/v1/get?type=http"
    ]


class PlatformUtils:
    @staticmethod
    def get_os_descriptor():
        os_name = platform.system().lower()
        os_version = platform.version()
        os_release = platform.release()
        machine = platform.machine()
        processor = platform.processor()

        print(f"{ConsoleConfig.BOLD}{Fore.WHITE}Operating System:{Fore.GREEN} {os_name.capitalize()}{ConsoleConfig.END}")
        print(f"{ConsoleConfig.BOLD}{Fore.WHITE}OS Version:{Fore.WHITE} {os_version}{ConsoleConfig.END}")
        print(f"{ConsoleConfig.BOLD}{Fore.WHITE}OS Release:{Fore.WHITE} {os_release}{ConsoleConfig.END}")
        print(f"{ConsoleConfig.BOLD}{Fore.WHITE}Machine:{Fore.WHITE} {machine}{ConsoleConfig.END}")
        print(f"{ConsoleConfig.BOLD}{Fore.WHITE}Processor:{Fore.WHITE} {processor}{ConsoleConfig.END}")

        try:
            mem_info = psutil.virtual_memory()
            print(f"{ConsoleConfig.BOLD}{Fore.WHITE}Total Memory:{Fore.WHITE} {mem_info.total // (1024 ** 2)} MB{ConsoleConfig.END}")

            cpu_freq = psutil.cpu_freq()
            if cpu_freq:
                print(f"{ConsoleConfig.BOLD}{Fore.WHITE}CPU Frequency:{Fore.WHITE} {cpu_freq.current} MHz{ConsoleConfig.END}")
            else:
                print(f"{ConsoleConfig.BOLD}{Fore.WHITE}CPU Frequency information not available{ConsoleConfig.END}")

            num_cores = psutil.cpu_count(logical=True)
            print(f"{ConsoleConfig.BOLD}{Fore.WHITE}Number of Cores:{Fore.WHITE} {num_cores}{ConsoleConfig.END}")

        except Exception as e:
            print(f"{ConsoleConfig.BOLD}{Fore.RED}Unable to retrieve some system information: {e}{ConsoleConfig.END}")

    @staticmethod
    def clear_screen():
        os_name = platform.system().lower()
        if os_name in ["linux", "darwin"]:
            os.system('clear')
        elif os_name == "windows":
            os.system('cls')
        else:
            print("[!] Cannot clear screen. Unsupported OS.")


class ProxyManager:
    def __init__(self):
        self.proxies = []

    def update_proxies(self):
        all_proxies = set()
        for url in Config.PROXY_API_URLS:
            try:
                response = requests.get(url)
                response.raise_for_status()  # Check for HTTP errors
                all_proxies.update(line.strip() for line in response.text.splitlines() if line.strip())
            except requests.RequestException as e:
                print(f"[!] Error fetching proxies from {url}: {e}")
        self.proxies = ["http://" + proxy for proxy in all_proxies]

    def get_random_proxy(self):
        return random.choice(self.proxies) if self.proxies else None


class DepthSearch:
    def __init__(self):
        self.user_agent = UserAgent()
        self.session = requests.Session()  # Use session for persistent connections
        self.proxy_manager = ProxyManager()

    def search(self, query, amount):
        headers = {'User-Agent': self.user_agent.random}

        if Config.USE_PROXY:
            self.proxy_manager.update_proxies()  # Update proxies before starting the search

        proxies_used = 0
        results_found = 0

        while results_found < amount:
            if Config.USE_PROXY:
                proxy = self.proxy_manager.get_random_proxy()
                if proxy:
                    print(f"{ConsoleConfig.BOLD}{Fore.MAGENTA}Using Proxy:{Fore.CYAN} {proxy}{ConsoleConfig.END}\n")
                    self.session.proxies.update({"http": proxy})

            try:
                response = self.session.get(Config.SEARCH_ENGINE_URL + query, headers=headers, timeout=10)
                response.raise_for_status()  # Ensure we handle HTTP errors

                soup = BeautifulSoup(response.content, 'html.parser')
                results = soup.find(id='ahmiaResultsPage')
                result_items = results.find_all('li', class_='result')

                titles = [item.find('p').text if item.find('p') else None for item in result_items]
                urls = [item.find('cite').text if item.find('cite') else None for item in result_items]
                descriptions = [item.find('p').text if item.find('p') else None for item in result_items]

                if len(urls) >= Config.MIN_DATA_RETRIEVE_LENGTH:
                    for i in range(len(urls)):
                        url = urls[i]
                        title = titles[i]
                        description = descriptions[i]

                        output = f"{ConsoleConfig.BOLD}{Fore.LIGHTGREEN_EX}URL:{Fore.WHITE} {url}\n"
                        if title:
                            output += f"\t{ConsoleConfig.BOLD}Title:{Fore.LIGHTBLUE_EX} {title}\n"
                        if description:
                            output += f"\t{ConsoleConfig.BOLD}Description:{Fore.LIGHTCYAN_EX} {description}\n"
                        output += ConsoleConfig.END
                        print(output)
                        results_found += 1
                        if results_found >= amount:
                            break
                else:
                    print(f"{ConsoleConfig.BOLD}{Fore.LIGHTRED_EX}No results found.{ConsoleConfig.END}")

                # Mimic human behavior with random delays between requests
                time.sleep(random.uniform(1, 3))
                
                proxies_used += 1
                if Config.USE_PROXY and proxies_used >= len(self.proxy_manager.proxies):
                    print(f"{ConsoleConfig.BOLD}{Fore.LIGHTRED_EX}Ran out of proxies.{ConsoleConfig.END}")
                    break

            except requests.RequestException as e:
                print(f"{ConsoleConfig.BOLD}{Fore.LIGHTRED_EX}Request failed: {e}{ConsoleConfig.END}")
                if Config.USE_PROXY:
                    self.proxy_manager.update_proxies()  # Update proxies on failure

        if results_found < amount:
            print(f"{ConsoleConfig.BOLD}{Fore.LIGHTRED_EX}Not enough results found after using all proxies.{ConsoleConfig.END}")


def main():
    PlatformUtils.clear_screen()
    PlatformUtils.get_os_descriptor()
    time.sleep(1.3)

    # Get user inputs
    query = input(f"n/{ConsoleConfig.BOLD}Enter the query: {ConsoleConfig.END}").strip()
    amount_str = input(f"{ConsoleConfig.BOLD}Enter the number of results to retrieve (default: 25): {ConsoleConfig.END}").strip()
    use_proxy_str = input(f"{ConsoleConfig.BOLD}Use proxy for increased anonymity? (y/n): {ConsoleConfig.END}").strip().lower()

    # Set defaults
    amount = 10
    use_proxy = use_proxy_str in ['yes', 'y']

    # Validate amount
    if amount_str.isdigit():
        amount = int(amount_str)

    if query:
        print(f"{ConsoleConfig.BOLD}Searching For:{Fore.GREEN} {query} and showing {amount} results...\n{ConsoleConfig.END}")
        Config.USE_PROXY = use_proxy
        DepthSearch().search(query, amount)
    else:
        print(f"{ConsoleConfig.BOLD}{Fore.LIGHTRED_EX}No query arguments were passed. Please supply a query to search.{ConsoleConfig.END}")


if __name__ == "__main__":
    main()
