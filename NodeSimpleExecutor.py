"""
Author: "KERRY-YUAN",
Title: "NodeSimpleExecutor",
Git-clone: "https://github.com/KERRY-YUAN/ComfyUI_Simple_Executor",
This node package contains automatic sampler setting according to model name in ComfyUI, adjusting image size according to specific constraints and some other nodes.
本节点包包含在 ComfyUI 中根据模型名称自动处理采样器设置、按特定约束调整图像大小和一些其他节点。。
"""

import torch
import math
import numpy as np
from PIL import Image
from comfy.samplers import KSampler

#--------------------------------------------------------------------------------------------------------------#
#Based on the input model name, automatically match the configuration parameters of step count, CFG value, and sampler name through "Auto, Light, Normal, User".
#根据输入的模型名称，通过“Auto、If_include、Else、User”自动化匹配步数、CFG值和采样器名称的配置参数。

class NodeAutoSampler:
    @classmethod
    def INPUT_TYPES(s):
        # 获取 ComfyUI 中的采样器名称列表
        sampler_names = KSampler.SAMPLERS
        return {
            "required": {
                "ckpt_name": ("STRING", {"default": ""}),
                "mode": (["Auto", "If_include", "Else", "User"], {"default": "Auto"})
            },
            "optional": {
                "if_include": ("STRING", {"default": "light,turbo"}),
                "if_steps": ("INT", {"default": 5, "min": 1, "max": 1000}),
                "if_cfg": ("FLOAT", {"default": 2.0, "min": 0.1, "max": 100.0}),
                "if_sampler": (sampler_names, {"default": "dpmpp_sde"}),
                "else_steps": ("INT", {"default": 30, "min": 1, "max": 1000}),
                "else_cfg": ("FLOAT", {"default": 5.0, "min": 0.1, "max": 100.0}),
                "else_sampler": (sampler_names, {"default": "dpmpp_2m_sde"}),
                "user_steps": ("INT", {"default": 20, "min": 1, "max": 1000}),
                "user_cfg": ("FLOAT", {"default": 3.5, "min": 0.1, "max": 100.0}),
                "user_sampler": (sampler_names, {"default": "dpmpp_2m_sde"})
            }
        }

    RETURN_TYPES = ("INT", "FLOAT", "STRING", "STRING")
    RETURN_NAMES = ("steps", "cfg", "sampler", "text")
    FUNCTION = "generate_dynamic_settings"
    CATEGORY = "custom"

    def generate_dynamic_settings(self, ckpt_name, mode, **kwargs):
        mode_priority = {
            "If_include": "1", "Else": "2", "User": "3", "Auto": "0"
        }
        selected_mode = mode_priority[mode]
        
        if selected_mode == "0":
            input_str = str(ckpt_name).lower()
            keywords = [k.strip().lower() for k in kwargs.get("if_include", "").split(',')]
            selected_mode = "1" if any(k in input_str for k in keywords) else \
                          "3" if "userconfig" in input_str else "2"

        config_map = {
            "1": (kwargs["if_steps"], kwargs["if_cfg"], kwargs["if_sampler"]),
            "2": (kwargs["else_steps"], kwargs["else_cfg"], kwargs["else_sampler"]),
            "3": (kwargs["user_steps"], kwargs["user_cfg"], kwargs["user_sampler"])
        }
        steps, cfg, sampler = config_map.get(selected_mode, (30, 5.0, "dpmpp_2m_sde"))
        
        return (steps, cfg, sampler, f"{steps};{cfg};{sampler}")

#---------------------------------------------------------------------------------------------------------------------------------------------------#
#Resizes the image based on the target short side (`num`), maintaining aspect ratio, with final width and height both rounded up (ceil) to the nearest multiple of 16.
#根据目标短边 (`num`) 调整图像大小，保持宽高比，最终宽高均向上取整为 16 的倍数。

class NodeResizeImage:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "shortside": ("INT", {"default": 1024, "min": 560, "max": 9600, "step": 16}),
            }
        }
    RETURN_TYPES = ("IMAGE", "INT", "INT")
    RETURN_NAMES = ("image_resize", "width", "height")
    FUNCTION = "resize_image"
    CATEGORY = "Image/Transform"

    def _tensor_to_pil(self, img_tensor):
        # Convert tensor to PIL Image / 将张量转换为 PIL 图像。
        img_np = img_tensor[0].cpu().numpy() * 255.0
        img_np = np.clip(img_np, 0, 255).astype(np.uint8)[:, :, :3]
        return Image.fromarray(img_np, 'RGB')

    def _pil_to_tensor(self, img_pil):
        # Convert PIL Image to tensor / 将 PIL 图像转换为张量。
        img_np = np.array(img_pil).astype(np.float32) / 255.0
        return torch.from_numpy(img_np).unsqueeze(0)

    def _calculate_dimensions(self, w, h, target):
        target = ((min(max(target, 560), 9600) + 15) // 16) * 16
        scale = target / min(w, h)
        new_w = round(w * scale) if w < h else ((round(w * scale) + 15) // 16) * 16
        new_h = ((round(h * scale) + 15) // 16) * 16 if w < h else target
        return new_w, new_h

    def resize_image(self, image, shortside):
        img_pil = self._tensor_to_pil(image)
        original_w, original_h = img_pil.size
        final_w, final_h = self._calculate_dimensions(original_w, original_h, shortside)
        if (original_w, original_h) != (final_w, final_h):
            img_pil = img_pil.resize((final_w, final_h), Image.Resampling.LANCZOS)
        return (self._pil_to_tensor(img_pil), final_w, final_h)

#---------------------------------------------------------------------------------------------------------------------------------------------------#    
#Node Registration / 节点注册

NODE_CLASS_MAPPINGS = {
    "NodeResizeImage": NodeResizeImage,
    "NodeAutoSampler": NodeAutoSampler,
}