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

class NodeImageResize:
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
#According to the image intelligently processed based on the short side, automatically generate parameters for adjusting size(16x), latent space, and magnification size(8x). 
#根据目标短边智能处理图像，生成调整尺寸(16的倍数)、空潜在空间及放大参数(8的倍数)。

class NodeImagePre:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "shortside": ("INT", {"default": 800, "min": 560, "max": 9600, "step": 16}),
                "batch": ("INT", {"default": 1, "min": 1}),
                "ups": ("FLOAT", {"default": 1.0, "min": 0.1})
            },
            "optional": {"mask": ("MASK",)}
        }

    RETURN_TYPES = ("IMAGE", "MASK", "LATENT", "INT", "INT", "INT", "INT", "INT")
    RETURN_NAMES = ("image_resize", "mask_resize", "empty_latent", "batch",
                   "width_resize", "height_resize", "width_ups", "height_ups")
    FUNCTION = "execute"
    CATEGORY = "Image/Transform" 

    def _process_size(self, w, h, target, divisor):
        scale = target / min(w, h)
        new_w = max(divisor, ((round(w * scale) + divisor - 1) // divisor) * divisor)
        new_h = max(divisor, ((round(h * scale) + divisor - 1) // divisor) * divisor)
        return new_w, new_h

    def _resize_tensor(self, tensor, size):
        if tensor is None:
            return None
        img_np = tensor[0].cpu().numpy()
        img_np = np.clip(img_np * 255. if np.max(img_np) <= 1.0 else img_np, 0, 255).astype(np.uint8)
        pil_mode = 'RGB' if img_np.ndim == 3 and img_np.shape[2] >= 3 else 'L'
        img_np_proc = img_np[:, :, :3] if pil_mode == 'RGB' else img_np
        img = Image.fromarray(img_np_proc, pil_mode)
        img = img.resize(size, Image.Resampling.LANCZOS) if img.size != size else img
        img_out_np = np.array(img).astype(np.float32) / 255.0
        img_out_np = img_out_np[..., np.newaxis] if img_out_np.ndim == 2 else img_out_np
        return torch.from_numpy(img_out_np).unsqueeze(0)

    def execute(self, image, shortside, batch, ups, mask=None):
        _, h, w, _ = image.shape
        resize_w, resize_h = self._process_size(w, h, shortside, 16)
        image_out = self._resize_tensor(image, (resize_w, resize_h))
        mask_out_resized = self._resize_tensor(mask, (resize_w, resize_h))
        latent = {"samples": torch.zeros((batch, 4, max(1, resize_h // 8), max(1, resize_w // 8)))}
        ups_w, ups_h = self._process_size(resize_w, resize_h, max(8, int(min(resize_w, resize_h) * ups)), 8)
        return (image_out, mask_out_resized, latent, batch, resize_w, resize_h, ups_w, ups_h)


#---------------------------------------------------------------------------------------------------------------------------------------------------#    
#Node Registration / 节点注册

NODE_CLASS_MAPPINGS = {
    "NodeImageResize": NodeImageResize,
    "NodeImagePre": NodeImagePre,
    "NodeAutoSampler": NodeAutoSampler,
}