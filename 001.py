from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time
from datetime import datetime, timedelta
import schedule

# 设置 Chrome 选项
options = webdriver.ChromeOptions()
options.add_argument('--ignore-certificate-errors')
options.add_argument('--ignore-ssl-errors')

# 添加一个头信息以避免被检测为自动化工具
options.add_argument(
    '--user-agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.45 Safari/537.36"')

driver = None


def login(username, password):
    global driver
    try:
        # 初始化 WebDriver
        driver = webdriver.Chrome(options=options)

        # 打开网页
        url = "https://org.xjtu.edu.cn/openplatform/oauth/authorize?scope=user_info&responseType=code&appId=1464&redirectUri=https://xkfw.xjtu.edu.cn/xsxkapp/sys/xsxkapp/login/dologin.do&state=11060afc5f7c49b9bd2227731a4c281b"
        driver.get(url)

        # 显式等待，直到找到用户名框输入
        username_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'input.username'))
        )
        username_input.send_keys(username)

        # 显式等待，直到找到密码输入框
        password_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'input.pwd'))
        )
        password_input.send_keys(password)

        # 显式等待，直到找到登录按钮并点击
        login_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, 'div.login_btn.account_login#account_login'))
        )
        login_button.click()

        # 等待页面跳转到选课页面
        WebDriverWait(driver, 10).until(
            EC.url_contains('https://xkfw.xjtu.edu.cn/xsxkapp/sys/xsxkapp/')
        )

    except TimeoutException:
        print("Timed out waiting for login page to load or elements to be present")
    except Exception as e:
        print(f"An error occurred during login: {e}")


def select_courses(target_courses):
    global driver
    if driver is None:
        print("Driver is not initialized. Please login first.")
        return

    try:
        # 显式等待，直到找到所有的 input.cv-electiveBatch-select 元素
        elective_batch_radio_list = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'input.cv-electiveBatch-select'))
        )

        if len(elective_batch_radio_list) >= 3:
            # 点击第三个按钮（索引从0开始）
            elective_batch_radio_list[2].click()
            print("第三个选课批次按钮已选择。")
        else:
            print("页面上没有足够的选课批次按钮。")

        # 显式等待，直到找到“确定”按钮并点击
        confirm_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, 'button.bh-btn.bh-btn-primary.bh-pull-right'))
        )
        confirm_button.click()

        # 显式等待，直到找到“开始选课”按钮并点击
        start_course_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, 'button.cv-btn.cv-mb-8#courseBtn'))
        )
        start_course_button.click()
        print("“开始选课”按钮已点击。")

        # 遍历目标课程列表
        for target_course_name in target_courses:
            # 在表格中进行课程名称模糊匹配
            # 显式等待，直到找到所有课程元素
            course_elements = WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div.cv-course'))
            )

            found_courses = []
            for course_element in course_elements:
                if target_course_name in course_element.text:
                    found_courses.append(course_element.text)
                    print(f"找到匹配的课程：{course_element.text}")

            if not found_courses:
                print(f"没有找到包含 '{target_course_name}' 的课程。")
                continue  # 跳过当前课程，继续处理下一门课程

            print("所有匹配的课程：")
            for course in found_courses:
                print(course)

            # 获取匹配课程的课程序号信息
            if found_courses:
                # 假设第一个匹配的课程是目标课程
                target_course = found_courses[0]

                # 找到目标课程的父级元素
                parent_element = None
                course_elements_full = WebDriverWait(driver, 10).until(
                    EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div.cv-row'))
                )
                for element in course_elements_full:
                    if target_course in element.text:
                        parent_element = element
                        break

                if parent_element:
                    # 获取课程信息
                    course_info = {
                        "课程号": parent_element.find_element(By.CSS_SELECTOR, 'div.cv-num').text,
                        "课程名称": parent_element.find_element(By.CSS_SELECTOR, 'div.cv-course').text,
                        "课程类别": parent_element.find_element(By.CSS_SELECTOR, 'div.cv-type').text,
                        "课程性质": parent_element.find_element(By.CSS_SELECTOR, 'div.cv-nature').text,
                        "开课单位": parent_element.find_element(By.CSS_SELECTOR, 'div.cv-department-col').text,
                        "学分": parent_element.find_element(By.CSS_SELECTOR, 'div.cv-credit-col').text
                    }
                    print(f"目标课程信息：{course_info}")

                    # 获取课程序号
                    course_number = course_info["课程号"][:10]

                    # 点击课程区域（不是“课程详情”链接）
                    course_row = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, f'div.cv-row[coursenumber="{course_number}"]'))
                    )
                    course_row.click()  # 点击整个课程行

                    # 等待课程卡片加载
                    time.sleep(0.5)

                    try:
                        # 等待并点击包含“课容量”的区域
                        capacity_div = WebDriverWait(driver, 20).until(
                            EC.element_to_be_clickable(
                                (By.XPATH, '//div[contains(text(), "课容量") and @class="cv-caption-text"]')
                            )
                        )
                        capacity_div.click()
                        print("已点击包含“课容量”的区域")

                        # 等待“选择”按钮出现并点击
                        choose_button = WebDriverWait(driver, 20).until(
                            EC.element_to_be_clickable((By.CSS_SELECTOR, 'button.cv-btn-chose'))
                        )
                        choose_button.click()
                        print(f"已点击“选择”按钮，完成选课：{target_course_name}")

                        # 检查是否出现添加失败的提示
                        try:
                            # 显式等待，检查是否出现“添加失败”提示
                            error_message = WebDriverWait(driver, 5).until(
                                EC.presence_of_element_located((By.CSS_SELECTOR, 'h2.cv-mb-8'))
                            )
                            if "添加失败" in error_message.text:
                                print(f"选课失败：{target_course_name} - {error_message.text}")
                                # 点击“确认”按钮
                                confirm_error_button = WebDriverWait(driver, 10).until(
                                    EC.element_to_be_clickable((By.CSS_SELECTOR, 'div.cv-sure.cvBtnFlag'))
                                )
                                confirm_error_button.click()
                                print(f"已点击“确认”按钮，继续尝试下一门课程。")
                        except TimeoutException:
                            # 如果没有出现错误提示，继续执行
                            print(f"选课成功：{target_course_name}")
                        except Exception as e:
                            print(f"处理错误提示时发生异常：{e}")

                    except TimeoutException:
                        print(f"等待“课容量”区域或“选择”按钮超时：{target_course_name}")
                    except Exception as e:
                        print(f"点击“课容量”区域或“选择”按钮时发生异常：{e}")

    except TimeoutException:
        print("Timed out waiting for elements during course selection")
    except Exception as e:
        print(f"An error occurred during course selection: {e}")


def start_course_selection(username, password, target_courses):
    global driver
    driver = None  # 确保driver被正确初始化

    # 登录操作
    print("开始登录...")
    login(username, password)

    if driver is None:
        print("登录失败，程序退出。")
        return

    # 选课操作
    print("登录成功，开始选课...")
    select_courses(target_courses)


def job(username, password, target_courses):
    # 获取当前时间并格式化
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"执行任务：{now}")
    start_course_selection(username, password, target_courses)


if __name__ == '__main__':
    username = "username"  # 统一身份认证
    password = "pwd"  # 统一身份认证
    target_courses = ["算法", "测控"]

    # 使用 input 函数获取开始时间
    start_time_str = input("请输入定时开始时间（格式：YYYY-MM-DD HH:MM:SS）：")
    start_time = datetime.strptime(start_time_str, "%Y-%m-%d %H:%M:%S")

    # 计算当前时间和目标时间之间的时间差
    now = datetime.now()
    time_diff = (start_time - now).total_seconds()

    if time_diff > 0:
        print(f"将在 {time_diff} 秒后开始执行任务。")
        # 使用 schedule 库实现定时功能
        schedule.every(time_diff).seconds.do(job, username=username, password=password, target_courses=target_courses)

        # 进入循环，等待任务执行
        while True:
            schedule.run_pending()
            if driver is not None:
                print("任务已执行，退出循环。")
                break
            time.sleep(1)
    else:
        print("开始时间已过，立即执行任务。")
        start_course_selection(username, password, target_courses)

    if driver:
        # 保持浏览器打开一段时间查看结果，然后关闭
        time.sleep(150)  # 保持打开 150 秒
        driver.quit()