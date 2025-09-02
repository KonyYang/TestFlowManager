from setuptools import setup, find_packages

setup(
    name="testflow-manager",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "PyQt5>=5.15.0",
        "requests>=2.25.0",
    ],
    entry_points={
        'console_scripts': [
            'testflow-manager=app.application:main',
        ],
    },
    author="Your Name",
    author_email="your.email@example.com",
    description="A tool for managing test workflows",
    long_description=open('README.md').read(),
    long_description_content_type="text/markdown",
    url="https://github.com/your-username/testflow-manager",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.7',
)
