# HP Cloud - Addins Library
This project is a shared library for addin services and products.

## common

### common.config
```python
checks_config(config_func)
settings(setting_key)
```

### common.keystone
```python
get_auth_token()

```

### common.logger
```python
getLogger(name)
```

### common.swift
```python
check_containier_missing(config=None)
check_file_exists(file_name, config=None)
ensure_containier_exists(config=None)
get_swift_config()
get_file_contents(file_name, config=None)
get_files_in_container(config=None)
save_object(name, contents, config=None)
```
