# Global Catalog API Service
This service is a global catalog API of products and their packages available to be installed and run within a customer's Helion cloud.


## Development Guidelines

### Development Environment Setup
The easiest method is to setup a virtual environment. If you have `virtualenv` installed run `virtualenv .venv` (the `.venv` directory is gitignored) and `source .venv/bin/activate` to prepare the environment.
```
virtualenv .venv
source .venv/bin/activate
```

Once you have the environment ready you can run `make dev-setup` to install the dependencies.
```
make dev-setup
```

Before you can begin developing you'll need to setup a development configuration. Copy the file `development.ini.dst` to `development.ini`. In this file you can configure elements of the setup including the server and port it runs on.


### To run the API (web) server
To run as a serve in development mode use `make serve`. This will start up a server based on the configuration in `development.ini` and be setup to watch for code changes where it reloads the server.
```
make serve
```
*Note, this runs as a WSGI server and content is not persisted between requests.
To persist data an external data store will need to be used.*


### List Routes
The pyramid docs tell us how to [list routes](http://docs.pylonsproject.org/projects/pyramid/en/latest/narr/commandline.html#displaying-matching-views):
```
.venv/bin/proutes development.ini
```


### Hitting the API

#### Packages (collection) endpoint
- API url: "/v1/products/{product_id}/packages"
- Note: At this point the product_id is ignored at this point, so you can pass any string in as the product ID and these API calls will work.

* Action: none (root url)
```
➜  http --json GET http://0.0.0.0:8001
HTTP/1.1 200 OK
Content-Length: 23
Content-Type: application/json; charset=UTF-8
Date: Thu, 16 Jul 2015 16:16:18 GMT
Server: waitress

{
    "project": "globalapi"
}
```

* Action: Index
```
➜ http --json GET http://0.0.0.0:8001/v1/products/fake/packages
HTTP/1.1 200 OK
Content-Length: 240
Content-Type: application/json; charset=UTF-8
Date: Thu, 16 Jul 2015 16:17:32 GMT
Server: waitress

{
    "packages": [
        {
            "author": "foo.bar@corp.com",
            "icon": "nodejs.png",
            "name": "Node Env",
            "package": "node-env.tar.gz",
            "status": "available",
            "tags": [
                "node-env",
                "nodejs",
                "foo-bar",
                "ALS",
                "helion"
            ],
            "version": "0.0"
        }
    ],
    "status": 200
}
```

* Action: Upload
```
➜  http --form POST http://0.0.0.0:8001/v1/products/fake/packages \
fileupload@src/catalog-api/doc/sample_packages/node-env.tar.gz
HTTP/1.1 201 Created
Content-Length: 2
Content-Type: application/json; charset=UTF-8
Date: Thu, 16 Jul 2015 16:17:16 GMT
Server: waitress

{}
```


#### Packages (resource) endpoint
- API url: "/v1/products/{product_id}/packages/{package_id}"
- Note: At this point the product_id is ignored at this point, so you can pass any string in as the product ID and these API calls will work.

* Action: Get
The following cli command should open a browser and fill the URL with the below noted URL, and kick off the file download. Once complete, the file should be found in your downloads folder.
```
open http://0.0.0.0:8001/v1/products/fake/packages/dummy-package
```


### Unit Testing

Configuration options for `nose` and `coverage` are located in `setup.cfg`.

To run all unit tests:
```
nosetests
```

To run a single test:
```
nosetests globalapi/tests/swift_utils_tests.py
```

To view a coverage report with overall statistics and drilldown to detailed source code line coverage:
```
open cover/index.html
```

Links to Unit Testing resources:
[UnitTest](https://docs.python.org/2.7/library/unittest.html#module-unittest)
[Pyramid - Testing](http://docs.pylonsproject.org/projects/pyramid/en/latest/narr/testing.html)
[Dive Into Python](http://www.diveintopython.net/index.html)


### Package formats

* Format Options
```
# .tar.gz
tar -cvzf dummy_package.tar.gz ./dummy_package
# .tar file
tar -cvf dummy_package.tar ./dummy_package
```
