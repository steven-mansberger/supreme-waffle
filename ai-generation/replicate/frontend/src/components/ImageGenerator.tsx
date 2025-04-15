"use client";

import React, { useState, useEffect } from 'react';
import { Box, Button, Card, CardHeader, CardContent, Checkbox, FormControl, FormControlLabel, Grid2, InputLabel, MenuItem, Select, Slider, TextField, Typography } from '@mui/material';
import { SelectChangeEvent } from '@mui/material/Select'
import { materialDarkTheme } from './themes';
import { ThemeProvider } from '@mui/material/styles';

const modelConfigs: { [key: string]: ModelConfig } = {
  "asiryan-juggernaut-xl-v7": {
    name: "Asiryan / Juggernaut XL",
    price: 714,
    params: {
      negative_prompt: { type: "text", default: "" },
      num_outputs: { type: "number", min: 1, max: 4, default: 4 },
      seed: { type: "number" },
      width: { type: "number", min: 0, max: 2048, step: 32, default: 1024 },
      height: { type: "number", min: 0, max: 2048, step: 32, default: 1024 },
      strength: { type: "slider", min: 0, max: 1, step: 0.1, default: 0.8 },
      scheduler: { 
        type: "select", 
        options: ["DDIM", "DPMSolverMultistep", "HeunDiscrete", "KarrasDPM", "K_EULER_ANCESTRAL", "K_EULER", "PNDM"],
        default: "K_EULER_ANCESTRAL" 
      },
      num_inference_steps: { type: "slider", min: 1, max: 500, step: 1, default: 40 },
      guidance_scale: { type: "slider", min: 1, max: 50, step: 1, default: 7 },
      disable_safety_checker: { type: "boolean", default: true }
    }
  },
  "datacte-flux-aesthetic-anime": {
    name: "Datacte / Flux Aesthetic Anime",
    price: 90,
    params: {
      aspect_ratio: { 
        type: "select",
        options: ["1:1", "16:9", "21:9", "3:2", "2:3", "4:5", "5:4", "3:4", "4:3", "9:16", "9:21", "custom"],
        default: "4:3"
      },
      megapixels: {
        type: "select",
        options: ["0.25", "1"],
        default: "1"
      },
      model_variant: { type: "select",
        options: ["dev", "schnell"],
        default: "dev"
      },
      num_outputs: { type: "number", min: 1, max: 4, default: 4 },
      lora_scale: { type: "slider", min: -1, max: 3, step: 0.1, default: 1 },
      extra_lora_scale: { type: "slider", min: 0, max: 1, step: 0.1, default: 0.8 },
      guidance_scale: { type: "slider", min: 1, max: 10, step: 1, default: 3 },
      prompt_strength: { type: "slider", min: 0, max: 1, step: 0.1, default: 0.8 },
      num_inference_steps: { type: "slider", min: 1, max: 50, step: 1, default: 28 },
      go_fast: { type: "boolean", default: false },
      disable_safety_checker: { type: "boolean", default: true },
      output_format: {type: "select",
        options: ["webp", "jpg", "png"],
        default: "png"
      },
      output_quality: { type: "slider", min: 1, max: 100, step: 1, default: 80}
    }
  },
  "datacte-flux-synthetic-anime": {
    name: "Datacte / Flux Synthetic Anime",
    price: 19,
    params: {
      num_outputs: { type: "number", min: 1, max: 4, default: 4 },
      aspect_ratio: { 
        type: "select",
        options: ["1:1", "16:9", "21:9", "3:2", "2:3", "4:5", "5:4", "3:4", "4:3", "9:16", "9:21", "custom"],
        default: "4:3"
      },
      megapixels: {
        type: "select",
        options: ["0.25", "1"],
        default: "1"
      },
      model_variant: { type: "select",
        options: ["dev", "schnell"],
        default: "dev"
      },
      lora_scale: { type: "slider", min: -1, max: 3, step: 0.1, default: 1 },
      extra_lora_scale: { type: "slider", min: 0, max: 1, step: 0.1, default: 0.8 },
      guidance_scale: { type: "slider", min: 1, max: 10, step: 1, default: 3 },
      prompt_strength: { type: "slider", min: 0, max: 1, step: 0.1, default: 0.8 },
      num_inference_steps: { type: "slider", min: 1, max: 50, step: 1, default: 28 },
      go_fast: { type: "boolean", default: false },
      disable_safety_checker: { type: "boolean", default: true },
      output_format: {type: "select",
        options: ["webp", "jpg", "png"],
        default: "png"
      },
      output_quality: { type: "slider", min: 1, max: 100, step: 1, default: 80}
    }
  },
  "datacte-mobius": {
    name: "Datacte / Mobius",
    price: 90,
    params: {
      negative_prompt: { type: "text", default: "" },
      num_outputs: { type: "number", min: 1, max: 4, default: 4 },
      seed: { type: "number" },
      width: {
        "type": "select",
        "options": ["128", "256", "384", "448", "512", "576", "640", "704", "768", "832", "896", "960", "1024", "1152", "1280", "1408", "1536", "1664", "1792", "1920", "2048"],
        "default": "1024"
      },
      height: {
        "type": "select",
        "options": ["128", "256", "384", "448", "512", "576", "640", "704", "768", "832", "896", "960", "1024", "1152", "1280", "1408", "1536", "1664", "1792", "1920", "2048"],
        "default": "1024"
      },
      scheduler: { 
        type: "select", 
        options: ["DDIM", "DPM++2MSDE", "DPMSolverMultistep", "HeunDiscrete", "KarrasDPM", "K_EULER_ANCESTRAL", "K_EULER", "PNDM"],
        default: "DPMSolverMultistep" 
      },
      guidance_scale: { type: "slider", min: 1, max: 50, step: 0.1, default: 7 },
      num_inference_steps: { type: "slider", min: 1, max: 100, step: 1, default: 50 },
      disable_safety_checker: { type: "boolean", default: true }
    }
  },
  "datacte-prometheusv1": {
    name: "Datacte / Prometheus v1",
    price: 180,
    params: {
      negative_prompt: { type: "text", default: "" },
      num_outputs: { type: "number", min: 1, max: 4, default: 4 },
      seed: { type: "number" },
      width: { type: "number", min: 0, max: 2048, step: 32, default: 1024 },
      height: { type: "number", min: 0, max: 2048, step: 32, default: 1024 },
      scheduler: { 
        type: "select", 
        options: ["DDIM", "DPM++2MSDE", "DPMSolverMultistep", "HeunDiscrete", "KarrasDPM", "K_EULER_ANCESTRAL", "K_EULER", "PNDM"],
        default: "DPMSolverMultistep" 
      },
      guidance_scale: { type: "slider", min: 1, max: 50, step: 1, default: 7 },
      prompt_strength: { type: "slider", min: 0, max: 1, step: 0.1, default: 0.8 },
      num_inference_steps: { type: "slider", min: 1, max: 100, step: 1, default: 50 },
      disable_safety_checker: { type: "boolean", default: true }
    }
  },
  "datacte-proteus-v0.5": {
    name: "Datacte / Proteus v0.5",
    price: 83,
    params: {
      negative_prompt: { type: "text", default: "" },
      num_outputs: { type: "number", min: 1, max: 4, default: 4 },
      seed: { type: "number" },
      width: { type: "number", min: 0, max: 2048, step: 32, default: 1024 },
      height: { type: "number", min: 0, max: 2048, step: 32, default: 1024 },
      scheduler: { 
        type: "select", 
        options: ["DDIM", "DPM++2MSDE", "DPMSolverMultistep", "HeunDiscrete", "KarrasDPM", "K_EULER_ANCESTRAL", "K_EULER", "PNDM"],
        default: "DPMSolverMultistep" 
      },
      guidance_scale: { type: "slider", min: 1, max: 50, step: 1, default: 7 },
      prompt_strength: { type: "slider", min: 0, max: 1, step: 0.1, default: 0.8 },
      num_inference_steps: { type: "slider", min: 1, max: 100, step: 1, default: 50 },
      disable_safety_checker: { type: "boolean", default: true }
    }
  },
  "dreamshaper-xl-turbo": {
    name: "Dreamshaper XL Turbo",
    price: 55,
    params: {
      negative_prompt: { type: "text", default: "" },
      num_outputs: { type: "number", min: 1, max: 4, default: 4 },
      width: { type: "number", min: 0, max: 2048, step: 32, default: 1024 },
      height: { type: "number", min: 0, max: 2048, step: 32, default: 1024 },
      scheduler: { 
        type: "select", 
        options: ["DDIM", "DPMSolverMultistep", "HeunDiscrete", "KarrasDPM", "K_EULER_ANCESTRAL", "K_EULER", "PNDM"],
        default: "DPMSolverMultistep" 
      },
      guidance_scale: { type: "slider", min: 1, max: 20, step: 1, default: 2 },
      num_inference_steps: { type: "slider", min: 1, max: 100, step: 1, default: 6 },
      disable_safety_checker: { type: "boolean", default: true }
    }
  },
  "flux-schnell": {
    name: "Flux Schnell",
    price: 333,
    params: {
      num_outputs: { type: "number", min: 1, max: 4, default: 4 },
      seed: { type: "number" },
      aspect_ratio: { 
        type: "select",
        options: ["1:1", "16:9", "21:9", "3:2", "2:3", "4:5", "5:4", "3:4", "4:3", "9:16", "9:21", "custom"],
        default: "4:3"
      },
      megapixels: {
        type: "select",
        options: ["0.25", "1"],
        default: "1"
      },
      num_inference_steps: { type: "slider", min: 1, max: 4, step: 1, default: 4 },
      go_fast: { type: "boolean", default: false },
      disable_safety_checker: { type: "boolean", default: true },
      output_format: {type: "select",
        options: ["webp", "jpg", "png"],
        default: "png"
      },
      output_quality: { type: "slider", min: 1, max: 100, step: 1, default: 80}
    }
  },
  "flux-dev": {
    name: "Flux Dev",
    price: 40,
    params: {
      num_outputs: { type: "number", min: 1, max: 4, default: 4 },
      seed: { type: "number" },
      aspect_ratio: { 
        type: "select",
        options: ["1:1", "16:9", "21:9", "3:2", "2:3", "4:5", "5:4", "3:4", "4:3", "9:16", "9:21", "custom"],
        default: "4:3"
      },
      guidance: { type: "slider", min: 1, max: 10, step: 1, default: 3 },
      megapixels: {
        type: "select",
        options: ["0.25", "1"],
        default: "1"
      },
      prompt_strength: { type: "slider", min: 0, max: 1, step: 0.1, default: 0.8 },
      num_inference_steps: { type: "slider", min: 1, max: 100, step: 1, default: 28 },
      go_fast: { type: "boolean", default: false },
      disable_safety_checker: { type: "boolean", default: true },
      output_format: {type: "select",
        options: ["webp", "jpg", "png"],
        default: "png"
      },
      output_quality: { type: "slider", min: 1, max: 100, step: 1, default: 80}
    }
  },
  "flux-1.1-pro": {
    name: "Flux 1.1 Pro",
    price: 25,
    params: {
      seed: { type: "number" },
      width: { type: "number", min: 0, max: 2048, step: 32, default: 1024 },
      height: { type: "number", min: 0, max: 2048, step: 32, default: 1024 },
      aspect_ratio: { 
        type: "select",
        options: ["1:1", "16:9", "21:9", "3:2", "2:3", "4:5", "5:4", "3:4", "4:3", "9:16", "9:21", "custom"],
        default: "4:3"
      },
      prompt_upsampling: { type: "boolean", default: true }, // True == more creative generation
      safety_tolerance: { type: "slider", min: 1, max: 6, step: 1, default: 2 },
      output_format: {type: "select",
        options: ["webp", "jpg", "png"],
        default: "png"
      },
      output_quality: { type: "slider", min: 1, max: 100, step: 1, default: 80}
    }
  },
  "flux-1.1-pro-ultra": {
    name: "Flux 1.1 Pro Ultra",
    price: 16,
    params: {
      seed: { type: "number" },
      aspect_ratio: { 
        type: "select",
        options: ["1:1", "16:9", "21:9", "3:2", "2:3", "4:5", "5:4", "3:4", "4:3", "9:16", "9:21", "custom"],
        default: "4:3"
      },
      safety_tolerance: { type: "slider", min: 1, max: 6, step: 1, default: 2 },
      image_prompt_strength: { type: "slider", min: 0, max: 1, step: 0.01, default: 0.1 },
      raw: { type: "boolean", default: false },
      output_format: {type: "select",
        options: ["jpg", "png"],
        default: "png"
      }
    }
  },
  "kandinsky-2.2": {
    name: "Kandinsky 2.2",
    price: 10,
    params: {
      seed: { type: "number" },
      width: {
        "type": "select",
        "options": ["128", "256", "384", "448", "512", "576", "640", "704", "768", "832", "896", "960", "1024", "1152", "1280", "1408", "1536", "1664", "1792", "1920", "2048"],
        "default": "1024"
      },
      height: {
        "type": "select",
        "options": ["128", "256", "384", "448", "512", "576", "640", "704", "768", "832", "896", "960", "1024", "1152", "1280", "1408", "1536", "1664", "1792", "1920", "2048"],
        "default": "1024"
      },
      num_inference_steps: { type: "slider", min: 1, max: 500, step: 1, default: 75 },
      num_inference_steps_prior: { type: "slider", min: 1, max: 500, step: 1, default: 25 },
      output_format: {type: "select",
        options: ["jpeg", "png"],
        default: "png"
      }
    }
  },
  "latent-consistency-model": {
    name: "Latent Consistency",
    price: 625,
    params: {
      num_images: { type: "number", min: 1, max: 4, default: 4 },
      width: { type: "number", min: 0, max: 2048, step: 32, default: 1024 },
      height: { type: "number", min: 0, max: 2048, step: 32, default: 1024 },
      guidance_scale: { type: "slider", min: 1, max: 20, step: 1, default: 8 },
      prompt_strength: { type: "slider", min: 0, max: 1, step: 0.1, default: 0.8 },
      lcm_origin_steps: { type: "slider", min: 1, max: 200, step: 1, default: 50 },
      canny_low_threshold: { type: "slider", min: 1, max: 255, step: 1, default: 100 },
      num_inference_steps: { type: "slider", min: 1, max: 50, step: 1, default: 8 },
      canny_high_threshold: { type: "slider", min: 1, max: 255, step: 1, default: 200 },
      control_guidance_end: { type: "slider", min: 0, max: 1, step: 0.1, default: 1 },
      control_guidance_start: { type: "slider", min: 0, max: 1, step: 0.1, default: 0 },
      controlnet_conditioning_scale: { type: "slider", min: 0.1, max: 4, step: 0.1, default: 2 }
    }
  },
  "material-diffusion": {
    name: "Material Diffusion",
    price: 238,
    params: {
      num_outputs: { type: "number", min: 1, max: 10, default: 4 },
      seed: { type: "number" },
      width: {
        "type": "select",
        "options": ["128", "256", "384", "448", "512", "576", "640", "704", "768", "832", "896", "960", "1024"],
        "default": "1024"
      },
      height: {
        "type": "select",
        "options": ["128", "256", "384", "448", "512", "576", "640", "704", "768", "832", "896", "960", "1024"],
        "default": "768"
      },
      scheduler: { 
        type: "select", 
        options: ["DDIM", "DPM++2MSDE", "DPMSolverMultistep", "HeunDiscrete", "KarrasDPM", "K_EULER_ANCESTRAL", "K-LMS", "K_EULER", "PNDM"],
        default: "K-LMS" 
      },
      guidance_scale: { type: "slider", min: 1, max: 20, step: 0.5, default: 7.5 },
      prompt_strength: { type: "slider", min: 0, max: 1, step: 0.1, default: 0.8 },
      num_inference_steps: { type: "slider", min: 1, max: 500, step: 1, default: 50 }
    }
  },
  "open-dalle-v1.1": {
    name: "Open Dalle V1.1",
    price: 1,
    params: {
      num_outputs: { type: "number", min: 1, max: 4, default: 4 },
      negative_prompt: { type: "text", default: "" },
      seed: { type: "number" },
      width: { type: "number", min: 0, max: 2048, step: 32, default: 1024 },
      height: { type: "number", min: 0, max: 2048, step: 32, default: 1024 },
      scheduler: { 
        type: "select", 
        options: ["DDIM", "DPM++2MSDE", "DPMSolverMultistep", "HeunDiscrete", "KarrasDPM", "K_EULER_ANCESTRAL", "K_EULER", "PNDM"],
        default: "DPMSolverMultistep" 
      },
      guidance_scale: { type: "slider", min: 1, max: 50, step: 0.5, default: 7.5 },
      prompt_strength: { type: "slider", min: 0, max: 1, step: 0.1, default: 0.8 },
      num_inference_steps: { type: "slider", min: 1, max: 100, step: 1, default: 60 },
      apply_watermark: { type: "boolean", default: false },
      disable_safety_checker: { type: "boolean", default: true }
    }
  },
  "photon": {
    name: "Photon",
    price: 33,
    params: {
      seed: { type: "number" },
      aspect_ratio: { 
        type: "select",
        options: ["1:1", "16:9", "21:9", "3:2", "2:3", "4:5", "5:4", "3:4", "4:3", "9:16", "9:21", "custom"],
        default: "4:3"
      },
      image_reference_url: { type: "text", default: "" },
      image_reference_weight: { type: "slider", min: 0, max: 1, step: 0.05, default: 0.85 },
      style_reference_url: { type: "text", default: "" },
      style_reference_weight: { type: "slider", min: 0, max: 1, step: 0.05, default: 0.85 },
      character_reference_url: { type: "text", default: "" }      
    }
  },
  "photon-flash": {
    name: "Photon Flash",
    price: 100,
    params: {
      seed: { type: "number" },
      aspect_ratio: { 
        type: "select",
        options: ["1:1", "16:9", "21:9", "3:2", "2:3", "4:5", "5:4", "3:4", "4:3", "9:16", "9:21", "custom"],
        default: "4:3"
      },
      image_reference_url: { type: "text", default: "" },
      image_reference_weight: { type: "slider", min: 0, max: 1, step: 0.05, default: 0.85 },
      style_reference_url: { type: "text", default: "" },
      style_reference_weight: { type: "slider", min: 0, max: 1, step: 0.05, default: 0.85 },
      character_reference_url: { type: "text", default: "" } 
    }
  },
  "pixart-xl-2": {
    name: "Pixart XL-2",
    price: 66,
    params: {
      num_outputs: { type: "number", min: 1, max: 4, default: 4 },
      width: { type: "number", min: 0, max: 2048, step: 32, default: 1024 },
      height: { type: "number", min: 0, max: 2048, step: 32, default: 1024 },
      scheduler: { 
        type: "select", 
        options: ["DDIM", "DPM++2MSDE", "DPMSolverMultistep", "HeunDiscrete", "KarrasDPM", "K_EULER_ANCESTRAL", "K_EULER", "PNDM"],
        default: "DPMSolverMultistep" 
      },
      "pixart_style": { 
        type: "select",
        options: ["None", "Digital Art", "Cinematic", "Photographic", "Anime", "Manga", "Pixel Art", "Fantasy Art", "Neonpunk", "3D Model"],
        default: "Digital Art"
      },
      guidance_scale: { type: "slider", min: 1, max: 50, step: 0.5, default: 4.5 },
      num_inference_steps: { type: "slider", min: 1, max: 100, step: 1, default: 14 }
    }
  },
  "playground-v2.5-1024px-aesthetic": {
    price: 158,
    name: "Playground v2.5 1024px Aesthetic",
    params: {
      num_outputs: { type: "number", min: 1, max: 4, default: 4 },
      negative_prompt: { type: "text", default: "" },
      width: { type: "number", min: 0, max: 2048, step: 32, default: 1024 },
      height: { type: "number", min: 0, max: 2048, step: 32, default: 1024 },
      scheduler: { 
        type: "select", 
        options: ["DDIM", "DPM++2MSDE", "DPMSolver++", "DPMSolverMultistep", "HeunDiscrete", "KarrasDPM", "K_EULER_ANCESTRAL", "K_EULER", "PNDM"],
        default: "DPMSolver++"
      },
      guidance_scale: { type: "slider", min: 1, max: 20, step: 1, default: 3 },
      prompt_strength: { type: "slider", min: 0, max: 1, step: 0.1, default: 0.8 },
      num_inference_steps: { type: "slider", min: 1, max: 60, step: 1, default: 25 },
      apply_watermark: { type: "boolean", default: false },
      disable_safety_checker: { type: "boolean", default: true }
    }
  },
  "realvisxl-v3-multi-controlnet-lora": {
    name: "RealvisXL V3 Multi-ControlNet-LoRA",
    price: 66,
    params: {
      num_outputs: { type: "number", min: 1, max: 4, default: 4 },
      negative_prompt: { type: "text", default: "" },
      seed: { type: "number" },
      width: { type: "number", min: 0, max: 2048, step: 32, default: 1024 },
      height: { type: "number", min: 0, max: 2048, step: 32, default: 1024 },
      scheduler: { 
        type: "select", 
        options: ["DDIM", "DPM++2MSDE", "DPMSolverMultistep", "HeunDiscrete", "KarrasDPM", "K_EULER_ANCESTRAL", "K_EULER", "PNDM"],
        default: "K_EULER" 
      },
      refine: { 
        type: "select", 
        options: ["no_refiner", "base_image_refiner", "expert_ensemble_refiner"], 
        default: "no_refiner" 
      },
      guidance_scale: { type: "slider", min: 1, max: 30, step: 0.5, default: 7.5 },
      lora_scale: { type: "slider", min: 0, max: 1, step: 0.1, default: 0.6 },   
      num_inference_steps: { type: "slider", min: 1, max: 500, step: 1, default: 30 },
      controlnet_1: { 
        type: "select", 
        options: ["none", "edge_canny", "illusion", "depth_leres", "depth_midas", "soft_edge_pidi", "soft_edge_hed", "lineart", "lineart_anime", "openpose"], 
        default: "none" 
      },
      controlnet_1_image: { type: "text", default: "" },
      controlnet_1_conditioning_scale: { type: "slider", min: 0, max: 2, step: 0.1, default: 0.8 },
      controlnet_1_start: { type: "slider", min: 0, max: 1, step: 0.1, default: 0 },
      controlnet_1_end: { type: "slider", min: 0, max: 1, step: 0.1, default: 1 },
      controlnet_2: { 
        type: "select", 
        options: ["none", "edge_canny", "illusion", "depth_leres", "depth_midas", "soft_edge_pidi", "soft_edge_hed", "lineart", "lineart_anime", "openpose"], 
        default: "none" 
      },
      controlnet_2_image: { type: "text", default: "" },
      controlnet_2_conditioning_scale: { type: "slider", min: 0, max: 2, step: 0.1, default: 0.8 },
      controlnet_2_start: { type: "slider", min: 0, max: 1, step: 0.1, default: 0 },
      controlnet_2_end: { type: "slider", min: 0, max: 1, step: 0.1, default: 1 },
      controlnet_3: { 
        type: "select", 
        options: ["none", "edge_canny", "illusion", "depth_leres", "depth_midas", "soft_edge_pidi", "soft_edge_hed", "lineart", "lineart_anime", "openpose"], 
        default: "none" 
      },
      controlnet_3_image: { type: "text", default: "" },
      controlnet_3_conditioning_scale: { type: "slider", min: 0, max: 2, step: 0.1, default: 0.8 },
      controlnet_3_start: { type: "slider", min: 0, max: 1, step: 0.1, default: 0 },
      controlnet_3_end: { type: "slider", min: 0, max: 1, step: 0.1, default: 1 },
      apply_watermark: { type: "boolean", default: false },
      prompt_strength: { type: "slider", min: 0, max: 1, step: 0.1, default: 0.8 },
      sizing_strategy: { 
        type: "select", 
        options: ["width_height", "long_side"], 
        default: "width_height" 
      }
    }
  },
  "sana": {
    name: "Sana",
    price: 555,
    params: {
      negative_prompt: { type: "text", default: "" },
      width: { type: "number", min: 0, max: 2048, step: 32, default: 1024 },
      height: { type: "number", min: 0, max: 2048, step: 32, default: 1024 },
      guidance_scale: { type: "slider", min: 1, max: 20, step: 1, default: 5 },
      pag_guidance_scale: { type: "slider", min: 1, max: 20, step: 1, default: 2 },
      model_variant: {
        type: "select",
        options: ["1600M-1024px", "1600M-512px", "400M-1024px", "400M-512px"],
        default: "1600M-1024px"
      }
    }
  },
  "sdxl": {
    name: "SDXL",
    price: 175,
    params: {
      num_outputs: { type: "number", min: 1, max: 4, default: 4 },
      negative_prompt: { type: "text", default: "" },
      mask: { type: "text", default: "" },
      seed: { type: "number" },
      width: { type: "number", min: 0, max: 2048, step: 32, default: 1024 },
      height: { type: "number", min: 0, max: 2048, step: 32, default: 1024 },
      scheduler: { 
        type: "select", 
        options: ["DDIM", "DPMSolverMultistep", "HeunDiscrete", "KarrasDPM", "K_EULER_ANCESTRAL", "K_EULER", "PNDM"],
        default: "K_EULER" 
      },
      refine: { 
        type: "select", 
        options: ["expert_ensemble_refiner", "no_refiner", "base_image_refiner"],
        default: "expert_ensemble_refiner" 
      },
      guidance_scale: { type: "slider", min: 1, max: 50, step: 0.5, default: 7.5 },
      high_noise_frac: { type: "slider", min: 0, max: 1, step: 0.1, default: 0.8},
      prompt_strength: { type: "slider", min: 0, max: 1, step: 0.1, default: 0.8 },
      lora_scale: { type: "slider", min: 0, max: 1, step: 0.1, default: 0.6 },
      num_inference_steps: { type: "slider", min: 1, max: 500, step: 1, default: 25 },
      apply_watermark: { type: "boolean", default: false }
    }
  },
  "stable-diffusion": {
    name: "Stable Diffusion",
    price: 714,
    params: {
      num_outputs: { type: "number", min: 1, max: 4, default: 4 },
      negative_prompt: { type: "text", default: "" },
      width: { type: "number", min: 0, max: 2048, step: 32, default: 1024 },
      height: { type: "number", min: 0, max: 2048, step: 32, default: 1024 },
      scheduler: { 
        type: "select", 
        options: ["DDIM", "DPM++2MSDE", "DPMSolverMultistep", "HeunDiscrete", "KarrasDPM", "K_EULER_ANCESTRAL", "K_EULER", "PNDM"],
        default: "DPMSolverMultistep" 
      },
      num_inference_steps: { type: "slider", min: 1, max: 500, step: 1, default: 50 },
      guidance_scale: { type: "slider", min: 1, max: 20, step: 0.5, default: 7.5 }
    }
  },
  "stable-diffusion-3": {
    name: "Stable Diffusion 3",
    price: 28,
    params: {
      negative_prompt: { type: "text", default: "" },
      aspect_ratio: { 
        type: "select",
        options: ["1:1", "16:9", "21:9", "3:2", "2:3", "4:5", "5:4", "3:4", "4:3", "9:16", "9:21", "custom"],
        default: "4:3"
      },
      cfg: { type: "slider", min: 1, max: 20, step: 0.5, default: 3.5 },
      steps: { type: "slider", min: 1, max: 100, step: 1 },
      prompt_strength: { type: "slider", min: 0, max: 1, step: 0.05, default: 0.85 },
      output_format: {type: "select",
        options: ["webp", "jpg", "png"],
        default: "png"
      },
      output_quality: { type: "slider", min: 1, max: 100, step: 1, default: 80}
    }
  },
  "stable-diffusion-3.5-medium": {
    name: "Stable Diffusion 3.5 Medium",
    price: 28,
    params: {
      negative_prompt: { type: "text", default: "" },
      seed: { type: "number" },
      aspect_ratio: { 
        type: "select",
        options: ["1:1", "16:9", "21:9", "3:2", "2:3", "4:5", "5:4", "3:4", "4:3", "9:16", "9:21", "custom"],
        default: "4:3"
      },
      cfg: { type: "slider", min: 1, max: 40, step: 1, default: 5 },
      steps: { type: "slider", min: 1, max: 28, step: 1, default: 28 },
      prompt_strength: { type: "slider", min: 0, max: 1, step: 0.05, default: 0.85 },
      output_format: {type: "select",
        options: ["webp", "jpg", "png"],
        default: "png"
      },
      output_quality: { type: "slider", min: 1, max: 100, step: 1, default: 80}
    }
  },
  "stable-diffusion-3.5-large": {
    name: "Stable Diffusion 3.5 Large",
    price: 15,
    params: {
      negative_prompt: { type: "text", default: "" },
      seed: { type: "number" },
      aspect_ratio: {
        type: "select",
        options: ["1:1", "16:9", "9:16", "4:3", "3:4", "5:4", "4:5", "21:9", "9:21", "custom"],
        default: "4:3"
      },
      cfg_scale: { type: "slider", min: 1, max: 30, step: 0.5, default: 7.5 },
      steps: { type: "slider", min: 1, max: 150, step: 1, default: 50 },       
      output_format: { type: "select", options: ["jpeg", "png"], default: "png" },
      output_quality: { type: "slider", min: 1, max: 100, step: 1, default: 90 }
    }
  },
  "stable-diffusion-3.5-large-turbo": {
    name: "Stable Diffusion 3.5 Large Turbo",
    price: 25,
    params: {
      seed: { type: "number" },
      aspect_ratio: { 
        type: "select",
        options: ["1:1", "16:9", "21:9", "3:2", "2:3", "4:5", "5:4", "3:4", "4:3", "9:16", "9:21", "custom"],
        default: "4:3"
      },
      cfg: { type: "slider", min: 1, max: 20, step: 1, default: 1 },
      steps: { type: "slider", min: 1, max: 10, step: 1, default: 4 },
      prompt_strength: { type: "slider", min: 0, max: 1, step: 0.05, default: 0.85 },
      output_format: {type: "select",
        options: ["webp", "jpg", "png"],
        default: "png"
      },
      output_quality: { type: "slider", min: 1, max: 100, step: 1, default: 80}
    }
  },
  "sticker-maker": {
    name: "Sticker Maker",
    price: 119,
    params: {
      number_of_images: { type: "number", min: 1, max: 4, default: 4 },
      negative_prompt: { type: "text", default: "" },
      width: { type: "number", min: 64, max: 2048, step: 32, default: 1152 },
      height: { type: "number", min: 64, max: 2048, step: 32, default: 1152 },
      steps: { type: "slider", min: 1, max: 100, step: 1, default: 17 },
      output_format: {type: "select",
        options: ["webp", "jpg", "png"],
        default: "png"
      },
      output_quality: { type: "slider", min: 1, max: 100, step: 1, default: 80}
    }
  }
};

interface ParamConfig {
  type: string;
  default?: string | number | boolean;
  min?: number;
  max?: number;
  step?: number;
  options?: string[];
}

interface ModelConfig {
  name: string;
  price: number;
  params: { [key: string]: ParamConfig };
}

const ModelSelector: React.FC = () => {
  const [error, setError] = useState<string | null>(null);
  const [selectedModel, setSelectedModel] = useState<string>("photon-flash");
  const [prompt, setPrompt] = useState<string>('');
  const [negativePrompt, setNegativePrompt] = useState<string>('');
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const clearImages = () => {
    const container = document.getElementById('imageContainer');
    if (container) {
      while (container.firstChild) {
        container.removeChild(container.firstChild);
      }
    }
  };
  const [params, setParams] = useState<{ [key: string]: string | number | boolean }>(() => {
    const firstModelKey: keyof typeof modelConfigs = Object.keys(modelConfigs)[0] as keyof typeof modelConfigs;
    const model = modelConfigs[firstModelKey];
    return Object.fromEntries(
      Object.entries(model.params).map(([key, config]) => {
        const typedConfig = config as ParamConfig;
        return [key, typedConfig.default ?? ''];
      })
    );
  });

  useEffect(() => {
    // Only load from localStorage when component mounts
    const savedPrompt = localStorage.getItem('prompt');
    const savedNegativePrompt = localStorage.getItem('negativePrompt');

    if (savedPrompt) setPrompt(savedPrompt);
    if (savedNegativePrompt) setNegativePrompt(savedNegativePrompt);

    const model = modelConfigs[selectedModel] as ModelConfig;
    const newParams = Object.fromEntries(
      Object.entries(model.params).map(([key, config]) => {
        const typedConfig = config as ParamConfig;
        return [key, typedConfig.default ?? ''];
      })
    );

    setParams(prev => ({
      ...prev,
      ...newParams
    }));
  }, [selectedModel]);

  const handleModelChange = (event: SelectChangeEvent) => {
    setSelectedModel(event.target.value as string);
  };

  const handleParamChange = (key: string, value: string | number | boolean) => {
    if (key === 'output_format' && value === 'png') {
      // If changing to png, reset output_quality to its default
      const modelConfig = modelConfigs[selectedModel];
      const outputQualityConfig = modelConfig.params['output_quality'] as ParamConfig;
      setParams(prev => ({
        ...prev,
        [key]: value,
        output_quality: outputQualityConfig.default ?? 80
      }));
    } else if (selectedModel === 'material-diffusion' && (key === 'width' || key === 'height')) {
      const prevWidth = parseInt(params['width'] as string);
      const prevHeight = parseInt(params['height'] as string);
      let newWidth = key === 'width' ? parseInt(value as string) : prevWidth;
      let newHeight = key === 'height' ? parseInt(value as string) : prevHeight;
  
      // Adjust width if changed and it's over 768
      if (key === 'width' && newWidth > 768) {
        newHeight = newHeight > 768 ? 768 : newHeight;
      }
      // Adjust height if changed and it's over 768
      if (key === 'height' && newHeight > 768) {
        newWidth = newWidth > 768 ? 768 : newWidth;
      }
  
      setParams(prev => ({
        ...prev,
        width: String(newWidth),
        height: String(newHeight)
      }));
    } else {
      setParams(prev => ({ ...prev, [key]: value }));
    }
  };

  const renderParam = (key: string, config: ParamConfig) => {
    // only show output_quality when output_format is not png
    if (key === 'output_quality') {
      const currentFormat = params['output_format'] as string || config.default as string;
      if (currentFormat === 'png') {
        return null; // Don't render output_quality for png format
      }
    }
    const defaultValue = config.default ?? '';
    const label = key === 'seed' ? key : 
    ['image_reference_url', 'style_reference_url', 'character_reference_url'].includes(key) ? 
      key : 
      `${key} (Default: ${defaultValue})`;

    switch (config.type) {
      case 'text':
        return (
          <Box sx={{ width: '100%', mt: 2, display: 'flex', flexDirection: 'column', justifyContent: 'center', height: '56px' }}>
            <TextField 
              fullWidth
              label={key === 'negative_prompt' ? 'Negative Prompt' : label}
              value={params[key] as string || ''} 
              onChange={(e) => handleParamChange(key, e.target.value)} 
            />
          </Box>
        );
      case 'number':
        return (
          <Box sx={{ width: '100%', mt: 2, display: 'flex', flexDirection: 'column', justifyContent: 'center', height: '56px' }}>
            <TextField 
              fullWidth
              type="number"
              label={label}
              value={params[key] as number || defaultValue} 
              onChange={(e) => handleParamChange(key, Number(e.target.value))}
              InputProps={{ inputProps: { min: config.min, max: config.max, step: config.step } }}
            />
          </Box>
        );
      case 'slider':
        return (
          // <Box sx={{ width: '100%', mt: 2 }}>
          <Box sx={{ width: '100%', mt: 2, display: 'flex', flexDirection: 'column', justifyContent: 'center', height: '56px' }}>
            <Typography id={`slider-${key}`} gutterBottom>
              {/* {label} (Current: {params[key] || defaultValue}, Default: {defaultValue}) */}
              {label}
            </Typography>
            <Slider 
              aria-labelledby={`slider-${key}`}
              value={params[key] as number || (defaultValue as number)} 
              onChange={(_, value) => handleParamChange(key, value as number)}
              min={config.min} 
              max={config.max} 
              step={config.step}
              valueLabelDisplay="auto"
            />
          </Box>
        );
      case 'select':
        return (
          <Box sx={{ width: '100%', mt: 2, display: 'flex', flexDirection: 'column', justifyContent: 'center', height: '56px' }}>
            <FormControl fullWidth>
              <InputLabel id={`${key}-label`}>{label}</InputLabel>
              <Select 
                labelId={`${key}-label`}
                value={params[key] as string || defaultValue as string} 
                onChange={(e) => handleParamChange(key, e.target.value)}
                label={label}
              >
                {config.options?.map((option, index) => (
                  <MenuItem key={index} value={option}>{option}</MenuItem>
                ))}
              </Select>
            </FormControl>
          </Box>
        );
      case 'boolean':
        return (
          <Box sx={{ width: '100%', mt: 2, display: 'flex', flexDirection: 'column', justifyContent: 'center', height: '56px' }}>
            <FormControlLabel 
              control={
                <Checkbox 
                  checked={Boolean(params[key])} 
                  onChange={(e) => handleParamChange(key, e.target.checked)}
                />
              }
              label={label}
            />
          </Box>
        );
      default:
        return null;
    }
  };

  interface GenerationPayload {
    model: string;
    prompt: string;
    // negative_prompt: string;
    [key: string]: string | number | boolean | undefined;
  } 
 
  const handleSubmit = () => {
    // console.log('Selected Model (exact):', JSON.stringify(selectedModel));
    setIsLoading(true);
    setError(null); // Clear any previous errors before starting a new request
    const modelConfig = modelConfigs[selectedModel];
    const payload: GenerationPayload = {
      model: selectedModel,
      prompt: prompt
      // negative_prompt: negativePrompt
    };
  
    Object.keys(modelConfig.params).forEach(key => {
      if (params[key] !== undefined && params[key] !== '') {
        payload[key] = params[key] as string | number | boolean;
      }
    });
  
    fetch('http://192.168.0.66:5000/api/generate', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
    })
    .then(response => {
      if (!response.ok) {
        // Read the error message from the response body if possible
        return response.text().then(text => {
          throw new Error(`HTTP error! status: ${response.status} - ${text || 'Unknown server error'}`);
        });
      }
      return response.json();
    })
    .then(data => {
      console.log('Success:', data);
      if (data.url) {
        const imageUrls = Array.isArray(data.url) ? data.url : [data.url];
        
        return fetch('http://192.168.0.66:5000/api/saveImages', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ urls: imageUrls, metadata: payload }),
        })
        .then(saveResponse => {
          if (!saveResponse.ok) {
            throw new Error('Failed to save images on server');
          }
          return saveResponse.json();
        })
        .then(saveData => {
          // Use the saved filenames for displaying images
          const savedFiles = saveData.saved || [];
          savedFiles.forEach((filename: string) => {
            const img = document.createElement('img');
            img.src = `http://192.168.0.66:5000/images/saved_images/${filename}`;
            
            const container = document.getElementById('imageContainer');
            if (container) {
              container.appendChild(img);
            } else {
              console.error("Container with ID 'imageContainer' not found in the DOM");
            }
          });
          
          console.log('Images saved and displayed successfully');
        });
      }
    })
    .catch((error) => {
      // Here we combine the general error with any specific message from the server
      setError(`Error: ${error.message}`);
      console.error('Error:', error);
    })
    .finally(() => {
      setIsLoading(false);
    });
  };

  const model: ModelConfig = modelConfigs[selectedModel];

  return (
    <ThemeProvider theme={materialDarkTheme}>
      <div style={{ position: 'relative' }}>
        <div className="background-container"></div>
        <div className="content-container">
          <Box sx={{ maxWidth: 1200, margin: '0 auto', padding: 2 }}>
            <Card>
              <CardHeader title="AI Image Generation" />
              <CardContent>
                <Grid2 container spacing={2}>
                  {/* Model Selection */}
                  <Grid2 size={12}>
                    <FormControl fullWidth>
                      <InputLabel id="model-select-label">Select Model</InputLabel>
                      <Select 
                        labelId="model-select-label"
                        value={selectedModel} 
                        onChange={handleModelChange}
                        label="Select Model"
                      >
                        {Object.entries(modelConfigs).map(([key, value]) => (
                          <MenuItem key={key} value={key}>
                            {value.name} - ({value.price} / $1)
                          </MenuItem>
                        ))}
                      </Select>
                    </FormControl>
                  </Grid2>
  
                  {/* Prompt Input */}
                  <Grid2 size={12}>
                    <TextField 
                      fullWidth 
                      label="Prompt" 
                      value={prompt} 
                      onChange={(e) => {
                        setPrompt(e.target.value);
                        localStorage.setItem('prompt', e.target.value);
                      }} 
                      placeholder="Enter your prompt here..."
                    />
                  </Grid2>
  
                  {/* Negative Prompt */}
                  {model.params['negative_prompt'] && (
                    <Grid2 size={12}>
                      <TextField 
                        fullWidth
                        label="Negative Prompt"
                        value={negativePrompt}
                        onChange={(e) => {
                          setNegativePrompt(e.target.value);
                          localStorage.setItem('negativePrompt', e.target.value);
                        }}
                      />
                    </Grid2>
                  )}
  
                  {/* Model Parameters */}
                  <Grid2 size={12}>
                    <Typography variant="h6" component="div">
                      Model Parameters
                    </Typography>
                  </Grid2>
                  {Object.keys(model.params)
                    .filter(key => 
                      key !== 'negative_prompt' && 
                      key !== 'output_format' && 
                      key !== 'output_quality' &&
                      typeof model.params[key].default !== 'boolean' // Exclude boolean params here
                    )
                    .reduce((rows: React.ReactNode[], key, index) => {
                      if (index % 2 === 0) {
                        const secondKey = Object.keys(model.params)
                          .filter(k => 
                            k !== 'negative_prompt' && 
                            k !== 'output_format' && 
                            k !== 'output_quality' &&
                            typeof model.params[k].default !== 'boolean'
                          )[index + 1];
                        
                        rows.push(
                          <Grid2 container size={12} spacing={2} key={index}>
                            <Grid2 size={{ xs: 12, sm: 6 }} sx={{ display: 'flex', alignItems: 'center' }}>
                              {renderParam(key, model.params[key])}
                            </Grid2>
                            {model.params[secondKey] && (
                              <Grid2 size={{ xs: 12, sm: 6 }} sx={{ display: 'flex', alignItems: 'center' }}>
                                {renderParam(secondKey, model.params[secondKey])}
                              </Grid2>
                            )}
                          </Grid2>
                        );
                      }
                      return rows;
                    }, [] as React.ReactNode[])}
  
                  {/* Boolean Parameters */}
                  {Object.keys(model.params)
                    .filter(key => typeof model.params[key].default === 'boolean') // Only boolean params
                    .reduce((rows: React.ReactNode[], key, index) => {
                      if (index % 2 === 0) {
                        const secondKey = Object.keys(model.params)
                          .filter(k => typeof model.params[k].default === 'boolean')[index + 1];
                        
                        rows.push(
                          <Grid2 container size={12} spacing={2} key={`boolean-${index}`}>
                            <Grid2 size={{ xs: 12, sm: 6 }} sx={{ display: 'flex', alignItems: 'center' }}>
                              {renderParam(key, model.params[key])}
                            </Grid2>
                            {model.params[secondKey] && (
                              <Grid2 size={{ xs: 12, sm: 6 }} sx={{ display: 'flex', alignItems: 'center' }}>
                                {renderParam(secondKey, model.params[secondKey])}
                              </Grid2>
                            )}
                          </Grid2>
                        );
                      }
                      return rows;
                    }, [] as React.ReactNode[])}
  
                  {/* Output Format and Quality */}
                  {(model.params['output_format'] || model.params['output_quality']) && (
                    <Grid2 container size={12} spacing={2}>
                      {model.params['output_format'] && (
                        <Grid2 size={{ xs: 12, sm: 6 }} sx={{ display: 'flex', alignItems: 'center' }}>
                          {renderParam('output_format', model.params['output_format'])}
                        </Grid2>
                      )}
                      {model.params['output_quality'] && (
                        <Grid2 size={{ xs: 12, sm: 6 }} sx={{ display: 'flex', alignItems: 'center' }}>
                          {renderParam('output_quality', model.params['output_quality'])}
                        </Grid2>
                      )}
                    </Grid2>
                  )}
  
                  {/* Action Buttons */}
                  <Grid2 container size={12} justifyContent="space-between" alignItems="center" spacing={2}>
                    <Grid2>
                      <Button 
                        variant="contained" 
                        color="primary" 
                        onClick={handleSubmit}
                        disabled={isLoading}
                      >
                        {isLoading ? 'Generating...' : 'Generate Image'}
                      </Button>
                    </Grid2>
                    <Grid2>
                      <Button 
                        variant="outlined" 
                        color="secondary" 
                        onClick={clearImages}
                      >
                        Clear Images
                      </Button>
                    </Grid2>
                    <Grid2>
                      <Button 
                        variant="outlined" 
                        color="primary"
                        component="a"
                        href="http://192.168.0.66/images/"
                        target="_blank"  
                        rel="noopener noreferrer"
                      >
                        View Saved Images
                      </Button>
                    </Grid2>
                  </Grid2>
  
                  {/* Error Display */}
                  {error && (
                    <Grid2 size={12}>
                      <Typography variant="body2" color="error" sx={{ mt: 2 }}>
                        {error}
                      </Typography>
                    </Grid2>
                  )}
  
                  {/* Image Container */}
                  <Grid2 size={12}>
                    <Box id="imageContainer" sx={{ display: 'flex', flexWrap: 'wrap', gap: 2, mt: 2 }}>
                      {/* Images will be dynamically added here */}
                    </Box>
                  </Grid2>
                </Grid2>
              </CardContent>
            </Card>
          </Box>
        </div>
      </div>
    </ThemeProvider>
  );  
};
  
export default ModelSelector;