# pip-tools

## First steps
Make sure that you have created a virtual environment locally and that it is activated. Then manually install pip-tools with `pip install pip-tools`

## How to specify which packages to use
Put these in the `.in` files, either dev or main depending on the need. You can also pin the versions in the `.in` file if you need to (but the compiled output `.txt` will serve as the primary way to track and pin the dependencies in a detailed way).

## How to generate the .txt requirements file
`pip-compile requirements/main.in`
`pip-compile requirements/dev.in`
The dev requirements will also pull in the main requirements.

## How to use the requirements file
Install the `.txt` file, either main or dev, by pointing to the file inside the `requirements` folder:
`pip install -r main.txt`
Note that the pip-tools docs recommend using `pip-sync` to install the dependencies in your virtualenv, that functionality can be flaky, so it's easier to just use pip as shown above.