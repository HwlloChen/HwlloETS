# HwlloETS

## Intro

基于adb和机器视觉的自动E听说作业完成工具  
目前在开发阶段，当前仅支持跟读作业。  

需要用到一个安卓模拟器，通过模拟点击和语音的方式来实现自动朗读。  

推荐使用Mumu模拟器  

## Installation

### 准备条件

- Python环境，推荐3.10以上
- 一台安卓设备或模拟器(推荐Mumu)
- 如果你使用了模拟器，那么推荐使用[VBCABLE](https://vb-audio.com/Cable/index.htm)来模拟麦克风输入，实现更好的效果
- [Tesseract OCR](https://github.com/UB-Mannheim/tesseract/wiki) 安装

### 安装程序

#### **Step1: 克隆项目并进入目录**
```bash
git clone https://github.com/HwlloChen/HwlloETS.git
cd HwlloETS
```

#### **Step2: 创建虚拟环境(可选)**
```bash
python -m venv .venv
```
- 请参照 [官方文档](https://docs.python.org/3/library/venv.html#how-venvs-work) 根据你的系统激活venv环境

#### **Step3: 安装必要依赖**

```bash
pip install -r requirements.txt
```

#### **Step4: 启动程序**
```bash
python main.py
```
## Tips

- 可以根据任务基类，在`tasks`下创建自定义任务
- 可以使用`python -m utils.debug_tool`来方便的调试并得到坐标位置，之后根据自己设备情况修改任务