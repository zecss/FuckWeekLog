from collections import defaultdict
import json
import requests
import git
from datetime import datetime, timedelta

# 读取配置文件
def read_config(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    return config


# 获取 Git 提交日志
def get_git_log(repo_path):
    repo = git.Repo(repo_path)
    author_name = repo.config_reader().get_value("user", "name")
    print("当前用户的Git配置用户名：", author_name)
    # 获取当前日期和一周前的日期
    end_date = datetime.now()
    start_date = end_date - timedelta(days=7)
    # 遍历提交记录
    commits = repo.iter_commits('master', since=start_date, until=end_date)
    # 用字典按日期分组
    logs_by_date = defaultdict(list)
    for commit in commits:
        if commit.author.name == author_name:
            commit_date = commit.committed_datetime.date()
            commit_message = commit.message.strip()
            logs_by_date[commit_date].append(commit_message)
    # 构建最终的日志信息
    log = ""
    for commit_date in sorted(logs_by_date.keys()):
        log += f"提交日期: {commit_date}\n"
        log += f"提交信息: {', '.join(logs_by_date[commit_date])}\n"
        log += "-" * 40 + "\n"
    return log


def generate_report(git_log, openai_api_key, openai_base_url, model):
    url = openai_base_url
    OPENAI_API_KEY = openai_api_key
    header = {"Content-Type": "application/json", "Authorization": "Bearer " + OPENAI_API_KEY}
    data = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": "你是一位擅长技术管理沟通的专家。根据git提交的代码变化，帮我写一份面向领导的工作日报。重点是列出每天做了什么功能，说明这些功能是怎么推动业务的，不要涉及太多技术细节。日报应该按日期写清楚每一天做了哪些事。不要使用太过正式的语气，尽量简洁明了，突出工作的成果，展现主动性和规划性。不要出现markdown格式,中文回复，每一天的工作内容要按日期列出，不要最终的总结！，每天的格式是：日期 - 完成的功能描述。"
            },
            {
                "role": "user",
                "content": git_log
            }
        ],
        "temperature": 0,
        "stream": False
    }
    response = requests.post(url=url, headers=header, json=data).json()
    result = response.get('choices', [{}])[0].get('message', {}).get('content', '')
    return result


# 主程序
def main():
    config_path = 'config.json'
    config = read_config(config_path)
    openai_api_key = config.get('openai_api_key')
    openai_base_url = config.get('openai_base_url')
    openai_model = config.get('openai_model')
    repo_path = config.get('repo_path')
    git_log = get_git_log(repo_path)
    if not git_log:
        print("没有获取到Git提交日志，是不是又摸鱼了(●'◡'●)")
        return
    else:
        print("获取到Git提交日志：", git_log)
    print("开始生成周报_...")
    report = generate_report(git_log, openai_api_key, openai_base_url, openai_model)
    # 获取当前日期
    current_date = datetime.now().strftime("%Y-%m-%d")
    filename = f"周报_{current_date}.txt"
    # 将生成的日报写入txt文件
    with open(filename, 'w', encoding='utf-8') as file:
        file.write(report)
    print(f"生成成功，已保存到 '{filename}' 文件中")


if __name__ == "__main__":
    main()