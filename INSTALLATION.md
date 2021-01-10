####  How to create wheel installation file:

Navigate to the project root folder and from the terminal:
> `pip install wheel`

Non versioned, dev-build:  
> `python setup.py bdist_wheel`

Versioned, release-like:
> `python setup.py bdist_wheel --version=vX.X --update-link=LINK

Link is an url to github api page which leads to releases.

For example: "https://api.github.com/repos/hapylestat/openstack_cli/releases"

#### To update integrated apputils tools
> `python setup.py apputils`

#### Wheel location
Resulting file would be placed to the `root/dist/` folder