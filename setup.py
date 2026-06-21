"""setup.py - football-predictor 安装配置。"""

from setuptools import setup, find_packages

setup(
    name="football-predictor",
    version="1.0.0",
    description="基于 Elo、阵容深度、战术匹配与动量修正的足球比分预测引擎",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    author="Football Predictor Team",
    packages=find_packages(exclude=("examples", "tests")),
    python_requires=">=3.9",
    extras_require={
        "dev": ["scipy>=1.6"],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
