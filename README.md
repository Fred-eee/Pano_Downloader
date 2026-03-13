# Pano_Downloader
A lightweight Python tool to download and stitch Baidu Maps street view panoramas into high-resolution images.

## 📜 说明
想下载百度的历史全景图作为回忆保存在笔记中，直接截图体积太大且不完整，找了一圈发现没有纯免费的类似软件（*这么简单的软件还要收费TMD*），所以就用AI搞了一个用来下载百度全景图，原理是通过获取碎片图再组合的简单程序，顺便发出来节省你的一点时间。

[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)


## 🌟 功能
- **断点续传**：支持下载暂停与继续，程序会自动跳过本地已存在的瓦片图，无需重复下载。
- **自动解析**：支持直接输入对应的百度地图全景链接。
- **图形界面**：基于 Tkinter 的原生 GUI，无需命令行操作，简单直观。
- **声明**：仅支持单张下载（不支持批量），适合保存特定的地点。

## 🚀 安装
```bash
pip install -r requirements.txt
```
## 🛠️ 使用
```bash
python main.py
```
或者直接双击**main.py**文件直接运行。

**获取 ID**：打开百度地图全景模式，定位到你需要的时间和地点。

**粘贴链接**：直接复制浏览器地址栏的网址，点击软件中的“清空并粘贴”按钮。

**开始下载**：设置好保存路径（建议选择一个空文件夹），点击“下载并合成”（**参数推荐保持默认**）。

**获取结果**：程序运行完成后，会自动清理缓存切片并生成最终的 JPG 图片。

## 📜 开源协议
本项目采用 GPL-3.0 协议开源。欢迎大家在遵守协议的基础上进行改进。

声明：本工具仅供学习研究和个人收藏使用，请勿用于商业用途或大规模非法抓取。
