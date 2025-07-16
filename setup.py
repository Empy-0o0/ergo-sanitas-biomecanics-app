#!/usr/bin/env python3
"""
Setup script para la aplicación Ergo SaniTas SpA
Análisis Biomecánico de Saltos
"""

from setuptools import setup, find_packages
import os

# Leer el archivo README para la descripción larga
def read_readme():
    with open("README.md", "r", encoding="utf-8") as fh:
        return fh.read()

# Leer los requisitos del archivo requirements.txt
def read_requirements():
    with open("requirements.txt", "r", encoding="utf-8") as fh:
        return [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="ergo-sanitas-app",
    version="1.0.0",
    author="Ergo SaniTas SpA",
    author_email="info@ergosanitas.cl",
    description="Aplicación móvil profesional para análisis biomecánico de saltos",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/ergosanitas/jump-analysis-app",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Healthcare Industry",
        "Topic :: Scientific/Engineering :: Medical Science Apps.",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Operating System :: OS Independent",
        "Environment :: X11 Applications",
        "Framework :: Kivy",
    ],
    python_requires=">=3.8",
    install_requires=read_requirements(),
    extras_require={
        "dev": [
            "pytest>=7.4.3",
            "pytest-cov>=4.1.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.5.0",
        ],
        "mobile": [
            "buildozer>=1.5.0",
            "kivy-ios>=1.1.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "ergo-sanitas=main:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["*.kv", "*.yaml", "*.json", "*.md"],
    },
    data_files=[
        ("config", ["config_Saltos.yaml"]),
        ("ui", ["app.kv"]),
        ("docs", ["README.md"]),
    ],
    keywords=[
        "biomechanics",
        "sports medicine",
        "jump analysis",
        "kivy",
        "mobile app",
        "healthcare",
        "motion analysis",
        "computer vision",
    ],
    project_urls={
        "Bug Reports": "https://github.com/ergosanitas/jump-analysis-app/issues",
        "Source": "https://github.com/ergosanitas/jump-analysis-app",
        "Documentation": "https://github.com/ergosanitas/jump-analysis-app/wiki",
        "Company": "https://www.ergosanitas.cl",
    },
)
