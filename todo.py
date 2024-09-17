import os
import re
import argparse
from datetime import datetime
from colorama import Fore, Style, init
from tabulate import tabulate


script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)
init(autoreset=True)

tasks = []
completed_tasks = []

def validate_date(date_str):
    if not re.match(r'^\d{1,2}/\d{1,2}$', date_str):
        raise argparse.ArgumentTypeError("Date must be in format M/D, M/DD, MM/D, or MM/DD")
    return date_str

def ensure_permissions(filename):
    try:
        os.chmod(filename, 0o600)  # Read and write permissions for the owner
    except FileNotFoundError:
        pass

def load_tasks(todo_filename="file", done_filename="file"):
    tasks.clear()
    completed_tasks.clear()
    
    ensure_permissions(todo_filename)
    ensure_permissions(done_filename)
    
    try:
        with open(todo_filename, "r") as file:
            for line_number, line in enumerate(file, start=1):
                match = re.match(r'- (.*?) \{(.*?)\}\[(.*?)\]', line.strip())
                if match:
                    task, date, task_class = match.groups()
                    tasks.append({"line_number": line_number, "task": task, "date": date, "task_class": task_class})
    except FileNotFoundError:
        pass

    try:
        with open(done_filename, "r") as file:
            for line in file:
                match = re.match(r'- (.*?) \{(.*?)\}\[(.*?)\]', line.strip())
                if match:
                    task, date, task_class = match.groups()
                    completed_tasks.append({"task": task, "date": date, "task_class": task_class})
    except FileNotFoundError:
        pass

def save_tasks(filename="todo.txt"):
    ensure_permissions(filename)
    with open(filename, "w") as file:
        for task in tasks:
            date = task["date"] if task["date"] else ""
            task_class = task["task_class"] if task["task_class"] else ""
            file.write(f'- {task["task"]} {{{date}}}[{task_class}]\n')
    ensure_permissions(filename)

def save_completed_tasks(filename="done.txt"):
    ensure_permissions(filename)
    with open(filename, "w") as file:
        for task in completed_tasks:
            date = task["date"] if task["date"] else ""
            task_class = task["task_class"] if task["task_class"] else ""
            file.write(f'- {task["task"]} {{{date}}}[{task_class}]\n')
    ensure_permissions(filename)

def move_task_to_done(task):
    global tasks
    tasks = [t for t in tasks if t != task]
    
    todo_filename = ""
    done_filename = ""
    
    save_tasks(todo_filename)
    save_completed_tasks(done_filename)

    completed_tasks.append(task)

def undo_last_done():
    if completed_tasks:
        last_task = completed_tasks.pop()
        tasks.append(last_task)
        save_tasks()
        save_completed_tasks()
        print(f"Undoing task: {last_task['task']}")
    else:
        print("No completed tasks to undo.")

def parse_date(date_str):
    return datetime.strptime(date_str, "%m/%d")

def main():
    load_tasks()

    parser = argparse.ArgumentParser(description="Todo list manager")
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    parser_add = subparsers.add_parser("add", help="Add a task to the todo list")
    parser_add.add_argument("task", help="The task to add")
    parser_add.add_argument("-d", "--date", type=validate_date, help="The due date for the task (M/DD or MM/DD)")
    parser_add.add_argument("-c", "--class", dest="task_class", help="The class of the task")

    parser_done = subparsers.add_parser("done", help="Complete one or more tasks on the todo list")
    parser_done.add_argument("identifiers", nargs='+', help="The task descriptions or numbers to mark as done")
    parser_done.add_argument("-d", "--date", type=validate_date, help="The due date for the task (M/DD or MM/DD)")
    parser_done.add_argument("-c", "--class", dest="task_class", help="The class of the task")

    parser_undo = subparsers.add_parser("undo", help="Undo the last completed task")

    parser_ls = subparsers.add_parser("ls", help="List all tasks that are still todo")
    parser_ls.add_argument("-n", "--now", action="store_true", help="List tasks due today")
    parser_ls.add_argument("-d", "--date", type=validate_date, help="List tasks due on a specific date (M/DD or MM/DD)")
    parser_ls.add_argument("-c", "--class", dest="task_class", help="List tasks for a specific class")

    parser_update = subparsers.add_parser("update", help="Update the list of tasks from the files")

    args = parser.parse_args()

    if args.command == "add":
        task_info = {"task": args.task, "date": args.date, "task_class": args.task_class}
        tasks.append(task_info)
        save_tasks()
        print(f"Adding task: {args.task}")
        if args.date:
            print(f"Due date: {args.date}")
        if args.task_class:
            print(f"Class: {args.task_class}")
    elif args.command == "done":
        for identifier in args.identifiers:
            if identifier.isdigit():
                task_number = int(identifier)
                task = next((t for t in tasks if t["line_number"] == task_number), None)
                if task:
                    move_task_to_done(task)
                    print(f"Completing task: {task['task']}")
                else:
                    print(f"Task number {task_number} is out of range.")
            else:
                for task in tasks:
                    if task["task"] == identifier and task["date"] == args.date and task["task_class"] == args.task_class:
                        tasks.remove(task)
                        move_task_to_done(task)
                        print(f"Completing task: {identifier}")
                        break
                else:
                    print(f"Task not found: {identifier}")
    elif args.command == "undo":
        undo_last_done()
    elif args.command == "ls":
        if args.now:
            today = datetime.now().strftime("%-m/%d")
            filtered_tasks = [task for task in tasks if task["date"] == today]
        elif args.date:
            filtered_tasks = [task for task in tasks if task["date"] == args.date]
        elif args.task_class:
            filtered_tasks = [task for task in tasks if task["task_class"] == args.task_class]
        else:
            filtered_tasks = tasks

        if not filtered_tasks:
            print("No tasks to show.")
        else:
            table = []
            for task in filtered_tasks:
                task_str = task['task']
                date_str = f"{Fore.RED}{task['date']}{Style.RESET_ALL}" if task["date"] else ""
                class_str = f"{Fore.BLUE}{task['task_class']}{Style.RESET_ALL}" if task["task_class"] else ""
                table.append([task["line_number"], task_str, date_str, class_str])
            print(tabulate(table, headers=["#", "Task", "Due Date", "Class"], tablefmt="plain"))
    elif args.command == "update":
        load_tasks()
        tasks.sort(key=lambda x: parse_date(x["date"]) if x["date"] else datetime.max)
        save_tasks()
        print("Task lists updated and sorted from files.")

if __name__ == "__main__":
    main()