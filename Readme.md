# Annotation project api
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
## Development setup
You can choose between [Pycharm](https://www.jetbrains.com/de-de/pycharm/) (Professional Edition) and [VsCode](https://code.visualstudio.com/) as a development environment. 

In the following steps, only the variant in the selected development environment needs to be executed.

### Create local environment file
```shell
cp .env.EXAMPLE .env
```

### Run Project

Clone the [setup](https://github.com/Databases-and-Informationsystems/setup) project and follow the instructions

### Git hooks
#### Update git hooks settings
```bash
git config core.hooksPath ./.githooks
```
```bash
chmod 744 ./.githooks/pre-commit
chmod 744 ./.githooks/commit-msg
```
#### Run pre-commit docker-compose
```bash
docker compose -f ./.githooks/docker/pre-commit/docker-compose.yml up -d
```

### Select Interpreter
#### in PyCharm ...
- `Settings -> "Seach" Python interpreter -> add interpreter (Button on the right of current interpreter) -> On Docker...`
   - `Pull or use existing image`
   - Select Docker image (Probably contains flask in its name)
      - You can find it using Docker Desktop
#### in VS Code ...
Source: [dev.to](https://dev.to/alvarocavalcanti/setting-up-a-python-remote-interpreter-using-docker-1i24)
- Install the Python extension
- Install the Dev - Containers extension
- Open the Command Palette and type `Dev-Containers`, then select the `Attach to Running Container...` and select the running docker container (flask)
- VS Code will restart and reload
- On the Explorer sidebar, click the open a folder button and then enter `/app` (this will be loaded from the remote container)
- On the Extensions sidebar, select the Python extension and install it on the container
- (When prompted on which interpreter to use, select `/usr/local/bin/python`)
- (Open the Command Palette and type Python: Configure Tests, then select the unittest framework)
### Code Formatting
- We use [Black](https://black.readthedocs.io/en/stable/index.html) to format the python code 
#### Set up in PyCharm
- install black
   - `pip install black` 
   - OR
   - `Settings -> Tools -> Black --> install black...`
- run black on save
   - `Settings -> Tools -> Actions on save --> "check" run black`
#### Set up in VS Code
- Install [Black Formatter](https://marketplace.visualstudio.com/items?itemName=ms-python.black-formatter) (inside the dev-container environment)
- `Settings -> Seach "Default Formatter"`
- `Settings -> Text Editor -> Format on Save`

### Connect to Database
#### in PyCharm ...
- Click Database Icon (top right)
- `+ -> Data Source -> PostgreSQL`
   - Host: `0.0.0.0`
   - Port: `5432`
   - User: `user`
   - Password: `s3cr3t`
   - Database: `annotation_db`
- `OK`
#### in VS Code...
TODO

### Updating Data Model
- Inside docker-image ``annotation_backend``, open terminal
- run ``flask db init`` (must only run once)
- After every change in data model:
- run ``flask db migrate``
- run ``flask db upgrade``
- If an error occurs during these steps, try: 
  - run ``flask db stamp head`` 
  - run migrate + upgrade again