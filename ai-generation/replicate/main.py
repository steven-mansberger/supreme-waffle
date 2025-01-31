import replicate
import os
from pathlib import Path
import urllib.request
from urllib.parse import urlparse

os.environ["REPLICATE_API_TOKEN"] = ""

# model_name = "datacte-flux-aesthetic-anime"           # 90    / $1        # Flux lora, ghibli retro anime
# model_name = "datacte-flux-synthetic-anime"           # 19    / $1        # Flux lora, Trigger word "syntheticanime". Use "1980s anime screengrab", "VHS quality", or "syntheticanime"
# model_name = "datacte-mobius"                         # 90    / $1
# model_name = "datacte-prometheusv1"                   # 180   / $1        # finetune of Playground v2.5
# model_name = "datacte-proteus-v0.5"                   # 83    / $1        # anime
# model_name = "dreamshaper-xl-turbo"                   # 55    / $1
# model_name = "flux-schnell"                           # 333   / $1
# model_name = "flux-dev"                               # 40    / $1
# model_name = "flux-1.1-pro"                           # 25    / $1         # image_prompt
# model_name = "flux-1.1-pro-ultra"                     # 16    / $1         # image_prompt
# model_name = "kandinsky-2.2"                          # 10    / $1
# model_name = "latent-consistency-model"               # 625   / $1         # 50 outputs, image_prompt
# model_name = "material-diffusion"                     # 238   / $1         # 10 outputs, Uses image_prompt
# model_name = "open-dalle-v1.1"                        # 1     / $1
# model_name = "photon"                                 # 33    / $1
# model_name = "photon-flash"                           # 100   / $1
# model_name = "pixart-xl-2"                            # 66    / $1
# model_name = "playground-v2.5-1024px-aesthetic"       # 158   / $1
# model_name = "realvisxl-v3-multi-controlnet-lora"     # 66    / $1
# model_name = "sana"                                   # 555   / $1
# model_name = "stable-diffusion"                       # 714   / $1
# model_name = "stable-diffusion-3"                     # 28    / $1
# model_name = "sdxl"                                   # 175   / $1
# model_name = "stable-diffusion-3.5-medium"            # 28    / $1
# model_name = "stable-diffusion-3.5-large-turbo"       # 25    / $1
# model_name = "sticker-maker"                          # 119   / $1

pixart_style = "Digital Art"            # None, Digital Art, Cinematic, Photographic, Anime, Manga, Pixel Art, Fantasy Art, Neonpunk, 3D Model
scheduler = "DPMSolverMultistep"        

# "DPMSolverMultistep" "DDIM" "HeunDiscrete" "KarrasDPM" "K_EULER_ANCESTRAL" "K_EULER" "PNDM"
# Default schedulers:
# datacte-mobius                            "DPMSolverMultistep"
# datacte-proteus-v0.5                      "DPM++2MSDE"
# datacte-prometheusv1                      "DPM++2MSDE"
# dreamshaper-xl-turbo                      "K_EULER"
# material-diffusion                        "K-LMS"
# open-dalle-v1.1                           "KarrasDPM"
# pixart-xl-2                               "DPMSolverMultistep"
# playground-v2.5-1024px-aesthetic          "DPMSolver++" "DPM++2MKarras"
# realvisxl-v3-multi-controlnet-lora        "K_EULER"
# stable-diffusion                          "DPMSolverMultistep"

prompt = "A muscular, bald man with a full beard, slightly-tan skin, wearing a black shirt with white and red designs, holding gold and silver medals, with a Japanese-themed forest background. high detail 3D animation style"
negative_prompt = ""
reference_image = Path(r"reference_images/01.jpg") # url or local path

prompt_strength = 0.8
mask = ""
refine = "no_refiner"                   # Default: "no_refiner" "base_image_refiner"
# Refiner only for sdxl "expert_ensemble_refiner"

aspect_ratio = "1:1"
width = 1024
height = 1024
num_outputs = 4                       # 1-4

seed = -1
output_format = "png"
output_quality = 100
apply_watermark = False
disable_safety_checker = True

# Define model parameters
model_params = {
    "datacte-flux-aesthetic-anime": {
        "model_id": "datacte/flux-aesthetic-anime:2c3677b83922a0ac99493467805fb0259f55c4f4f7b1988b1dd1d92f083a8304",
        "input": {
            "model": "dev",                             # "dev" "schnell"
            "prompt": prompt,
            "go_fast": False,
            "lora_scale": 1,                            # Default: 1, -1-3
            "megapixels": "1",
            "num_outputs": num_outputs,
            "aspect_ratio": aspect_ratio,
            "output_format": output_format,
            "guidance_scale": 3.5,                      # Default: 3, 1-10
            "output_quality": output_quality,
            "prompt_strength": prompt_strength,
            "extra_lora_scale": 0.8,
            "num_inference_steps": 28,                   # Default 28, 1-50            
            "disable_safety_checker": disable_safety_checker
        }
    },    
    "datacte-flux-synthetic-anime": {
        "model_id": "datacte/flux-synthetic-anime:01c7749152b789eef876573153fa36f6013a2d7185ad38588fae19743ebca6e0",
        "input": {
            "model": "dev",                             # "dev" "schnell"
            "prompt": prompt,
            "go_fast": False,
            "lora_scale": 0.85,
            "megapixels": "1",
            "num_outputs": num_outputs,
            "aspect_ratio": aspect_ratio,
            "output_format": output_format,
            "guidance_scale": 3.5,                      # Default: 3, 1-10
            "output_quality": output_quality,
            "prompt_strength": prompt_strength,
            "extra_lora_scale": 0.8,
            "num_inference_steps": 28,                   # Default 28, 1-50            
            "disable_safety_checker": disable_safety_checker
        }
    },    
    "datacte-mobius": {
        "model_id": "datacte/mobius:197f2145583f80c7c3ec520d2a1080aa7986601e1612e417ccd6e4f50fe0624f",
        "input": {
            # "seed": seed,
            "width": width,
            "height": height,
            "prompt": prompt,
            "scheduler": scheduler,
            "num_outputs": num_outputs,
            "guidance_scale": 7,                        # Default: 7, 1-50
            "negative_prompt": negative_prompt,
            "num_inference_steps": 50,                   # Default 50, 1-100
            "disable_safety_checker": disable_safety_checker
        }
    },
    "datacte-prometheusv1": {
        "model_id": "datacte/prometheusv1:a40536dd5f61e7c3c43060dff5b9b488a749dec1cb283a904dd82032fc717295",
        "input": {
            # "seed": seed,
            # "image": reference_image,
            "width": width,
            "height": height,
            "prompt": prompt,
            "scheduler": scheduler,
            "num_outputs": num_outputs,
            "guidance_scale": 7,                        # Default: 7, 1-50
            "negative_prompt": negative_prompt,
            "prompt_strength": prompt_strength,                     # Default 0.8, 0-1
            "num_inference_steps": 50,                   # Default 50, 1-100
            "disable_safety_checker": disable_safety_checker
        }
    },
    "datacte-proteus-v0.5": {
        "model_id": "datacte/proteus-v0.3:b28b79d725c8548b173b6a19ff9bffd16b9b80df5b18b8dc5cb9e1ee471bfa48",
        "input": {
            # "seed": seed,
            # "image": reference_image,
            "width": width,
            "height": height,
            "prompt": prompt,
            "scheduler": scheduler,
            "num_outputs": num_outputs,
            "guidance_scale": 7,                        # Default: 7, 1-50
            "negative_prompt": negative_prompt,
            "prompt_strength": prompt_strength,                     # Default 0.8, 0-1
            "num_inference_steps": 50,                   # Default 50, 1-100
            "disable_safety_checker": disable_safety_checker
        }
    },
    "dreamshaper-xl-turbo": {
        "model_id": "lucataco/dreamshaper-xl-turbo:0a1710e0187b01a255302738ca0158ff02a22f4638679533e111082f9dd1b615",
        "input": {
            "width": width,
            "height": height,
            "prompt": prompt,
            "scheduler": scheduler,
            "num_outputs": num_outputs,
            "guidance_scale": 2,                    # Default 2, 1-20
            "apply_watermark": apply_watermark,
            "negative_prompt": negative_prompt,
            "num_inference_steps": 7,                # Default 6, 1-50
            "disable_safety_checker": disable_safety_checker
        }
    },
    "flux-schnell": {
        "model_id": "black-forest-labs/flux-schnell",
        "input": {
            # "seed": seed,
            "prompt": prompt,                        
            "num_inference_steps": 4,               # Default: 4, 1-4                                  
            "megapixels": "1",                      # 0.25 or 1
            "output_quality": output_quality,                  # Default: 80, 1-100, only for webm 
            "num_outputs": num_outputs,
            "output_format": output_format,  
            "aspect_ratio": aspect_ratio,        
            "go_fast": False,
            "disable_safety_checker": disable_safety_checker
        }
    },
    "flux-dev": {
        "model_id": "black-forest-labs/flux-dev",
        "input": {
            # "seed": seed,
            "prompt": prompt,
            "prompt_strength": prompt_strength,                 # Default: 0.8, 0-1           
            "num_inference_steps": 28,              # Default: 28, recommend 28-50, 1-50            
            "guidance": 3,                          # Default: 3, 1-10            
            "megapixels": "1",                      # 0.25 or 1
            "output_quality": output_quality,                  # Default: 80, 1-100, only for webm
            "num_outputs": num_outputs,
            "output_format": output_format,
            "aspect_ratio": aspect_ratio,            
            "go_fast": False,
            "disable_safety_checker": disable_safety_checker
        }
    },
    "flux-1.1-pro": {
        "model_id": "black-forest-labs/flux-1.1-pro",
        "input": {
            # "seed": seed,
            "prompt": prompt,
            "aspect_ratio": aspect_ratio,         # or custom
            "height": height,                     # Only used when aspect_ratio=custom. Must be a multiple of 32
            "width": width,                       # Only used when aspect_ratio=custom. Must be a multiple of 32
            # "image_prompt": reference_image,      # reference image URL. Must be jpeg, png, gif, or webp.
            "output_format": output_format,
            "output_quality": output_quality,
            "safety_tolerance": 6,                  # Default 2, 1-6 strict to permissive
            "prompt_upsampling": True               # Automatically modify the prompt for more creative generation
        }
    },
    "flux-1.1-pro-ultra": {
        "model_id": "black-forest-labs/flux-1.1-pro-ultra",
        "input": {
            # "seed": seed,
            "raw": False,                           # Generate less processed, more natural-looking images
            "prompt": prompt,
            "aspect_ratio": aspect_ratio,
            "output_format": output_format,
            "safety_tolerance": 6,                  # Default 2, 1-6 strict to permissive
            # "image_prompt": reference_image,           # reference image URL. Must be jpeg, png, gif, or webp.
            "image_prompt_strength": 0.1            # Default 0.1, Max 1, Blend between the prompt and the image prompt
        }
    },
    "kandinsky-2.2": {
        "model_id": "ai-forever/kandinsky-2.2:ad9d7879fbffa2874e1d909d1d37d9bc682889cc65b31f7bb00d2362619f194a",
        "input": {
            # "seed": seed,
            "prompt": prompt,
            "num_inference_steps": 75,              # Default 75, 1-500
            "num_inference_steps_prior": 25,         # Default 25, 1-500
            "output_format": output_format,
            "width": width,                         # Default: 512
            "height": height                        # Default: 512
        }
    },
    "latent-consistency-model": {
        "model_id": "fofr/latent-consistency-model:683d19dc312f7a9f0428b04429a9ccefd28dbf7785fef083ad5cf991b65f406f",
        "input": {
            # "image": reference_image,
            "width": width,
            "height": height,
            "prompt": prompt,
            "num_images": num_outputs,
            "guidance_scale": 8,                    # Defaul: 8, 1-20
            "archive_outputs": False,
            "prompt_strength": prompt_strength,                # Default 0.8, 0-1
            "sizing_strategy": "width/height",
            "lcm_origin_steps": 50,                 # Default 50, 1-?
            "canny_low_threshold": 100,             # Default 100, 1-255
            "num_inference_steps": 8,               # Default 8, 1-50
            "canny_high_threshold": 200,            # Default 200, 1-255
            "control_guidance_end": 1,              # Default: 1, Max 1
            "control_guidance_start": 0,            # Default: 1, Max 1
            "controlnet_conditioning_scale": 2      # Default 2, 0.1-4
        }
    },
    "material-diffusion": {
        "model_id": "tstramer/material-diffusion:a42692c54c0f407f803a0a8a9066160976baedb77c91171a01730f9b0d7beeff",
        "input": {
            # "seed": seed,
            "width": width,                         # Default: 512
            "height": width,                        # Default: 512
            "prompt": prompt,
            # "init_image": reference_image,          # Inital image to generate variations of. Will be resized to the specified width and height
            "scheduler": "K-LMS",                   # Default: "K-LMS" "DDIM" "PNDM"
            "num_outputs": num_outputs,             # 1-10
            "guidance_scale": 7.5,                  # Default: 7.5, 1-20
            "prompt_strength": prompt_strength,                 # Default 0.8, 0-1
            "num_inference_steps": 50               # Default 50, 1-500
        }
    },
    "open-dalle-v1.1": {
        "model_id": "lucataco/open-dalle-v1.1:1c7d4c8dec39c7306df7794b28419078cb9d18b9213ab1c21fdc46a1deca0144",
        "input": {
            # "seed": seed,
            "width": width,
            "height": height,
            "prompt": prompt,
            "negative_prompt": negative_prompt,
            "scheduler": scheduler,
            "num_outputs": num_outputs,
            "guidance_scale": 7.5,                  # Default 7.5, 1-50
            "prompt_strength": prompt_strength,                 # Default 0.8, 0-1
            "num_inference_steps": 60,              # Default 60, 1-100
            "apply_watermark": True,
            "disable_safety_checker": disable_safety_checker
        }
    },
    "photon": {
        "model_id": "luma/photon",
        "input": {
            # "seed": seed,
            "prompt": prompt,
            "aspect_ratio": "16:9",
            "image_reference_url": "",
            "style_reference_url": "",
            "character_reference_url": "",
            "image_reference_weight": 0.85,         # Max: 1
            "style_reference_weight": 0.85          # Max: 1
        }
    },
    "photon-flash": {
        "model_id": "luma/photon-flash",
        "input": {
            # "seed": seed,
            "prompt": prompt,
            "aspect_ratio": "16:9",
            "image_reference_url": "",
            "style_reference_url": "",
            "character_reference_url": "",
            "image_reference_weight": 0.85,         # Max: 1
            "style_reference_weight": 0.85          # Max: 1
        }
    },
    # PixArt-Alpha 1024px
    "pixart-xl-2": {
        "model_id": "lucataco/pixart-xl-2:816c99673841b9448bc2539834c16d40e0315bbf92fef0317b57a226727409bb",
        "input": {
            "prompt": prompt,
            "guidance_scale": 4.5,                  # Default: 4.5, 1-50
            "num_inference_steps": 14,              # Default 14, 1-100
            "style": pixart_style,
            "width": width,
            "height": height,            
            "scheduler": scheduler,
            "num_outputs": num_outputs            
        }
    },
    "playground-v2.5-1024px-aesthetic": {
        "model_id": "playgroundai/playground-v2.5-1024px-aesthetic:a45f82a1382bed5c7aeb861dac7c7d191b0fdf74d8d57c4a0e6ed7d4d0bf7d24",
        "input": {
            "width": width,
            "height": height,
            "prompt": prompt,
            "scheduler": scheduler,                 # Default: "DPMSolver++" "DPM++2MKarras"
            "num_outputs": num_outputs,
            "guidance_scale": 3,                    # Default 3, 0.1-20
            "apply_watermark": apply_watermark,
            "negative_prompt": negative_prompt,
            "prompt_strength": prompt_strength,
            "num_inference_steps": 25,
            "disable_safety_checker": disable_safety_checker
        }
    },
    "realvisxl-v3-multi-controlnet-lora": {
        "model_id": "fofr/realvisxl-v3-multi-controlnet-lora:90a4a3604cd637cb9f1a2bdae1cfa9ed869362ca028814cdce310a78e27daade",
        "input": {
            "prompt": prompt,
            "negative_prompt": negative_prompt,
            "seed": seed,
            "width": width,
            "height": width,
            # "image": reference_image,
            "refine": "no_refiner",                           # Default: "no_refiner" "base_image_refiner"
            "scheduler": scheduler,                     # Default: "K_EULER"
            "lora_scale": 0.6,                          # Default: 0.6, Max: 1
            "num_outputs": num_outputs,
            # "controlnet_1": "none",
            # "controlnet_1_image": reference_image,
            # "controlnet_1_conditioning_scale": 0.8,
            # "controlnet_1_start": 0,
            # "controlnet_1_end": 1,            
            # "controlnet_2": "none",
            # "controlnet_2_image": "",
            # "controlnet_2_conditioning_scale": 0.8,
            # "controlnet_2_start": 0,
            # "controlnet_2_end": 1,
            # "controlnet_3": "none",
            # "controlnet_3_image": "",
            # "controlnet_3_conditioning_scale": 0.8,
            # "controlnet_3_start": 0,
            # "controlnet_3_end": 1,
            "guidance_scale": 7.5,
            "apply_watermark": apply_watermark,
            "prompt_strength": prompt_strength,             # Default 0.8, 0-1
            "sizing_strategy": "width_height",
            "num_inference_steps": 30                       # Default 30, 1-500            
        }
    },
    # model_variants: "1600M-1024px" "1600M-1024px-multilang" "1600M-512px" "600M-1024px-multilang" "600M-512px-multilang"
    # 1600M variants are slower but produce higc c  her quality than 600M, 1024px variants are optimized for 1024x1024px images
    # 512px variants are optimized for 512x512px images, 'multilang' variants can be prompted in both English and Chinese
    "sana": {
        "model_id": "nvidia/sana:c6b5d2b7459910fec94432e9e1203c3cdce92d6db20f714f1355747990b52fa6",
        "input": {
            "prompt": prompt,
            "negative_prompt": negative_prompt,
            "guidance_scale": 5,                    # Default: 5, 1-20      
            "pag_guidance_scale": 2,                # Default: 2, 1-20
            "num_inference_steps": 24,              # Default: 18
            "model_variant": "1600M-1024px",        # Default: "1600M-1024px"
            "width": width,                         # Default: 1024, 1-4096
            "height": height                        # Default: 1024, 1-4096
        }
    },
    "stable-diffusion": {
        "model_id": "stability-ai/stable-diffusion:ac732df83cea7fff18b8472768c88ad041fa750ff7682a21affe81863cbe77e4",
        "input": {
            "width": width,
            "height": height,
            "prompt": prompt,
            "negative_prompt": negative_prompt,
            "scheduler": scheduler,
            "num_outputs": num_outputs,
            "guidance_scale": 7.5,                  # Default 7.5, 1-20
            "num_inference_steps": 50               # Default 50, 1-500
        }
    },
    "stable-diffusion-3": {
        "model_id": "stability-ai/stable-diffusion-3",
        "input": {
            "cfg": 3.5,                             # Default: 3.5, 1-20
            "steps": 28,                            # Default: 28, 1-28
            "prompt": prompt,
            "aspect_ratio": aspect_ratio,
            "output_format": output_format,
            "output_quality": output_quality,
            "negative_prompt": negative_prompt,
            "prompt_strength": prompt_strength      # Default 0.85, 0-1
        }
    },
    "sdxl": {
        "model_id": "stability-ai/sdxl:7762fd07cf82c948538e41f63f77d685e02b063e37e496e96eefd46c929f9bdc",
        "input": {
            # "seed": seed,    
            # "mask": mask,    
            "prompt": prompt,
            "negative_prompt": negative_prompt,
            "prompt_strength": prompt_strength,                 # Default: 0.8, 0-1
            "guidance_scale": 7.5,                  # Default: 7.5, 1-50
            "high_noise_frac": 0.8,                 # 0-1, For expert_ensemble_refiner, the fraction of noise to use
            "num_inference_steps": 25,              # Max: 500
            "refine": "expert_ensemble_refiner",    # Default: "expert_ensemble_refiner" "no_refiner" "base_image_refiner"
            "scheduler": scheduler,
            "lora_scale": 0.6,                      # Max: 1
            "num_outputs": num_outputs,
            "width": 1024,
            "height": 1024,
            "apply_watermark": apply_watermark
        }
    },
    "stable-diffusion-3.5-medium": {
        "model_id": "stability-ai/stable-diffusion-3.5-medium",
        "input": {
            # "seed": seed,
            "cfg": 5,                               # Default 5, 1-20
            "steps": 40,                            # Default 40, 1-50
            "prompt": prompt,
            "aspect_ratio": aspect_ratio,
            "output_format": output_format,
            "output_quality": output_quality,
            "prompt_strength": prompt_strength                 # Default 0.85, 0-1
        }
    },
    "stable-diffusion-3.5-large-turbo": {
        "model_id": "stability-ai/stable-diffusion-3.5-large-turbo",
        "input": {
            # "seed": seed,
            "cfg": 1,                               # Default 1, 1-20
            "steps": 4,                            # Default 4, 1-10
            "prompt": prompt,
            "aspect_ratio": aspect_ratio,
            "output_format": output_format,
            "output_quality": output_quality,
            "prompt_strength": prompt_strength                 # Default 0.85, 0-1
        }
    },
    "sticker-maker": {
        "model_id": "fofr/sticker-maker:4acb778eb059772225ec213948f0660867b2e03f277448f18cf1800b96a65a1a",
        "input": {
            "prompt": prompt,
            "negative_prompt": negative_prompt,
            "steps": 17,                            # Default: 17
            "width": 1152,                          # Default: 1152
            "height": 1152,                         # Default: 1152
            "output_format": output_format,
            "output_quality": output_quality,                  # Default 90, 1-100
            "number_of_images": num_outputs
        }
    }
}

# Run the selected model
output = replicate.run(model_params[model_name]["model_id"], input=model_params[model_name]["input"])

# File naming logic
existing_files = [f for f in os.listdir('.') if f.startswith('output_') and f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp', '.gif', '.bmp', '.tiff'))]
existing_count = len(existing_files)

print(output)
# Save the output based on model type
if model_name in ["sana", "photon-flash", "photon", "flux-1.1-pro", "flux-1.1-pro-ultra"]:
    output = str(output)  # Ensure it's a string URL
    try:
        # Parse the URL to get the file extension
        parsed_url = urlparse(output)
        file_extension = os.path.splitext(parsed_url.path)[1]
        
        # Use the correct file extension for the filename
        filename = f"output_{existing_count + 1}_{model_name}{file_extension}"
        urllib.request.urlretrieve(output, filename)
        print(f"Saved image from URL as {filename}")
    except urllib.error.HTTPError as e:
        print(f"HTTP Error for URL download: {e.code} - {e.reason}")
    except urllib.error.URLError as e:
        print(f"URL Error for URL download: {e.reason}")
    except Exception as e:
        print(f"Unexpected error for URL download: {e}")
else:
    try:
        for index, item in enumerate(output):
            file_extension = ".jpg" if model_name == "latent-consistency-model" else f".{output_format}"
            filename = f"output_{existing_count + index + 1}_{model_name}{file_extension}"
            with open(filename, "wb") as file:
                file.write(item.read())
            print(f"Saved image as {filename}")
        # Update existing_count after the loop to reflect new files for the next run
        existing_count += len(output)
    except Exception as e:
        print(f"Failed to write image data: {e}")