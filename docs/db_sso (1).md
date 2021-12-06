# SSO DB

About PREFIX:

- `mbcsso_dev`: for development environment
- `mbcsso_stg`: for stage environment
- `mbcsso_prod`: for production environment

## 1. Config Table Schema

- name: `{PREFIX}_Config`

| Name             | Type   | Content       | Default |
| ---------------- | ------ | ------------- | ------- |
| `system_id`      | String | Partition key |         |
| `tenant_id`      | String | Sort Key      |         |
| `client_id`      | String |               |         |
| `client_secret`  | String | KMS???        |         |
| `admin`          | String | Admin's name  |         |
| `password`       | String | KMS???        |         |
| `keycloak_url`   | String |               |         |
| `keycloak_realm` | String | KMS???        |         |

## 2. Write User Table Schema

## 2.1. Base Table

- name: `{PREFIX}_{SystemId}_{TenantId}_user_commands`
- TTL: set on sk `config#version` with `ttl` field

| Name         | Type          | Content                                                                                                                                                       | Default             |
| ------------ | ------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------- |
| `id`         | String        | Partition Key.<br>- `user#username`: user partition <br>- `group#name`: group partition                                                                       |                     |
| `sk`         | String        | Sort Key.<br>- `config`: user and group (latest version) info<br>- `config#version`: user and group (older version) info<br>- `member#uid`: group member info |                     |
| `command`    | String        | Command:<br> - `add`: Add action<br> - `update`: Update action<br> - `delete`: Delete action                                                                  |                     |
| `sso_type`   | String        | SSO type:<br>- `keycloak`                                                                                                                                     | `keycloak`          |
| `email`      | String        | Unique user' Email.<br>pk: `user#username`                                                                                                                    | `undefined`         |
| `password`   | String        | Encrypted user's password. <br>pk: `user#username`                                                                                                            | `undefined`         |
| `first_name` | String        | User's first name.<br>pk: `user#username`                                                                                                                     | `undefined`         |
| `last_name`  | String        | User's last name.<br>pk: `user#username`                                                                                                                      | `undefined`         |
| `is_active`  | Bool          | Active status.<br> `true`: active, `undefined`: deactive.<br>sk: `config`                                                                                     | `undefined`         |
| `version`    | Number        | Record version.<br>sk: `config#version`<br>sk: `config`                                                                                                       | `1`                 |
| `updated_at` | Timestamp     |                                                                                                                                                               | `CURRENT_TIMESTAMP` |
| `attributes` | Object        | Additional record's attributes.<br>sk: `config#version`<br>sk: `config`                                                                                       | `undefined`         |
| `ttl`        | Timestamp (s) | DynamoDB TTL.<br>sk: `config#version`                                                                                                                         | `undefined`         |

## 2.2. GSI User-Email Table

- name: `UserEmailGSI`

| Field        | Type          |
| ------------ | ------------- |
| `email`      | Partition Key |
| `sk`         | Sort Key      |
| `id`         |               |
| `first_name` |               |
| `last_name`  |               |
| `is_active`  |               |
| `version`    |               |
| `updated_at` |               |
| `attributes` |               |

- Uses Case
  - Fetch user by email

## 3. Read User Table Schema

## 3.1. Base Table

- name: `{PREFIX}_{SystemId}_{TenantId}_users`

| Name                | Type      | Content                                                                                 | Default             |
| ------------------- | --------- | --------------------------------------------------------------------------------------- | ------------------- |
| `id`                | String    | Partition Key.<br>- `user#username`: user partition <br>- `group#name`: group partition |                     |
| `sk`                | String    | Sort Key.<br>- `config`: user info and group info,<br>- `member#uid`: group member      |                     |
| `email`             | String    | Unique user' Email.<br>pk: `user#username`                                              | `undefined`         |
| `first_name`        | String    | User's first name.<br>pk: `user#username`                                               | `undefined`         |
| `last_name`         | String    | User's last name.<br>pk: `user#username`                                                | `undefined`         |
| `member_id`         | String    | User' id .<br>sk: `member#uid`                                                          | `undefined`         |
| `is_active`         | Bool      | Active status.<br>`true`: active, `undefined`: deactive.<br>sk: `config`                | `undefined`         |
| `version`           | Number    | Record version.<br>sk: `config`                                                         | `1`                 |
| `config_updated_at` | Timestamp | User or Group updated timestamp.<br>sk: `config`                                        | `CURRENT_TIMESTAMP` |
| `updated_at`        | Timestamp | Record's updated timestamp                                                              | `undefined`         |
| `attributes`        | Object    | Additional record's attributes.<br>sk: `config`                                         | `undefined`         |

## 3.2. GSI User-Group Table

- name: `UserGroupGSI`

| Field        | Type            |
| ------------ | --------------- |
| `member_id`  | Partition key   |
| `id`         | Sort Key        |
| `sk`         |                 |
| `updated_at` | added timestamp |

- Uses Case
  - Fetch groups by user' id

## 3.3. GSI User-Email Table

- name: `UserEmailGSI`

| Field               | Type          |
| ------------------- | ------------- |
| `email`             | Partition Key |
| `sk`                | Sort Key      |
| `id`                |               |
| `first_name`        |               |
| `last_name`         |               |
| `is_active`         |               |
| `version`           |               |
| `config_updated_at` |               |
| `attributes`        |               |

- Uses Case
  - Fetch user by email

## 3.4. GSI User-UpdatedAt Table

- name: `UserUpdatedAtGSI`

| Field               | Type          |
| ------------------- | ------------- |
| `id`                | Partition Key |
| `config_updated_at` | Sort key      |
| `sk`                |               |
| `email`             |               |
| `first_name`        |               |
| `last_name`         |               |
| `is_active`         |               |
| `version`           |               |
| `attributes`        |               |

- Uses Case
  - Fetch all users sorted by updated timestamp
  - Fetch all groups sorted by updated timestamp

## 3.5 GSI User-LastName Table

- name: `UserLastNameGSI`

| Field               | Type          |
| ------------------- | ------------- |
| `last_name`         | Partition Key |
| `config_updated_at` | Sort key      |
| `id`                |               |
| `sk`                |               |
| `email`             |               |
| `first_name`        |               |
| `is_active`         |               |
| `version`           |               |
| `attributes`        |               |

- Uses Case
  - Search users by last name

## 3.6 GSI User-FirstName Table

- name: `UserFirstNameGSI`

| Field               | Type          |
| ------------------- | ------------- |
| `first_name`        | Partition Key |
| `config_updated_at` | Sort key      |
| `id`                |               |
| `sk`                |               |
| `email`             |               |
| `last_name`         |               |
| `is_active`         |               |
| `version`           |               |
| `attributes`        |               |

- Uses Case
  - Search users by first name
