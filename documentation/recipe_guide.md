# Recipe Guide

## Overview

Recipes define the structure and logic of workflows in the Workflow Manager Application. They are written in JSON/JSONC format and allow for:
- Parallel task execution.
- Dynamic task management.
- Customizable properties for tasks and streams.

Recipes are highly flexible and can be tailored to suit a variety of workflows, from simple task lists to complex, multitasking processes.


``` more w user in mind 
Recipes define workflows in the Workflow Manager Application. They allow you to break down complex tasks into smaller steps, organize them into groups, and run them in parallel. Recipes are written in JSON/JSONC format and are highly customizable to suit your needs.

If was written completely for users, think would reference e.g. you 
```
---
## What makes up a Recipe 

1st 
### Pre-Flight and Post-Flight Checklists
- **Pre-Flight**: A checklist of steps to prepare for the workflow. This ensures all necessary equipment and ingredients are ready before starting.
- **Post-Flight**: A checklist of steps to clean up and ensure safety after the workflow is completed.

## then the bulk of the recipe 
- Streams: a sequence of related tasks that can run in parallel with other streams, allowing multitasking.
- **Example**: In the eggs & soldiers recipe, there are two streams:
  - `"Eggs"`: Handles boiling eggs.
  - `"Soldiers"`: Handles preparing toast.
- Tasks: tasks are steps within a stream, each with properties defining its behavior, duration, and importance.
- **Types**:
  - **Active**: Require user interaction (e.g., `"Put the eggs on to boil"`).
  - **Background**: Run without constant attention and can auto-progress to the next step (e.g., `"Boiling eggs..."`).
  - **High-Stakes**: Critical tasks with alerts if not completed on time (e.g., `"Remove Eggs"`).

### Task Properties
Each task can have the following properties:
- **`Type`**: `Active` or `Background`.
- **`Steps`**: Instructions for completing the task.
- **`DurationSeconds`**: Time allocated for the task.
- **`Stakes`**: Importance level (`Low`, `Mid`, `High`).
- **`Autoprogress`**: Auto-completes after the duration if `true` (for background tasks -> )
- **`CheckEverySeconds`**: Interval for high-stakes task checks.
- **`CheckMessage`**: Alert message for high-stakes tasks.
- **`StartMessage`**: Message displayed at task start.
- **`Trigger`**: Starts another stream or task upon completion.

- **Optional Features**: Not all tasks need to include every property. For example, RAG (Red-Amber-Green) status indicators are optional. #TODO check how validation handles 

### Parallel Task Management
- **Dynamic Stream Triggering**: Tasks can trigger other streams dynamically. For example, the `"StartEggs"` task in the `"Eggs"` stream triggers the `"Soldiers"` stream.
- **Multitasking**: Streams allow for parallel execution of tasks, such as boiling eggs while preparing toast.

---

## Example Recipe Walkthrough
Here’s how the `"Eggs"` stream works in the example recipe:

1. **`Put_kettle_on`**: An active task where the user boils water in the kettle.
2. **`KettleBoiling`**: A background task that auto-progresses after 2 minutes.
3. **`StartEggs`**: An active task where the user starts boiling the eggs. This task triggers the `"Soldiers"` stream.
4. **`BoilingEggs`**: A background task where the eggs boil for 3 minutes.
5. **`RemoveEggs`**: A high-stakes active task where the user removes the eggs from the water. Alerts are triggered if the task is not completed within the allocated time.

---

## Best Practices for Recipe Design

1. **Break Down Tasks**: Divide workflows into small, manageable tasks with clear instructions.
2. **Use Streams for Parallelism**: Group related tasks into streams to enable multitasking.
3. **Set Realistic Durations**: Assign appropriate durations to tasks based on their complexity.
4. **Leverage Alerts**: Use `CheckEverySeconds` and `CheckMessage` for high-stakes tasks to ensure critical steps are not overlooked.
5. **Test Your Recipes**: Run through the recipe to ensure the timing and instructions are practical.

---
For more examples and advanced usage, refer to the sample recipes in the `recipes/` directory.


#TODO make tutorial ver recipe 
   "GoStream" : "Eggs", #one stream has to be "starting" stream