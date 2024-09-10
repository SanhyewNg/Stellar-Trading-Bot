import requests

def get_issuer_details(issuer_account_id):
    # Replace with the Horizon server URL you're using
    horizon_url = 'https://horizon.stellar.org'
    
    # Endpoint to fetch account details
    response = requests.get(f'{horizon_url}/accounts/{issuer_account_id}')
    
    if response.status_code == 200:
        account_data = response.json()
        return account_data
    else:
        return None

# Replace with the actual issuer account ID
issuer_account_id = 'GA5ZSEJYB37JRC5AVCIA5MOP4RHTM335X2KGX3IHOJAPP5RE34K4KZVN'

issuer_details = get_issuer_details(issuer_account_id)

if issuer_details:
    print(f"Account ID: {issuer_details['id']}")
    print(f"Account Sequence: {issuer_details['sequence']}")
    # Add other details you need, but note this won't give you 'centre.io' directly
else:
    print("Issuer details not found")
