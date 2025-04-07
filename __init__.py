"""
Author: "KERRY-YUAN",
Title: "NodeSimpleExecutor",
Git-clone: "https://github.com/KERRY-YUAN/ComfyUI_Simple_Executor",
This node package contains automatic sampler setting according to model name in ComfyUI, adjusting image size according to specific constraints and some other nodes.
本节点包包含在 ComfyUI 中根据模型名称自动处理采样器设置、按特定约束调整图像大小和一些其他节点。。
"""

from .NodeSimpleExecutor import NODE_CLASS_MAPPINGS

__all__ = ['NODE_CLASS_MAPPINGS']