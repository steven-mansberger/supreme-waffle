from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import replicate
from urllib.parse import urlparse
import urllib.request
import requests

import logging
from flask.logging import default_handler
app = Flask(__name__)
app.logger.setLevel(logging.DEBUG)

CORS(app, resources={r"/api/*": {"origins": ["http://192.168.0.66:3000", "http://localhost:3000"]}})
# Allow all origins
# CORS(app)

# Replicate API token
os.environ["REPLICATE_API_TOKEN"] = ""

model_params = {
    "asiryan-juggernaut-xl-v7": {
        "model_id": "asiryan/juggernaut-xl-v7:6a52feace43ce1f6bbc2cdabfc68423cb2319d7444a1a1dae529c5e88b976382",
        "input": {
            "seed": None,
            "width": None,
            "height": None,
            "prompt": None,
            "strength": None,
            "scheduler": None,
            "num_outputs": None,
            "guidance_scale": None,
            "negative_prompt": None,
            "num_inference_steps": None
        }
    },
    "datacte-flux-aesthetic-anime": {
        "model_id": "datacte/flux-aesthetic-anime:2c3677b83922a0ac99493467805fb0259f55c4f4f7b1988b1dd1d92f083a8304",
        "input": {
            "prompt": None,
            "model": None,
            "go_fast": None,
            "lora_scale": None,
            "megapixels": None,
            "num_outputs": None,
            "aspect_ratio": None,
            "output_format": None,
            "guidance_scale": None,
            "output_quality": None,
            "prompt_strength": None,
            "extra_lora_scale": None,
            "num_inference_steps": None,
            "disable_safety_checker": None
        }
    },
    "datacte-flux-synthetic-anime": {
        "model_id": "datacte/flux-synthetic-anime:01c7749152b789eef876573153fa36f6013a2d7185ad38588fae19743ebca6e0",
        "input": {
            "model": None,
            "prompt": None,
            "go_fast": None,
            "lora_scale": None,
            "megapixels": None,
            "num_outputs": None,
            "aspect_ratio": None,
            "output_format": None,
            "guidance_scale": None,
            "output_quality": None,
            "prompt_strength": None,
            "extra_lora_scale": None,
            "num_inference_steps": None,
            "disable_safety_checker": None
        }
    },
    "datacte-mobius": {
        "model_id": "datacte/mobius:197f2145583f80c7c3ec520d2a1080aa7986601e1612e417ccd6e4f50fe0624f",
        "input": {
            "seed": None,
            "width": None,
            "height": None,
            "prompt": None,
            "scheduler": None,
            "num_outputs": None,
            "guidance_scale": None,
            "negative_prompt": None,
            "num_inference_steps": None,
            "disable_safety_checker": None
        }
    },
    "datacte-prometheusv1": {
        "model_id": "datacte/prometheusv1:a40536dd5f61e7c3c43060dff5b9b488a749dec1cb283a904dd82032fc717295",
        "input": {
            "seed": None,
            "image": None,
            "width": None,
            "height": None,
            "prompt": None,
            "scheduler": None,
            "num_outputs": None,
            "guidance_scale": None,
            "negative_prompt": None,
            "prompt_strength": None,
            "num_inference_steps": None,
            "disable_safety_checker": None
        }
    },
    "datacte-proteus-v0.5": {
        "model_id": "datacte/proteus-v0.3:b28b79d725c8548b173b6a19ff9bffd16b9b80df5b18b8dc5cb9e1ee471bfa48",
        "input": {
            "seed": None,
            "image": None,
            "width": None,
            "height": None,
            "prompt": None,
            "scheduler": None,
            "num_outputs": None,
            "guidance_scale": None,
            "negative_prompt": None,
            "prompt_strength": None,
            "num_inference_steps": None,
            "disable_safety_checker": None
        }
    },
    "dreamshaper-xl-turbo": {
        "model_id": "lucataco/dreamshaper-xl-turbo:0a1710e0187b01a255302738ca0158ff02a22f4638679533e111082f9dd1b615",
        "input": {
            "width": None,
            "height": None,
            "prompt": None,
            "scheduler": None,
            "num_outputs": None,
            "guidance_scale": None,
            "apply_watermark": None,
            "negative_prompt": None,
            "num_inference_steps": None,
            "disable_safety_checker": None
        }
    },
    "flux-schnell": {
        "model_id": "black-forest-labs/flux-schnell",
        "input": {
            "seed": None,
            "prompt": None,
            "num_inference_steps": None,
            "megapixels": None,
            "output_quality": None,
            "num_outputs": None,
            "output_format": None,
            "aspect_ratio": None,
            "go_fast": None,
            "disable_safety_checker": None
        }
    },
    "flux-dev": {
        "model_id": "black-forest-labs/flux-dev",
        "input": {
            "seed": None,
            "prompt": None,
            "prompt_strength": None,
            "num_inference_steps": None,
            "guidance": None,
            "megapixels": None,
            "output_quality": None,
            "num_outputs": None,
            "output_format": None,
            "aspect_ratio": None,
            "go_fast": None,
            "disable_safety_checker": None
        }
    },
    "flux-1.1-pro": {
        "model_id": "black-forest-labs/flux-1.1-pro",
        "input": {
            "seed": None,
            "prompt": None,
            "aspect_ratio": None,
            "height": None,
            "width": None,
            "image_prompt": None,
            "output_format": None,
            "output_quality": None,
            "safety_tolerance": None,
            "prompt_upsampling": None
        }
    },
    "flux-1.1-pro-ultra": {
        "model_id": "black-forest-labs/flux-1.1-pro-ultra",
        "input": {
            "seed": None,
            "raw": None,
            "prompt": None,
            "aspect_ratio": None,
            "output_format": None,
            "safety_tolerance": None,
            "image_prompt": None,
            "image_prompt_strength": None
        }
    },
    "kandinsky-2.2": {
        "model_id": "ai-forever/kandinsky-2.2:ad9d7879fbffa2874e1d909d1d37d9bc682889cc65b31f7bb00d2362619f194a",
        "input": {
            "seed": None,
            "prompt": None,
            "num_inference_steps": None,
            "num_inference_steps_prior": None,
            "output_format": None,
            "width": None,
            "height": None
        }
    },
    "latent-consistency-model": {
        "model_id": "fofr/latent-consistency-model:683d19dc312f7a9f0428b04429a9ccefd28dbf7785fef083ad5cf991b65f406f",
        "input": {
            "image": None,
            "width": None,
            "height": None,
            "prompt": None,
            "num_images": None,
            "guidance_scale": None,
            "archive_outputs": None,
            "prompt_strength": None,
            "sizing_strategy": None,
            "lcm_origin_steps": None,
            "canny_low_threshold": None,
            "num_inference_steps": None,
            "canny_high_threshold": None,
            "control_guidance_end": None,
            "control_guidance_start": None,
            "controlnet_conditioning_scale": None
        }
    },
    "material-diffusion": {
        "model_id": "tstramer/material-diffusion:a42692c54c0f407f803a0a8a9066160976baedb77c91171a01730f9b0d7beeff",
        "input": {
            "seed": None,
            "width": None,
            "height": None,
            "prompt": None,
            "init_image": None,
            "scheduler": None,
            "num_outputs": None,
            "guidance_scale": None,
            "prompt_strength": None,
            "num_inference_steps": None
        }
    },
    "open-dalle-v1.1": {
        "model_id": "lucataco/open-dalle-v1.1:1c7d4c8dec39c7306df7794b28419078cb9d18b9213ab1c21fdc46a1deca0144",
        "input": {
            "seed": None,
            "width": None,
            "height": None,
            "prompt": None,
            "negative_prompt": None,
            "scheduler": None,
            "num_outputs": None,
            "guidance_scale": None,
            "prompt_strength": None,
            "num_inference_steps": None,
            "apply_watermark": None,
            "disable_safety_checker": None
        }
    },
    "photon": {
        "model_id": "luma/photon",
        "input": {
            "seed": None,
            "prompt": None,
            "aspect_ratio": None,
            "image_reference_url": None,
            "style_reference_url": None,
            "character_reference_url": None,
            "image_reference_weight": None,
            "style_reference_weight": None
        }
    },
    "photon-flash": {
        "model_id": "luma/photon-flash",
        "input": {
            "seed": None,
            "prompt": None,
            "aspect_ratio": None,
            "image_reference_url": None,
            "style_reference_url": None,
            "character_reference_url": None,
            "image_reference_weight": None,
            "style_reference_weight": None
        }
    },
    "pixart-xl-2": {
        "model_id": "lucataco/pixart-xl-2:816c99673841b9448bc2539834c16d40e0315bbf92fef0317b57a226727409bb",
        "input": {
            "prompt": None,
            "guidance_scale": None,
            "num_inference_steps": None,
            "style": None,
            "width": None,
            "height": None,
            "scheduler": None,
            "num_outputs": None
        }
    },
    "playground-v2.5-1024px-aesthetic": {
        "model_id": "playgroundai/playground-v2.5-1024px-aesthetic:a45f82a1382bed5c7aeb861dac7c7d191b0fdf74d8d57c4a0e6ed7d4d0bf7d24",
        "input": {
            "width": None,
            "height": None,
            "prompt": None,
            "scheduler": None,
            "num_outputs": None,
            "guidance_scale": None,
            "apply_watermark": None,
            "negative_prompt": None,
            "prompt_strength": None,
            "num_inference_steps": None,
            "disable_safety_checker": None
        }
    },
    "realvisxl-v3-multi-controlnet-lora": {
        "model_id": "fofr/realvisxl-v3-multi-controlnet-lora:90a4a3604cd637cb9f1a2bdae1cfa9ed869362ca028814cdce310a78e27daade",
        "input": {
            "prompt": None,
            "negative_prompt": None,
            "seed": None,
            "width": None,
            "height": None,
            "image": None,
            "refine": None,
            "scheduler": None,
            "lora_scale": None,
            "num_outputs": None,
            "controlnet_1": None,
            "controlnet_1_image": None,
            "controlnet_1_conditioning_scale": None,
            "controlnet_1_start": None,
            "controlnet_1_end": None,
            "controlnet_2": None,
            "controlnet_2_image": None,
            "controlnet_2_conditioning_scale": None,
            "controlnet_2_start": None,
            "controlnet_2_end": None,
            "controlnet_3": None,
            "controlnet_3_image": None,
            "controlnet_3_conditioning_scale": None,
            "controlnet_3_start": None,
            "controlnet_3_end": None,
            "guidance_scale": None,
            "apply_watermark": None,
            "prompt_strength": None,
            "sizing_strategy": None,
            "num_inference_steps": None
        }
    },
    "sana": {
        "model_id": "nvidia/sana:c6b5d2b7459910fec94432e9e1203c3cdce92d6db20f714f1355747990b52fa6",
        "input": {
            "prompt": None,
            "negative_prompt": None,
            "guidance_scale": None,
            "pag_guidance_scale": None,
            "num_inference_steps": None,
            "model_variant": None,
            "width": None,
            "height": None
        }
    },
    "sdxl": {
        "model_id": "stability-ai/sdxl:7762fd07cf82c948538e41f63f77d685e02b063e37e496e96eefd46c929f9bdc",
        "input": {
            "seed": None,
            "mask": None,
            "prompt": None,
            "negative_prompt": None,
            "prompt_strength": None,
            "guidance_scale": None,
            "high_noise_frac": None,
            "num_inference_steps": None,
            "refine": None,
            "scheduler": None,
            "lora_scale": None,
            "num_outputs": None,
            "width": None,
            "height": None,
            "apply_watermark": None
        }
    },
    "stable-diffusion": {
        "model_id": "stability-ai/stable-diffusion:ac732df83cea7fff18b8472768c88ad041fa750ff7682a21affe81863cbe77e4",
        "input": {
            "width": None,
            "height": None,
            "prompt": None,
            "negative_prompt": None,
            "scheduler": None,
            "num_outputs": None,
            "guidance_scale": None,
            "num_inference_steps": None
        }
    },
    "stable-diffusion-3": {
        "model_id": "stability-ai/stable-diffusion-3",
        "input": {
            "cfg": None,
            "steps": None,
            "prompt": None,
            "aspect_ratio": None,
            "output_format": None,
            "output_quality": None,
            "negative_prompt": None,
            "prompt_strength": None
        }
    },
    "stable-diffusion-3.5-medium": {
        "model_id": "stability-ai/stable-diffusion-3.5-medium",
        "input": {
            "seed": None,
            "cfg": None,
            "steps": None,
            "prompt": None,
            "aspect_ratio": None,
            "output_format": None,
            "output_quality": None,
            "prompt_strength": None
        }
    },
    "stable-diffusion-3.5-large": {
        "model_id": "stability-ai/stable-diffusion-3.5-large",
        "input": {
        "prompt": None,
        "aspect_ratio": None,
        "cfg_scale": None,
        "steps": None,
        "seed": None,
        "negative_prompt": None,
        "output_format": None,
        "output_quality": None,
        }
    },
    "stable-diffusion-3.5-large-turbo": {
        "model_id": "stability-ai/stable-diffusion-3.5-large-turbo",
        "input": {
            "seed": None,
            "cfg": None,
            "steps": None,
            "prompt": None,
            "aspect_ratio": None,
            "output_format": None,
            "output_quality": None,
            "prompt_strength": None
        }
    },
    "sticker-maker": {
        "model_id": "fofr/sticker-maker:4acb778eb059772225ec213948f0660867b2e03f277448f18cf1800b96a65a1a",
        "input": {
            "prompt": None,
            "negative_prompt": None,
            "steps": None,
            "width": None,
            "height": None,
            "output_format": None,
            "output_quality": None,
            "number_of_images": None
        }
    }
}

def save_images(data):
    urls = data.get('urls', [])
    model_name = data.get('metadata', {}).get('model', 'unknown-model')
    save_dir = '/var/www/images/saved_images/'
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)

    existing_files = [f for f in os.listdir(save_dir) if f.startswith('output_')]
    existing_numbers = [int(f.split('_')[1]) for f in existing_files if f.split('_')[1].isdigit()]
    next_number = max(existing_numbers, default=0) + 1

    saved_files = []
    
    for url in urls:
        try:
            response = requests.get(url)
            response.raise_for_status()
            
            parsed_url = urlparse(url)
            file_extension = os.path.splitext(parsed_url.path)[1].lower()
            
            filename = f"output_{next_number:04d}_{model_name}{file_extension}"
            with open(os.path.join(save_dir, filename), 'wb') as file:
                file.write(response.content)
            
            saved_files.append(filename)
            next_number += 1

        except requests.RequestException as e:
            print(f"Failed to download image {url}: {e}")

    return {"saved": saved_files, "metadata": data.get('metadata', {})}

@app.errorhandler(Exception)
def handle_exception(e):
    app.logger.exception(f'An error occurred: {e}')
    return jsonify(error=str(e)), 500

@app.before_request
def log_request_info():
    app.logger.debug('Request Method: %s', request.method)
    app.logger.debug('Request URL: %s', request.url)
    app.logger.debug('Headers: %s', request.headers)

@app.route('/api/generate', methods=['POST'])
def generate_image():
    data = request.json
    model_name = data.get('model')
    app.logger.debug(f"Received model name: {model_name}")
    app.logger.debug(f"Available models: {list(model_params.keys())}")
    
    if model_name not in model_params:
        return jsonify({"error": "Invalid model"}), 400

    model_config = model_params[model_name]
    input_params = model_params[model_name]["input"].copy()

    if model_name in ["datacte-flux-aesthetic-anime", "datacte-flux-synthetic-anime"] and 'model_variant' in data:
        data['model'] = data['model_variant']  # Map model_variant to model for these specific models
        if 'prompt' in data and 'syntheticanim' not in data['prompt'].lower():
            data['prompt'] = "syntheticanim, " + data['prompt']

    # Update with provided data, but only if the key exists in input_params
    for key, value in data.items():
        if key in input_params:
            # Special handling for 'material-diffusion' model's width and height
            if model_name in ['material-diffusion', 'datacte-mobius', 'kandinsky-2.2'] and key in ['width', 'height']:
                try:
                    input_params[key] = int(value)
                except ValueError:
                    # If conversion fails, use the default value
                    input_params[key] = int(input_params[key] or model_config["input"].get(key, 0))
            else:
                input_params[key] = value

    # Filter out None values
    filtered_params = {k: v for k, v in input_params.items() if v is not None}

    app.logger.debug(f"Sending to Replicate: {filtered_params}")

    try:
        output = replicate.run(model_params[model_name]["model_id"], input=filtered_params)
        
        if model_name in ["sana", "photon-flash", "photon", "flux-1.1-pro", "flux-1.1-pro-ultra"]:
            # For models that return a URL
            url_output = str(output)  # Convert to string if it's not already
            return jsonify({"url": url_output})
        else:
            # For models that return bytes or a list of bytes
            if isinstance(output, list):
                return jsonify({"url": [str(item) for item in output]})
            else:
                # Assuming single image output
                return jsonify({"url": str(output)})
        
    except Exception as e:
        error_message = str(e)
        cleaned_error = error_message.replace('\n', ' ')
        app.logger.error(f"Replicate API call failed: {cleaned_error}")
        return jsonify({"error": cleaned_error}), 500

@app.route('/images/saved_images/<filename>')
def serve_image(filename):
    return send_from_directory('/var/www/images/saved_images/', filename)

@app.route('/api/saveImages', methods=['POST'])
def save_images_endpoint():
    data = request.json
    try:
        result = save_images(data)
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)