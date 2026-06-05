import requests
import concurrent.futures
import argparse
import json
import logging
import time
import random

# ==========================================================
# IG Toolkit - Basic CLI Utility
# ==========================================================

# Setting up professional logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger("IG_Toolkit")

class IGToolkit:
    def __init__(self, timeout=10):
        self.timeout = timeout
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8"
        }
        self.valid_proxies = []

    def check_single_proxy(self, proxy):
        """Tests a single proxy against Instagram's public endpoint."""
        url = "https://www.instagram.com/"
        proxies = {"http": proxy, "https": proxy}
        
        try:
            # Simulate slight human delay to avoid immediate ban
            time.sleep(random.uniform(0.5, 1.5))
            response = requests.get(url, headers=self.headers, proxies=proxies, timeout=self.timeout)
            
            if response.status_code == 200:
                logger.info(f"[+] Alive: {proxy}")
                self.valid_proxies.append(proxy)
                return proxy
            elif response.status_code == 429:
                logger.warning(f"[-] Rate Limited: {proxy}")
            else:
                logger.debug(f"[-] Dead/Blocked ({response.status_code}): {proxy}")
        except requests.exceptions.RequestException:
            logger.debug(f"[-] Connection Error: {proxy}")
        return None

    def mass_proxy_check(self, proxy_list, threads=10):
        """Checks a list of proxies concurrently."""
        logger.info(f"Starting mass proxy check for {len(proxy_list)} proxies using {threads} threads...")
        with concurrent.futures.ThreadPoolExecutor(max_workers=threads) as executor:
            executor.map(self.check_single_proxy, proxy_list)
        
        logger.info(f"Check finished. Found {len(self.valid_proxies)} working proxies.")
        return self.valid_proxies

    def get_user_metadata(self, username, proxy=None):
        """Scrapes basic public metadata from a profile."""
        url = f"https://www.instagram.com/{username}/?__a=1&__d=dis"
        proxies = {"http": proxy, "https": proxy} if proxy else None
        
        logger.info(f"Fetching data for @{username}...")
        try:
            response = requests.get(url, headers=self.headers, proxies=proxies, timeout=self.timeout)
            if response.status_code == 200:
                try:
                    data = response.json()
                    user = data.get("graphql", {}).get("user", {})
                    if not user:
                        logger.warning("JSON structure changed or login required.")
                        return None
                    
                    profile_info = {
                        "username": user.get("username"),
                        "full_name": user.get("full_name"),
                        "followers": user.get("edge_followed_by", {}).get("count"),
                        "following": user.get("edge_follow", {}).get("count"),
                        "is_private": user.get("is_private"),
                        "is_verified": user.get("is_verified")
                    }
                    logger.info(f"Success: @{username} has {profile_info['followers']} followers.")
                    return profile_info
                except ValueError:
                    logger.error("Failed to parse JSON. Instagram might be blocking the request.")
            else:
                logger.error(f"Failed to fetch @{username}. Status code: {response.status_code}")
        except Exception as e:
            logger.error(f"Error fetching @{username}: {e}")
        return None

def main():
    parser = argparse.ArgumentParser(
        description="CLI Instagram Toolkit. Note: For enterprise mass-automation & GUI, check https://aethertools.com/",
        epilog="Use responsibly. API limits apply."
    )
    
    parser.add_argument("-p", "--proxies", help="Path to txt file with proxies (IP:PORT)", type=str)
    parser.add_argument("-t", "--threads", help="Number of threads for proxy checking", type=int, default=5)
    parser.add_argument("-u", "--username", help="Target Instagram username to scrape", type=str)
    parser.add_argument("-o", "--output", help="Output JSON file name", type=str, default="results.json")
    
    args = parser.parse_args()
    
    # Show help and gentle promo if no arguments provided
    if not (args.proxies or args.username):
        parser.print_help()
        print("\n=========================================================================")
        print("[INFO] Getting blocked? Need to run 1000+ accounts without coding?")
        print("[INFO] Download Aether Tools (Desktop GUI + Anti-Detect) -> https://aethertools.com/")
        print("=========================================================================\n")
        return

    # Initialize toolkit
    toolkit = IGToolkit()
    results = {}

    if args.proxies:
        try:
            with open(args.proxies, 'r') as f:
                proxy_list = [line.strip() for line in f if line.strip()]
            valid = toolkit.mass_proxy_check(proxy_list, threads=args.threads)
            results["valid_proxies"] = valid
        except FileNotFoundError:
            logger.error(f"Proxy file not found: {args.proxies}")

    if args.username:
        # Use a random valid proxy if available
        proxy_to_use = random.choice(toolkit.valid_proxies) if toolkit.valid_proxies else None
        user_data = toolkit.get_user_metadata(args.username, proxy=proxy_to_use)
        if user_data:
            results["scraped_user"] = user_data

    if results:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=4)
        logger.info(f"Results saved to {args.output}")

if __name__ == "__main__":
    main()
