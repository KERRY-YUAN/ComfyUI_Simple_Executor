# ComfyUI_Simple_Executor
This node package includes nodes for automatically processing sampler settings based on model names and resizing images with specific constraints within ComfyUI. Subject to occasional updates.
本节点包包含在 ComfyUI 中根据模型名称自动处理采样器设置、按特定约束调整图像大小和一些其他节点。不定时更新中。

## Node List

*   **NodeAutoSampler**: Automatically sets sampler settings.
*   **NodeResizeImage**: Resizes images, rounding dimensions up to multiples of 16.

## Node Descriptions

### 1. NodeAutoSampler (`NodeAutoSampler`)

*   **Description**: Sets sampler steps, CFG, and name based on the input `ckpt_name` and selected `mode` ("Auto", "If_include", "Else", "User"). Uses conditional logic based on keywords in `ckpt_name` or predefined settings.
*   **Category**: `custom`
*   **Key Inputs**:
    *   `ckpt_name` (STRING): Checkpoint name for logic.
    *   `mode` (COMBO): Operation mode.
    *   Optional settings for `if`, `else`, `user` conditions (steps, cfg, sampler).
*   **Outputs**: `steps` (INT), `cfg` (FLOAT), `sampler` (STRING), `text` (STRING summary).
*   **Usage**: Use 'Auto' mode with `if_include`='light' to apply specific settings (e.g., low steps/cfg) when 'light' is in the model name.
![image](https://github.com/KERRY-YUAN/ComfyUI_Simple_Executor/blob/main/Examples/NodeAutoSampler.png)

---
### 2. NodeResizeImage (`NodeResizeImage`)

*   **Description**: Resizes an image based on a target `shortside` length, maintaining aspect ratio. Final width and height are both rounded *up* (ceil) to the nearest multiple of 16.
*   **Category**: `Image/Transform`
*   **Inputs**:
    *   `image` (IMAGE): Image to resize.
    *   `shortside` (INT): Target length for the shorter side.
*   **Outputs**:
    *   `image_resize` (IMAGE): Resized image.
    *   `width` (INT): Final width (multiple of 16).
    *   `height` (INT): Final height (multiple of 16).
*   **Usage**: Resize 800x600 with `shortside`=768 results in 1024x768 output dimensions, as both are rounded up to the nearest 16x multiple.
![image](https://github.com/KERRY-YUAN/ComfyUI_Simple_Executor/blob/main/Examples/NodeResizeImage_16ceil.png)

---

## Installation Steps

1.  Clone the repository into ComfyUI's `custom_nodes` directory:
    cd /path/to/comfyui/custom_nodes
    git clone https://github.com/KERRY-YUAN/ComfyUI_Simple_Executor.git
2.  Restart ComfyUI.

---
---

## 节点列表

*   **NodeAutoSampler**: 自动设置采样器参数。
*   **NodeResizeImage**: 调整图像大小，并将尺寸向上取整至16的倍数。

## 节点说明

### 1. NodeAutoSampler (`NodeAutoSampler`)

*   **描述**: 根据输入的 `ckpt_name` 和选择的 `mode`（"Auto", "If_include", "Else", "User"）设置采样器步数、CFG 和名称。基于 `ckpt_name` 中的关键字或预定义设置使用条件逻辑。
*   **分类**: `custom`
*   **主要输入**:
    *   `ckpt_name` (STRING): 用于逻辑判断的检查点名称。
    *   `mode` (下拉框): 操作模式。
    *   用于 `if`, `else`, `user` 条件的可选设置 (步数, cfg, 采样器)。
*   **输出**: `steps` (INT), `cfg` (FLOAT), `sampler` (STRING), `text` (STRING 摘要)。
*   **使用**: 使用 'Auto' 模式配合 `if_include`='light'，可在模型名称含 'light' 时应用特定设置（如低步数/CFG）。

---
### 2. NodeResizeImage (`NodeResizeImage`)

*   **描述**: 根据目标 `shortside` 长度调整图像大小，保持宽高比。最终宽度和高度都将向上（ceil）取整至最接近的 16 的倍数。
*   **分类**: `Image/Transform`
*   **输入**:
    *   `image` (IMAGE): 待调整图像。
    *   `shortside` (INT): 目标短边长度。
*   **输出**:
    *   `image_resize` (IMAGE): 调整后的图像。
    *   `width` (INT): 最终宽度（16的倍数）。
    *   `height` (INT): 最终高度（16的倍数）。
*   **使用**: 使用 `shortside`=768 调整 800x600 图像，输出尺寸为 1024x768，因为宽高都向上取整至最接近的16倍数。

---

## 安装步骤

1.  将仓库克隆到 ComfyUI 的 `custom_nodes` 目录：
    cd /path/to/comfyui/custom_nodes
    git clone https://github.com/KERRY-YUAN/ComfyUI_Simple_Executor.git
2.  重启 ComfyUI。