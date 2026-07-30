# refract 

**Lightweight Virtual Environment Manager for Python**

Refract centralizes your Python virtual environments in a single location, providing simple commands to create, manage, and switch between project contexts—without the complexity of traditional virtual environment tools.

##  Features

- **Centralized Management**: All environments stored in `~/.refract/envs/`
- **Simple Commands**: Intuitive syntax that's easy to remember
- **Global Access**: Use `refract` from anywhere in your system
- **Zero Dependencies**: Only requires Python standard library
- **Seamless Switching**: Instant environment activation with new shell sessions
- **Colored Prompts**: Clear visual indication of active environment in shell prompt
- **Clean Organization**: Automatic directory structure management

##  Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [Commands Reference](#commands-reference)
- [Usage Examples](#usage-examples)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)

##  Installation

#### What refract install does
- Creates ~/.refract/refract.json with the default green/black colorway
- Installs prompt integration in both ~/.zshrc and ~/.bashrc
- Installs the shell wrapper in both files (auto-reloads after refract colorway)
- Sets up the symlink and PATH 

##### Re-running refract install is idempotent and will only update existing snippets to the latest version, not duplicate them!

### Prerequisites

- Python 3.7 or higher
- pip3 (usually comes with Python)

### Option 1: Quick Install (Recommended)

```bash
# Clone the repository
git clone git@github.com:YakShavingCatHerder/refract.git &&

# Run the installation script
cd refract && ./install.sh

# Reload your shell so PATH updates apply immediately
source ~/.zshrc
```

### Option 2: Manual Install

```bash
# Install using pip (macOS/Linux)
pip3 install -e . --user

# Make the script executable
chmod +x refract.py

# Set up global access
python3 -m refract install

# Reload your shell so PATH updates apply immediately
source ~/.zshrc
```

### Uninstall

```bash
# Run the uninstall script
cd User/path/to/refrect && ./uninstall.sh
```

##  Quick Start

After installation, you can immediately start using refract:

```bash
# Create your first environment
refract init myproject

# List all environments
refract list

# Activate an environment
refract use myproject

# Remove an environment when done
refract rm myproject
```

##  Commands Reference

`refract init <name>`

Creates a new virtual environment with the specified name.

**Parameters:**
- `environment_name`: Must be a valid Python identifier (letters, numbers, underscores only)

**Example:**
```bash
$ refract init django_project
Created new virtualenv at /path/to/.refract/envs/django_project
```

**What happens:**
- Creates a new virtual environment in `~/.refract/envs/<name>/`
- Uses Python's built-in `venv` module
- Validates the environment name format
- Prevents duplicate environment creation
---------------
`refract list`

Displays all available virtual environments.

**Example Output:**
```bash
$ refract list
Available virtualenvs:
  * django_project
  * flask_api
  * data_analysis
  * machine_learning
```

**What happens:**
- Scans `~/.refract/envs/` directory
- Lists all subdirectories as available environments
- Shows helpful message if no environments exist

---------------
`refract use <name>`

Activates the specified virtual environment by opening a new shell session.

**Example:**
```bash
$ refract use django_project
[refract] Switching to environment 'django_project'...
```

**What happens:**
1. Validates the environment exists
2. Creates a temporary activation script that:
  - Sources your shell profile files (`.bash_profile`, `.zshrc`, etc.)
  - Activates the virtual environment
  - Opens a new shell session with the environment active
  - Sets up colored prompt showing the active refract environment with `[refract:name]` prefix
3. Runs the script in a new shell process
4. Removes the temporary script as a cleanup process

**After activation, you'll see:**
```bash
[refract:django_project] user@machine ~ %
```
---------------
`refract rm <name>`

Removes the specified virtual environment.

**Example:**
```bash
$ refract rm old_project
Removed environment 'old_project'
```

**What happens:**
- Validates the environment exists
- Completely removes the environment directory
- Provides confirmation message
---------------
`refract current`

Shows the currently active refract environment.

**Example:**
```bash
$ refract current
Currently in refract environment: django_project
```

**What happens:**
- Checks for the `REFRACT_ENV` environment variable
- Displays the active environment name in light gray if one is active
- Shows "No refract environment currently active" if none is active
---------------
`refract install`

Sets up global access for refract (usually run automatically during installation).

**What happens:**
- Creates symlink in `~/.local/bin/`
- Adds `~/.local/bin` to your PATH if not already present
- Updates shell configuration files

## Usage Examples

### Example 1: Web Development Workflow

```
# Create environments for different projects
$ refract init frontend
Created new virtualenv at /Users/path/.refract/envs/frontend

$ refract init backend
Created new virtualenv at /Users/path/.refract/envs/backend

# List all environments
$ refract list
Available virtualenvs:
  * frontend
  * backend

# Switch to frontend work
$ refract use frontend
[refract] Switching to environment 'frontend'...

# In the new shell session:
[refract:frontend] $ npm install
[refract:frontend] $ npm start

# Switch to backend work (in another terminal)
$ refract use backend
[refract] Switching to environment 'backend'...

# In the new shell session:
[refract:backend] $ pip install django
[refract:backend] $ python manage.py runserver
```

### Example 2: Data Science Workflow
```
# Create specialized environments
$ refract init data_analysis
$ refract init ml_experiment
$ refract init visualization

# Switch between different analysis contexts
$ refract use data_analysis
[refract:data_analysis] $ pip install pandas numpy matplotlib

$ refract use ml_experiment
[refract:ml_experiment] $ pip install scikit-learn tensorflow

$ refract use visualization
[refract:visualization] $ pip install plotly seaborn bokeh
```

### Example 3: Project Cleanup
```bash
# List all environments
$ refract list
Available virtualenvs:
  * old_project
  * experiment_1
  * experiment_2
  * current_project

# Remove completed experiments
$ refract rm experiment_1
Removed environment 'experiment_1'

$ refract rm experiment_2
Removed environment 'experiment_2'

# Verify cleanup
$ refract list
Available virtualenvs:
  * old_project
  * current_project
```
---------------

### Directory Structure

Refract creates and manages the following structure:

```
~/.refract/
├── envs/                    # All virtual environments
│   ├── project_a/
│   │   ├── bin/
│   │   ├── lib/
│   │   └── ...
│   ├── project_b/
│   │   ├── bin/
│   │   ├── lib/
│   │   └── ...
│   └── ...
└── refract.json            # Configuration file
```

### Colored Prompts Feature

Refract automatically modifies your shell prompt to show the active environment:

- **Format**: `[refract:environment_name]` appears at the beginning of your prompt
- **Color**: Green background with black text by default to make current venv easily visible
- **Shell Support**: Works with both bash and zsh
- **Environment Variable**: Sets `REFRACT_ENV` for programmatic access

##  Troubleshooting

### Common Issues

#### "command not found: refract"

**Problem**: The `refract` command isn't available globally.

**Solution**:
```bash
# Re-run the install command
python3 -m refract install

# Or manually add to PATH
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

#### Refract environment is active, but prompt prefix is missing

**Problem**: `refract use <name>` activates the environment, but `[refract:<name>]` is not shown in your prompt.

**Why this happens**: Some shell themes/frameworks rebuild the prompt and can override custom prompt text.

**How to verify activation**:
```bash
echo $REFRACT_ENV
which python
```

If active, `REFRACT_ENV` should contain your environment name and `which python` should point to `~/.refract/envs/<name>/bin/python`.

#### "Permission denied: refract"

**Problem**: The refract.py file doesn't have execute permissions.

**Solution**:
```bash
chmod +x /path/to/refract.py
```

#### "Environment 'name' does not exist"

**Problem**: Trying to use an environment that hasn't been created.

**Solution**:
```bash
# Check available environments
refract list

# Create the environment first
refract init name
```

#### "Environment name must be a valid identifier"

**Problem**: Using invalid characters in environment names.

**Solution**: Use only letters, numbers, and underscores:
```bash
#  Valid names
refract init my_project
refract init project123
refract init _private

#  Invalid names
refract init my-project    # hyphens not allowed
refract init "my project"  # spaces not allowed
refract init my.project    # dots not allowed
```

### Debug Mode

Enable debug output to troubleshoot issues:

```bash
refract --debug list
```

This will show additional information about paths and configuration.

### Manual Environment Management

If you need to manually manage environments:

```bash
# List all environments
ls ~/.refract/envs/

# Remove an environment manually
rm -rf ~/.refract/envs/environment_name

# Check refract configuration
cat ~/.refract/refract.json
```

##  Contributing

### Development Setup

1. Clone the repository
2. Install in development mode:
   ```bash
   pip3 install -e . --user
   ```
3. Make your changes
4. Test your changes:
   ```bash
   python3 -m refract --debug list
   ```

### Code Style

- Follow PEP 8 guidelines
- Use descriptive variable names
- Add docstrings to functions
- Include error handling

##  License

This project is licensed under the MIT License - see the LICENSE file for details.

##  Acknowledgments

- Built with 1 dependency: Python's standard library
- Inspired by the need for simpler, cli-native management of virtual environments; perfect for deploying to lightweight servers when needed
- Thanks to the Python community for the excellent `venv` module; this isn't a diss, just a specific use-case ;)

---

**Happy coding with refract! **
