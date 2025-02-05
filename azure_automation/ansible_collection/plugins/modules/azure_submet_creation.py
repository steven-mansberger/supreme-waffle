#!/usr/bin/python

from ansible.module_utils.basic import AnsibleModule
import json
import hcl2
import os
from pathlib import Path
from ipaddress import ip_network
import time

def calculate_new_bits(vnet_cidr, subnet_cidr):
    vnet_prefix = ip_network(vnet_cidr).prefixlen
    subnet_prefix = ip_network(subnet_cidr).prefixlen
    return subnet_prefix - vnet_prefix

def find_target_module(terraform_config, vnet_name):
    for module in terraform_config.get('module', []):
        for name, config in module.items():
            if config.get('vnet_name') == vnet_name:
                return config
    return None

def main():
    module_args = dict(
        file_path=dict(type='path', required=True),
        vnet_name=dict(type='str', required=True),
        vnet_address=dict(type='str', required=True),
        subnet_name=dict(type='str', required=True),
        new_subnet_cidr=dict(type='str', required=True),
        delegation_name=dict(type='str', default=None)
    )

    result = dict(changed=False, message='')
    module = AnsibleModule(argument_spec=module_args, supports_check_mode=False)

    file_path = module.params['file_path']
    vnet_name = module.params['vnet_name']
    subnet_name = module.params['subnet_name']
    delegation_name = module.params['delegation_name']

    try:
        # Determine file type and new path
        original_path = Path(file_path)
        is_json = original_path.suffix == '.json'
        
        # Read and parse file
        with open(file_path, 'r') as f:
            content = f.read()

        if is_json:
            terraform_config = json.loads(content)
        else:
            terraform_config = hcl2.loads(content)

        # Find target module
        target_config = find_target_module(terraform_config, vnet_name)
        if not target_config:
            module.fail_json(msg=f"Module with vnet_name '{vnet_name}' not found")

        # Process subnets
        subnets = target_config.get('subnets', [])
        if not isinstance(subnets, list):
            module.fail_json(msg="Subnets configuration is invalid")

        # Calculate new_bits
        new_bits = calculate_new_bits(
            module.params['vnet_address'],
            module.params['new_subnet_cidr']
        )

        # Create new subnet
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

        # Add and sort subnets
        subnets.append(new_subnet)
        subnets.sort(key=lambda x: x['new_bits'], reverse=True)
        target_config['subnets'] = subnets

        # Determine output path
        if original_path.suffix == '.tf':
            new_path = original_path.with_suffix('.tf.json')
        elif not is_json:
            new_path = original_path.with_suffix('.json')
        else:
            new_path = original_path

        # Write JSON output
        with open(new_path, 'w') as f:
            json.dump(terraform_config, f, indent=2)

        # Add a small delay for file system sync
        time.sleep(2)

        # Don't remove original file
        if new_path != original_path:
            result['message'] = f"File converted to {new_path.name} and original file kept"
        else:
            result['message'] = "File updated in place"

        # Add new path to results
        result['changed'] = True
        result['new_file_path'] = str(new_path)

    except Exception as e:
        module.fail_json(msg=f"Failed to update Terraform file: {str(e)}")

    module.exit_json(**result)

if __name__ == '__main__':
    main()