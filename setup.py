from setuptools import setup, find_packages

setup(
    name="animate",
    description="Animate time stack from DL platform",
    version="0.2.3",
    packages=find_packages(),
    entry_points={"console_scripts": ["dl-animate=animate:main"]},
    setup_requires=["setuptools>40"],
    install_requires=[
        "descarteslabs[complete]>=0.24.0",
        "numpy>=1.16",
        "scipy>=1.1.0",
        "matplotlib>=3.0.0",
        "moviepy>=1.0.0",
        "pyfftw>=0.11.0",
        "scikit-image>=0.15.0",
        "Pillow>=2.2.2",
    ],
)
