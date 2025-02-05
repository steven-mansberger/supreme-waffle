#!/usr/bin/python

from ansible.module_utils.basic import AnsibleModule
import ipaddress
import requests
import json

def get_access_token(module):
    """Helper function to obtain Azure access token."""
    token_url = f"https://login.microsoftonline.com/{module.params['tenant_id']}/oauth2/v2.0/token"
    token_data = {
        "grant_type": "client_credentials",
        "client_id": module.params['client_id'],
        "client_secret": module.params['client_secret'],
        "scope": "https://management.azure.com/.default"
    }
   
    try:
        token_response = requests.post(token_url, data=token_data)
        token_response.raise_for_status()
        return token_response.json()['access_token']
    except requests.exceptions.RequestException as e:
        module.fail_json(msg=f"Failed to obtain access token: {str(e)}")
    except json.JSONDecodeError as e:
        module.fail_json(msg=f"Failed to parse token response: {str(e)}")

def get_first_vnet(module, headers):
    """Get the first VNet from the subscription if vnet_name is not provided."""
    try:
        url = f"https://management.azure.com/subscriptions/{module.params['subscription_id']}/providers/Microsoft.Network/virtualNetworks?api-version=2021-05-01"
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        try:
            response_json = response.json()
        except json.JSONDecodeError as e:
            module.fail_json(msg=f"Failed to parse API response as JSON: {str(e)}")
        
        vnets = response_json.get('value', [])
        if not vnets:
            module.fail_json(msg="No VNets found in subscription")
            
        vnet = vnets[0]
        vnet_name = vnet.get('name')
        vnet_id = vnet.get('id')
        
        if not vnet_name or not vnet_id:
            module.fail_json(msg=f"VNet data missing required fields (name or id). VNet data: {vnet}")
            
        return vnet_name, vnet_id
        
    except requests.exceptions.RequestException as e:
        module.fail_json(msg=f"Failed to get VNet list: {str(e)}")
    except Exception as e:
        module.fail_json(msg=f"Error retrieving VNet information: {str(e)}")

def get_vnet_details(module, vnet_id, headers):
    """Get details of a specific VNet."""
    try:
        if not vnet_id.startswith('/'):
            vnet_id = f"/{vnet_id}"
        url = f"https://management.azure.com{vnet_id}?api-version=2021-05-01"
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        vnet_data = response.json()
        
        # Validate VNet data structure using .get()
        properties = vnet_data.get('properties', {})
        if not properties:
            module.fail_json(msg="VNet data missing 'properties' field")
            
        subnets = properties.get('subnets', [])
        address_space = properties.get('addressSpace', {})
        address_prefixes = address_space.get('addressPrefixes', [])
        
        if not address_prefixes:
            module.fail_json(msg="VNet data missing 'addressPrefixes' field")
            
        vnet_data['properties']['subnets'] = subnets
        vnet_data['properties']['addressSpace']['addressPrefixes'] = address_prefixes
            
        return vnet_data
        
    except requests.exceptions.RequestException as e:
        module.fail_json(msg=f"Failed to get VNet details: {str(e)}")
    except Exception as e:
        module.fail_json(msg=f"Error retrieving VNet details: {str(e)}")

def validate_subnet(module, new_subnet_cidr, existing_subnets, vnet_address_space, vnet_name):
    """Validate if the new subnet CIDR can be added to the VNet."""
    try:
        new_network = ipaddress.ip_network(new_subnet_cidr)
    except ValueError as e:
        module.fail_json(
            msg=f"Invalid CIDR format: {new_subnet_cidr}. Please provide a valid CIDR notation (e.g., '10.0.0.0/24'). Error: {str(e)}"
        )

    # Check if subnet fits within VNet address space
    subnet_fits = False
    try:
        for address_prefix in vnet_address_space:
            try:
                vnet_network = ipaddress.ip_network(address_prefix)
                if new_network.subnet_of(vnet_network):
                    subnet_fits = True
                    break
            except ValueError as e:
                module.fail_json(
                    msg=f"Invalid VNet address space format: {address_prefix}. Error: {str(e)}",
                    vnet_name=vnet_name
                )
    except Exception as e:
        module.fail_json(
            msg=f"Error validating subnet fit: {str(e)}",
            vnet_name=vnet_name,
            subnet_cidr=new_subnet_cidr,
            vnet_address_space=vnet_address_space
        )
    
    if not subnet_fits:
        module.fail_json(
            msg=f"Subnet {new_subnet_cidr} does not fit within VNet '{vnet_name}' address space {vnet_address_space}",
            vnet_name=vnet_name,
            subnet_cidr=new_subnet_cidr,
            vnet_address_space=vnet_address_space
        )

    # Check for overlap with existing subnets
    try:
        for subnet in existing_subnets:
            if 'properties' not in subnet or 'addressPrefix' not in subnet['properties']:
                module.fail_json(msg=f"Invalid subnet data structure for subnet {subnet.get('name', 'unknown')}")
            
            try:
                existing_network = ipaddress.ip_network(subnet['properties']['addressPrefix'])
                if new_network.overlaps(existing_network):
                    module.fail_json(
                        msg=f"Subnet {new_subnet_cidr} overlaps with existing subnet '{subnet['name']}' ({subnet['properties']['addressPrefix']}) in VNet '{vnet_name}'",
                        vnet_name=vnet_name,
                        subnet_cidr=new_subnet_cidr,
                        overlapping_subnet=subnet['name'],
                        overlapping_subnet_cidr=subnet['properties']['addressPrefix']
                    )
            except ValueError as e:
                module.fail_json(
                    msg=f"Invalid existing subnet CIDR format: {subnet['properties'].get('addressPrefix', 'unknown')} for subnet {subnet.get('name', 'unknown')}. Error: {str(e)}"
                )
    except Exception as e:
        module.fail_json(
            msg=f"Error checking subnet overlap: {str(e)}",
            vnet_name=vnet_name,
            subnet_cidr=new_subnet_cidr
        )

    return True, f"Subnet {new_subnet_cidr} can be added to VNet '{vnet_name}' (address space: {', '.join(vnet_address_space)})"

def main():
    module = AnsibleModule(
        argument_spec=dict(
            subscription_id=dict(type='str', required=True),
            new_subnet_cidr=dict(type='str', required=True),
            vnet_name=dict(type='str', required=False),
            client_id=dict(type='str', required=True, no_log=True),
            client_secret=dict(type='str', required=True, no_log=True),
            tenant_id=dict(type='str', required=True)
        )
    )

    try:
        # Get authentication token
        token = get_access_token(module)
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }

        # Get VNet details
        if module.params['vnet_name']:
            # Get specific VNet ID first
            url = f"https://management.azure.com/subscriptions/{module.params['subscription_id']}/providers/Microsoft.Network/virtualNetworks?api-version=2021-05-01"
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            vnets = response.json()['value']
            vnet_id = next((v['id'] for v in vnets if v['name'] == module.params['vnet_name']), None)
            if not vnet_id:
                module.fail_json(msg=f"VNet {module.params['vnet_name']} not found")
            vnet_name = module.params['vnet_name']
        else:
            vnet_name, vnet_id = get_first_vnet(module, headers)
            module.warn(f"No VNet name provided; using the first VNet found: '{vnet_name}'.")

        # Get VNet details
        vnet_details = get_vnet_details(module, vnet_id, headers)
        existing_subnets = vnet_details['properties']['subnets']
        vnet_address_space = vnet_details['properties']['addressSpace']['addressPrefixes']

        # Validate new subnet
        valid, message = validate_subnet(
            module,
            module.params['new_subnet_cidr'],
            existing_subnets,
            vnet_address_space,
            vnet_name
        )

        result = {
            'changed': False,
            'vnet_name': vnet_name,
            'valid': valid,
            'message': message,
            'vnet_address_space': vnet_address_space,
            'subnet_cidr': module.params['new_subnet_cidr'],
            'existing_subnets': [
                {
                    'name': subnet['name'],
                    'address_prefix': subnet['properties']['addressPrefix']
                }
                for subnet in existing_subnets
            ]
        }
        
        module.exit_json(**result)

    except Exception as e:
        module.fail_json(msg=f"Error: {str(e)}")

if __name__ == '__main__':
    main()