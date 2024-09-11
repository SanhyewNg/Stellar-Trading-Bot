import yaml
import requests
import logging

# Set up logging configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def load_config(config_path):
    with open(config_path, 'r') as file:
        config = yaml.safe_load(file)
    return config


def get_usdc_price_and_change():
    try:
        url = f"https://api.coingecko.com/api/v3/simple/price?ids=usd-coin&vs_currencies=usd&include_24hr_change=true"
        response = requests.get(url).json()
        print(response)
        
        price = response['usd-coin']['usd']
        change_24h = response['usd-coin']['usd_24h_change']
        
        logging.info(f"Fetched price for usd-coin: {price} USD, 24h change: {change_24h}%")
        return price, change_24h
    except Exception as e:
        logging.error(f"Error fetching price for usd-coin: {e}")
        return 0.0, 0.0
