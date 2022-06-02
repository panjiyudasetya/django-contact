import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="django-contact",
    version="0.1.0",
    author="Panji Y. Wiwaha",
    author_email="panjiyudasetya@gmail.com",
    description="A Django app to manage user's contact list",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/panjiyudasetya/django-contacts",
    project_urls={
        "Bug Tracker": "https://github.com/panjiyudasetya/django-contacts/issues",
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    packages=setuptools.find_packages(),
    python_requires=">=3.6",
    install_requires=[
        'django',
        'djangorestframework',
        'django-phonenumber-field',
        'phonenumbers'
    ]
)
