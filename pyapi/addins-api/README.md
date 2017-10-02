# Addins Catalog API Service
This service is a local catalog API of addins installed within a customer's Helion cloud.


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

#### Endpoints

##### Catalog Endpoint ("/v1/catalog")

Action: Index
```
➜  curl -i \
  -H "Accept: application/json" \
  -H "Content-Type: application/json" \
  -X GET http://0.0.0.0:8002/v1/catalog
HTTP/1.1 200 OK
Date: Wed, 01 Jul 2015 04:14:45 GMT
Server: Apache/2.4.7 (Ubuntu)
Content-Length: 252
Content-Type: application/json; charset=UTF-8

{"status": 200, "packages": ["status", "packages", {"status": "installed", "hash": "421e105dda2580a39b21edeaf9b035de", "name": "test_vendor_package.json", "bytes": 92, "last_modified": "2015-06-22T15:54:25.722450", "content_type": "application/json"}]}
```


##### Catalog Item Endpoint ("/v1/catalog_item")

Action: Install
```
curl -i \
  -H "Accept: application/json" \
  -H "Content-Type: application/json" \
  -X POST \
  http://0.0.0.0:8002/v1/catalog_item?package_name=test_vendor_package
```


### Unit Testing

Configuration options for `nose` and `coverage` are located in `setup.cfg`.

To run all unit tests:
```
nosetests
```

To run a single test:
```
nosetests localapi/tests/swift_utils_tests.py
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
tar -cvzf test_vendor_package.tar.gz ./test_vendor_package
# .tar file
tar -cvf test_vendor_package.tar ./test_vendor_package
```
