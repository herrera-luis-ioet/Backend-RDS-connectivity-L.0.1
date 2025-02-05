from setuptools import setup, find_packages

setup(
    name="product_order_api",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "fastapi==0.115.0",
        "uvicorn==0.25.0",
        "sqlalchemy==2.0.25",
        "pymysql==1.1.0",
        "python-dotenv==1.0.0",
    ],
    python_requires=">=3.9",
)
