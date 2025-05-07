# Workflow Timer Application

This application is a PyQt6-based workflow timer designed to help manage, monitor and execute workflows, such as recipes. It provides a graphical user interface (GUI) for managing tasks, timers, and checklists, with features like countdown timers, pre-flight and post-flight checklists, and dynamic stream triggering. Helping to complete complex workflows that require coordination and tracking across multiple streams.

## Features
- **Countdown Timer**: Manage tasks with countdown timers that visually indicate progress using color-coded backgrounds (green, amber, red).
- **Pre-Flight and Post-Flight Checklists**: Display checklists before and after workflows for review.
- **Parallel Workstream Management**: Execute and monitor multiple workflows simultaneously and automatically trigger new streams based on task completion.
- **Customizable Timer Controls**: Pause, resume, extend, or reduce timers dynamically.
- **Task Overrun Alerts**: Notify users when tasks exceed their allocated time.
- **Speaker Integration**: Text-to-speech alerts for task start messages and overrun notifications.

The application is composed of **two key parts**:
1. **The Application**: A feature-rich tool that provides the interface and functionality to execute workflows, including timers, alerts, and dynamic stream management.
2. **The Recipes**: Custom-designed workflow definitions (in JSONC format) that describe the tasks, dependencies, and logic for your specific use case. Recipes are highly flexible and can be tailored to your needs, whether you require simple task lists or complex workflows.
    For a detailed explanation of the recipe model and how to create your own recipes, see the [Recipe Guide](documentation/recipe_guide.md).
## Installation

Recommended to create a virtual environment [venv_setup.txt]

### Prerequisites

Ensure you have Python 3.11 or later installed. Install the required dependencies using `pip`:

```bash
pip install -r [requirements.pip](documentation/reminders_pip.txt)
```


