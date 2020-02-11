# Migration Schemas
> JSON Schema Definitions for ArcDesktop Migration Project

##  Contained Schemas
### Operations
- exported-domains.schema.json
- exported-layer.schema.json
- exported-table.schema.json
- transformed-domain.schema.json
- transformed-layer.schema.json
- transformed-table.schema.json

## Validating Schemas
Run following command:  
`npx ajv compile -s <operation_schema_file> [-r <dep_schema_file>]*`