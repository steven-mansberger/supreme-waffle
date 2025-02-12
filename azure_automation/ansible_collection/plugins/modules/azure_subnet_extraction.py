#!/usr/bin/env python3
from ansible.module_utils.basic import AnsibleModule
from pathlib import Path
import hcl2
import json
import os
import re

def process_terraform_file(file_path):
    orig_path = Path(file_path)
    subnets_dir = orig_path.parent / f"{orig_path.stem}_subnets"
    
    with open(str(orig_path), 'r') as f:
        file_content = f.read()

    parsed = hcl2.loads(file_content)
    modules = parsed.get("module", [])
    
    extracted_subnets = {}
    modified = False

    for module in modules:
        for mod_name, module_config in module.items():
            if not isinstance(module_config, dict):
                continue

            subnets = module_config.get("subnets")
            if subnets and isinstance(subnets, (list, dict)) and len(subnets) > 0:
                os.makedirs(str(subnets_dir), exist_ok=True)                
                extracted_subnets[mod_name] = subnets                
                json_filename = subnets_dir / f"{mod_name}_subnets.tf.json"
                with open(str(json_filename), 'w') as jf:
                    json.dump(subnets, jf, indent=2)
                
                modified = True

    if modified:
        updated_content = rebuild_hcl(file_content, extracted_subnets)
        with open(str(orig_path), 'w') as f:
            f.write(updated_content)

    return extracted_subnets, modified

def rebuild_hcl(original_content, extracted_subnets):
    lines = original_content.splitlines()
    result_lines = []
    in_module = False
    current_module = None
    brace_count = 0
    i = 0
    
    while i < len(lines):
        line = lines[i]
        module_match = re.match(r'\s*module\s+"([^"]+)"\s*{', line)
        if module_match:
            current_module = module_match.group(1)
            in_module = True
            brace_count = 1
            result_lines.append(line)
            i += 1
            continue

        if in_module:
            brace_count += line.count('{') - line.count('}')
            if brace_count == 0:
                in_module = False
                current_module = None
                result_lines.append(line)
                i += 1
                continue

            if current_module in extracted_subnets and re.match(r'\s*subnets\s*=', line):
                indent = re.match(r'(\s*)', line).group(1)
                subnet_brace_count = line.count('[') - line.count(']')
                i += 1

                while subnet_brace_count > 0 and i < len(lines):
                    subnet_brace_count += lines[i].count('[') - lines[i].count(']')
                    i += 1

                relative_path = f"{current_module}_subnets/{current_module}_subnets.tf.json"
                result_lines.append(f'{indent}subnets = jsondecode(file("${{path.module}}/{relative_path}"))')
                continue

        result_lines.append(line)
        i += 1

    return '\n'.join(result_lines)

def main():
    module = AnsibleModule(
        argument_spec={
            'file_path': {'type': 'str', 'required': True},
        }
    )
    
    file_path = module.params['file_path']
    
    try:
        extracted_subnets, modified = process_terraform_file(file_path)
        if not extracted_subnets:
            module.exit_json(
                changed=False,
                message="No modules with a 'subnets' key found; no changes made."
            )
        message = (
            f"Extracted subnets for modules: {', '.join(extracted_subnets.keys())}. "
            "Subnets JSON files written and original file updated." if modified else
            "No changes were necessary; subnets already processed."
        )
        module.exit_json(changed=modified, message=message)
    except Exception as e:
        module.fail_json(msg=f"Error processing file: {str(e)}")

if __name__ == '__main__':
    main()
