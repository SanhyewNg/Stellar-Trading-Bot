from stellar_sdk import Server

# def list_assets(server_url):
#     server = Server(server_url)
#     assets = server.assets().limit(200).call()  # Adjust limit as needed
#     return assets['_embedded']['records']

# # Example usage:
# server_url = "https://horizon.stellar.org"  # or mainnet URL
# assets = list_assets(server_url)
# for asset in assets:
#     # print(f"Asset Code: {asset['asset_code']}, Issuer: {asset['asset_issuer']}")
#     print(asset)


from stellar_sdk import Server

def get_asset_details_by_code(server_url, asset_code):
    """
    Fetch details of a specific asset by code using `for_code`.
    """
    server = Server(server_url)
    
    try:
        # Search for assets by code
        assets_call = server.assets().for_code(asset_code).call()
        
        if assets_call['_embedded']['records']:
            for asset_detail in assets_call['_embedded']['records']:
                # print(f"Asset Code: {asset_detail['asset_code']}, Issuer: {asset_detail['asset_issuer']}")
                print(asset_detail)
            return assets_call['_embedded']['records']  # Return the list of asset details
        else:
            print(f"No assets found with code {asset_code}.")
            return None

    except Exception as e:
        print(f"Error fetching asset details: {e}")
        return None

# Example usage:
# server_url = "https://horizon-testnet.stellar.org"  # testnet 
server_url = "https://horizon.stellar.org" # mainnet
asset_code = "AQUA"  # The asset code you are searching for
# asset_code = "USDC"  # The asset code you are searching for
# asset_code = "BTC"  # The asset code you are searching for

details = get_asset_details_by_code(server_url, asset_code)

# if details:
#     for detail in details:
#         print(f"Found Asset: Code={detail['asset_code']}, Issuer={detail['asset_issuer']}")
# else:
#     print(f"Asset {asset_code} not found.")
