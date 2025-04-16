from flask import Flask, render_template, request, jsonify, redirect, url_for
import os
import json
from random import uniform
import math

app = Flask(__name__, static_folder='static')
DATA_FILE = "tasks.json"
FINISHED_FILE = "finished_tasks.json"
TASK_TYPES = ["学习", "科研", "生活", "其他"]
COLORS = {"学习": "#4285F4", "科研": "#EA4335", "生活": "#FBBC05", "其他": "#34A853"}  # Google配色

# 初始化数据文件
def init_files():
    for file in [DATA_FILE, FINISHED_FILE]:
        if not os.path.exists(file):
            with open(file, "w") as f:
                json.dump([], f)

def load_tasks(filename=DATA_FILE):
    with open(filename, "r") as f:
        return json.load(f)

def save_tasks(tasks, filename=DATA_FILE):
    with open(filename, "w") as f:
        json.dump(tasks, f, indent=2)

# 为重叠任务生成分散坐标
def scatter_points(tasks):
    positions = {}
    for task in tasks:
        key = (task["urgency"], task["priority"])
        if key not in positions:
            positions[key] = []
        positions[key].append(task)
        # print(f'append task: {task["text"]} - key: {key}')  # 调试输出任务信息
    
    for key, group in positions.items():
        # print(f"处理任务组: {key} - 任务数量: {len(group)}")  # 调试输出任务组信息
        if len(group) > 1:
            for i, task in enumerate(group):
                # print(f"处理任务: {task['text']} - 原坐标: ({key[0]}, {key[1]})")  # 调试输出任务信息
                angle = 2 * 3.14159 * i / len(group)
                radius = 0.2 * min(1, 10/len(group))
                task["x"] = key[0] + radius * uniform(0.8, 1.2) * (0.5 if i%2 else -0.5)
                task["y"] = key[1] + radius * uniform(0.8, 1.2) * (0.5 if i%3 else -0.5)
                workload = max(0, min(10, task.get('workload', 5)))
                task['radius'] = 2 + math.sqrt(workload) * 6
        else:
            task = group[0]
            task["x"], task["y"] = key[0], key[1]
            workload = max(0, min(10, task.get('workload', 5)))
            task['radius'] = 2 + math.sqrt(workload) * 6
        # print(f"任务坐标: {task['text']} - x: {task['x']}, y: {task['y']}")  # 调试输出坐标
    return tasks

@app.route("/")
def index():
    tasks = load_tasks()
    # print("调试任务数据:", tasks)  # 查看x/y是否存在
    finished = load_tasks(FINISHED_FILE)
    return render_template(
        "index.html",
        tasks=scatter_points(tasks),
        task_types=TASK_TYPES,
        colors=COLORS,
        finished_count=len(finished)
    )
@app.route("/add", methods=["POST"])
def add_task():
    task = {
        "text": request.form.get("task"),
        "note": request.form.get("note", "")[:200],
        "type": request.form.get("type") or "其他",
        "priority": int(request.form.get("priority") or 5),
        "urgency": int(request.form.get("urgency") or 5),
        "workload": int(request.form.get("workload") or 5),
        "due_date": request.form.get("due_date") or None,
        "due_time": request.form.get("due_time") or "23:59",
        "completed": False
    }
    tasks = load_tasks()
    tasks.append(task)
    save_tasks(tasks)
    return jsonify({"status": "success"})

@app.route("/complete/<int:index>", methods=["POST"])
def complete_task(index):
    tasks = load_tasks()
    if 0 <= index < len(tasks):
        finished_task = tasks.pop(index)
        finished_task["completed"] = True
        finished = load_tasks(FINISHED_FILE)
        finished.append(finished_task)
        save_tasks(tasks)
        save_tasks(finished, FINISHED_FILE)
    return jsonify({"status": "success"})

@app.route("/delete/<int:index>", methods=["POST"])
def delete_task(index):
    tasks = load_tasks()
    if 0 <= index < len(tasks):
        tasks.pop(index)
        save_tasks(tasks)
    return jsonify({"status": "success"})
@app.route('/edit/<int:index>', methods=['GET', 'POST'])
def edit_task(index):
    tasks = load_tasks()
    if request.method == 'POST':
        # 更新任务数据
        tasks[index]['text'] = request.form['task']
        tasks[index]['type'] = request.form['type']
        tasks[index]['priority'] = int(request.form['priority'])
        tasks[index]['urgency'] = int(request.form['urgency'])
        tasks[index]['workload'] = int(request.form['workload'])
        tasks[index]['due_date'] = request.form['due_date']
        tasks[index]['due_time'] = request.form['due_time']
        return redirect(url_for('index'))  # 返回主页面

    # 渲染编辑页面
    task = tasks[index]
    return render_template('edit_task.html', task=task, index=index)

if __name__ == "__main__":
    init_files()
    app.run(host="0.0.0.0", port=5000, debug=True)