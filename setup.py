import setuptools

VERSION = '2.0.0'

setuptools.setup(
    name="pxl_camera",
    version=VERSION,
    author="Pasko Zdilar",
    author_email="pasko.zdilar@pixlbrain.ai",
    description="SDK for camera management, capturing, configuration and frame preprocessing.",
    long_description_content_type="text/markdown",
    url="https://github.com/pxlbrain/core-camera-sdk.git",
    packages=setuptools.find_packages(),
    zip_safe=False,
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: Pixlbrain",
        "Operating System :: GNU/Linux",
    ],
    install_requires=[
        "pyudev",
        "opencv-python",
        "pxl-actor @ git+ssh://git@github.com/paskozdilar/pxl-actor.git",
    ],
)
