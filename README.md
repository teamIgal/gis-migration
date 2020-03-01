# Migration Schemas
> JSON Schema Definitions for ArcDesktop Migration Project

## Installing
* Make sure you're using Python 3.7 or newer.  
* Ensure you have [pipenv](https://pipenv.kennethreitz.org/en/latest/) installed.
* Run the following command to install project dependencies:
```shell
$ pipenv install
```

## Using Schemas
### Compile Schema
__Run the following command:__
```shell
$ jsonschema <path_to_schema_file>
```
If schema is compiled successfuly, expect no output.
Otherwise, an error will be printed to console.

__Example:__
```shell
$ jsonschema ./schemas/domain.schema.json
```


### Validate JSON Against Schema
__Run the following command:__
```shell
$ jsonschema -i <path_to_json_file> <path_to_schema_file>
```
__Example:__
```shell
$ jsonschema -i my-domain.json ./schemas/domain.schema.json
```
If JSON adheres to schema, expect no output.
Otherwise, an error will be printed to console.