#!/usr/bin/env python3

from ansible.module_utils.basic import AnsibleModule
import ipaddress
import requests
import json
import hcl2
import os
from pathlib import Path
import time

# ---------------------------
# Azure API helper functions
# ---------------------------

def get_access_token(module):
    """Obtain Azure access token."""
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
    """
    Retrieve the first VNet from the subscription.
    Used when no vnet_name is provided.
    """
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


def get_vnet_by_name(module, target_vnet_name, headers):
    """
    Retrieve a VNet with the specified name by listing VNets in the subscription.
    """
    try:
        url = f"https://management.azure.com/subscriptions/{module.params['subscription_id']}/providers/Microsoft.Network/virtualNetworks?api-version=2021-05-01"
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        try:
            response_json = response.json()
        except json.JSONDecodeError as e:
            module.fail_json(msg=f"Failed to parse API response as JSON: {str(e)}")
        
        vnets = response_json.get('value', [])
        for v in vnets:
            if v.get('name') == target_vnet_name:
                vnet_id = v.get('id')
                if not vnet_id:
                    module.fail_json(msg=f"VNet '{target_vnet_name}' missing id field.")
                return target_vnet_name, vnet_id

        module.fail_json(msg=f"VNet with name '{target_vnet_name}' not found")
        
    except requests.exceptions.RequestException as e:
        module.fail_json(msg=f"Failed to get VNet list: {str(e)}")
    except Exception as e:
        module.fail_json(msg=f"Error retrieving VNet information: {str(e)}")


def get_vnet_details(module, vnet_id, headers):
    """Retrieve details of a specific VNet."""
    try:
        # Ensure vnet_id starts with a slash
        if not vnet_id.startswith('/'):
            vnet_id = f"/{vnet_id}"
        url = f"https://management.azure.com{vnet_id}?api-version=2021-05-01"
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        vnet_data = response.json()
        
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
    """
    Validate that the new subnet CIDR:
      1. Is valid CIDR notation.
      2. Fits within one of the VNet's address spaces.
      3. Does not overlap any existing subnet.
    """
    try:
        new_network = ipaddress.ip_network(new_subnet_cidr)
    except ValueError as e:
        module.fail_json(
            msg=f"Invalid CIDR format: {new_subnet_cidr}. Please provide a valid CIDR (e.g., '10.0.0.0/24'). Error: {str(e)}"
        )

    # Check if the subnet is within any of the VNet's address prefixes.
    subnet_fits = False
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
    
    if not subnet_fits:
        module.fail_json(
            msg=f"Subnet {new_subnet_cidr} does not fit within VNet '{vnet_name}' address space {vnet_address_space}",
            vnet_name=vnet_name,
            subnet_cidr=new_subnet_cidr,
            vnet_address_space=vnet_address_space
        )

    # Check for overlap with existing subnets.
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
                msg=f"Invalid existing subnet CIDR: {subnet['properties'].get('addressPrefix', 'unknown')} for subnet {subnet.get('name', 'unknown')}. Error: {str(e)}"
            )

    return True, f"Subnet {new_subnet_cidr} can be added to VNet '{vnet_name}' (address space: {', '.join(vnet_address_space)})"

# ---------------------------
# Terraform file helper functions
# ---------------------------

def calculate_new_bits(vnet_cidr, subnet_cidr):
    """
    Calculate the difference between the subnet CIDR prefix length and the VNet's CIDR prefix length.
    """
    vnet_prefix = ipaddress.ip_network(vnet_cidr).prefixlen
    subnet_prefix = ipaddress.ip_network(subnet_cidr).prefixlen
    return subnet_prefix - vnet_prefix


def find_target_module(terraform_config, vnet_name):
    """
    Search for the module in the Terraform configuration that has the matching vnet_name.
    The configuration is assumed to have a top-level "module" block.
    """
    modules = terraform_config.get('module', [])
    # When parsed from HCL2 the modules list is a list of dicts.
    for mod in modules:
        for name, config in mod.items():
            if config.get('vnet_name') == vnet_name:
                return config
    return None


def update_terraform_file(module, terraform_config, vnet_name, vnet_address, subnet_name, new_subnet_cidr, delegation_name):
    """
    Update the Terraform configuration data structure by adding the new subnet.
    """
    target_config = find_target_module(terraform_config, vnet_name)
    if not target_config:
        module.fail_json(msg=f"Module with vnet_name '{vnet_name}' not found in Terraform configuration")
    
    subnets = target_config.get('subnets', [])
    if not isinstance(subnets, list):
        module.fail_json(msg="Subnets configuration is invalid in Terraform module")

    new_bits = calculate_new_bits(vnet_address, new_subnet_cidr)

    # Build the new subnet dictionary.
    new_subnet = {
        'name': subnet_name,
        'new_bits': new_bits,
        'aviatrix_subnet': False
    }
    if delegation_name:
        new_subnet['delegation'] = [{
            'name': 'delegation',
            'service_delegation': {
                'name': delegation_name,
                'actions': ["Microsoft.Network/virtualNetworks/subnets/action"]
            }
        }]

    subnets.append(new_subnet)
    # Sort subnets by new_bits in descending order.
    subnets.sort(key=lambda x: x['new_bits'], reverse=True)
    target_config['subnets'] = subnets

    return terraform_config

# ---------------------------
# Main Module Logic
# ---------------------------

def main():
    module = AnsibleModule(
        argument_spec=dict(
            # Azure / validation parameters
            subscription_id=dict(type='str', required=True),
            new_subnet_cidr=dict(type='str', required=True),
            vnet_name=dict(type='str', required=False, default=None),
            client_id=dict(type='str', required=True, no_log=True),
            client_secret=dict(type='str', required=True, no_log=True),
            tenant_id=dict(type='str', required=True),
            # Terraform file update parameters
            file_path=dict(type='path', required=True),
            subnet_name=dict(type='str', required=True),
            delegation_name=dict(type='str', required=False, default=None)
        ),
        supports_check_mode=False
    )

    # Authenticate with Azure.
    token = get_access_token(module)
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }

    # Determine the VNet to update.
    if module.params['vnet_name']:
        # Look up the VNet by name.
        vnet_name, vnet_id = get_vnet_by_name(module, module.params['vnet_name'], headers)
    else:
        # If not provided, use the first VNet in the subscription.
        vnet_name, vnet_id = get_first_vnet(module, headers)

    # Get details of the chosen VNet.
    vnet_details = get_vnet_details(module, vnet_id, headers)
    existing_subnets = vnet_details['properties']['subnets']
    vnet_address_space = vnet_details['properties']['addressSpace']['addressPrefixes']

    # Validate the new subnet against the VNet.
    valid, validation_message = validate_subnet(
        module,
        module.params['new_subnet_cidr'],
        existing_subnets,
        vnet_address_space,
        vnet_name
    )

    # At this point, validation passed.
    # For Terraform update we need a single VNet CIDR.
    # Here we use the first address prefix from the VNet.
    vnet_address = vnet_address_space[0]

    # Now update the Terraform configuration file.
    file_path = module.params['file_path']
    original_path = Path(file_path)
    is_json = original_path.suffix == '.json'
    
    try:
        with open(file_path, 'r') as f:
            content = f.read()
    except Exception as e:
        module.fail_json(msg=f"Failed to read Terraform file {file_path}: {str(e)}")

    # Parse the file based on its type.
    try:
        if is_json:
            terraform_config = json.loads(content)
        else:
            terraform_config = hcl2.loads(content)
    except Exception as e:
        module.fail_json(msg=f"Failed to parse Terraform file {file_path}: {str(e)}")

    # Update the terraform configuration in memory.
    terraform_config = update_terraform_file(
        module,
        terraform_config,
        vnet_name,
        vnet_address,
        module.params['subnet_name'],
        module.params['new_subnet_cidr'],
        module.params['delegation_name']
    )

    # Determine the output file path.
    if original_path.suffix == '.tf':
        new_path = original_path.with_suffix('.tf.json')
    elif not is_json:
        new_path = original_path.with_suffix('.json')
    else:
        new_path = original_path

    try:
        with open(new_path, 'w') as f:
            json.dump(terraform_config, f, indent=2)
    except Exception as e:
        module.fail_json(msg=f"Failed to write updated Terraform file: {str(e)}")

    # Small delay for file system sync.
    time.sleep(2)

    # Build the result.
    result = {
        'changed': True,
        'vnet_name': vnet_name,
        'validation': {
            'valid': valid,
            'message': validation_message,
            'vnet_address_space': vnet_address_space,
            'subnet_cidr': module.params['new_subnet_cidr'],
            'existing_subnets': [
                {
                    'name': subnet.get('name'),
                    'address_prefix': subnet.get('properties', {}).get('addressPrefix')
                }
                for subnet in existing_subnets
            ]
        },
        'terraform_update': {
            'new_file_path': str(new_path),
            'message': "Terraform file updated. " +
                       (f"Converted to {new_path.name} and original file kept" if new_path != original_path else "File updated in place")
        }
    }
    
    module.exit_json(**result)

if __name__ == '__main__':
    main()
