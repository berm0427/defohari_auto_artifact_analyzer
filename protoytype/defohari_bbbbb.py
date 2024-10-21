import os
import sys
import subprocess
import threading
import queue
import json
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
import time

# 리소스 파일 경로 찾기 함수
def resource_path(relative_path):
    """ PyInstaller와 같은 빌드 환경에서 리소스 파일 경로를 가져옴 """
    try:
        base_path = sys._MEIPASS  
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def run_hive(image_path):
    """Step 0: web_hive_parsing_Log_num.py 실행, 파싱한 하이브 파일을 저장"""
    subprocess.run(['python', r'subroutine\web\web_hive_parsing_Log_num.py', image_path], check=True)

# PrintLogger 클래스 정의
class PrintLogger:
    def __init__(self, text_widget, message_queue):
        self.text_widget = text_widget
        self.message_queue = message_queue
        self.update_text()

    def write(self, message):
        # 메시지를 메시지 큐에 추가
        self.message_queue.put(('log', message))

    def flush(self):
        pass

    def update_text(self):
        while not self.message_queue.empty():
            message = self.message_queue.get()
            if isinstance(message, tuple) and message[0] == 'log':
                msg_content = message[1]
                self.text_widget.config(state=tk.NORMAL)
                self.text_widget.insert(tk.END, msg_content)
                self.text_widget.see(tk.END)
                self.text_widget.config(state=tk.DISABLED)
        self.text_widget.after(100, self.update_text)

# 서브프로세스 실행 함수
def run_subroutine(task_name, task_name_for_info, command, args, log_file_path, progress_queue, message_queue, index, stop_event, file_lock):
    creationflags = 0
    if sys.platform == 'win32':
        creationflags = subprocess.CREATE_NO_WINDOW

    if stop_event.is_set():
        progress_queue.put((index, 0))  # 진행률 업데이트를 위해 0초로 처리
        return 0

    start_time = time.time()

    # 메시지를 저장할 큐 생성
    task_message_queue = []

    # 작업 시작 메시지 추가
    task_message_queue.append(f"{task_name} 시작\n")
    task_message_queue.append(f"'{task_name}'의 로그가 '{log_file_path}' 파일에 기록됩니다.\n")

    # 현재 작업 라벨 업데이트 요청
    message_queue.put(('current_task', f"{task_name_for_info}"))

    try:
        command_with_args = command + args
        process = subprocess.Popen(
            command_with_args,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            universal_newlines=True,
            creationflags=creationflags
        )
        with file_lock:
            with open(log_file_path, 'a', encoding='utf-8') as f:
                f.write(f"===== {task_name} 시작 =====\n")
        while True:
            if stop_event.is_set():
                process.terminate()
                task_message_queue.append(f"{task_name} 중지됨\n")
                progress_queue.put((index, time.time() - start_time, task_message_queue))
                return time.time() - start_time
            line = process.stdout.readline()
            if not line:
                break
            with file_lock:
                with open(log_file_path, 'a', encoding='utf-8') as f:
                    f.write(line)
        process.stdout.close()
        process.wait()
        if process.returncode != 0:
            error_message = process.stderr.read()
            with file_lock:
                with open(log_file_path, 'a', encoding='utf-8') as f:
                    f.write(f"Error: {error_message}\n")
            task_message_queue.append(f"{task_name}에서 오류 발생: {error_message}\n")
        else:
            task_message_queue.append(f"{task_name} 완료\n\n")
            with file_lock:
                with open(log_file_path, 'a', encoding='utf-8') as f:
                    f.write(f"===== {task_name} 종료 =====\n\n")
    except Exception as e:
        task_message_queue.append(f"{task_name} 실행 중 오류 발생: {e}\n")
    elapsed_time = time.time() - start_time
    progress_queue.put((index, elapsed_time, task_message_queue))  # 메시지 큐도 함께 전달
    return elapsed_time

# GUI 클래스 정의
class ArtifactExtractorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Defohari Artifact Extractor")
        self.root.geometry("800x800")

        self.style = ttk.Style()
        self.style.theme_use('default')
        self.style.configure('TFrame', background='#f9f9f9')
        self.style.configure('TLabel', background='#f9f9f9', font=('Arial', 12))
        self.style.configure('TButton', font=('Arial', 12), padding=5)
        self.style.configure('Header.TLabel', font=('Arial', 18, 'bold'), background='#f9f9f9')

        # 진행바 색상 및 디자인 커스터마이즈
        self.style.configure("Custom.Horizontal.TProgressbar",
                             troughcolor='gray',  # 바깥쪽 트랙 색상
                             background='green',  # 진행바 색상
                             thickness=20)        # 진행바 두께

        self.main_frame = ttk.Frame(self.root, padding="15 15 15 15")
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        self.header_label = ttk.Label(self.main_frame, text="Defohari Artifact Extractor", style='Header.TLabel')
        self.header_label.grid(row=0, column=0, columnspan=4, pady=(0, 20))

        self.select_label = ttk.Label(self.main_frame, text="추출할 아티팩트를 선택하세요:")
        self.select_label.grid(row=1, column=0, columnspan=4, pady=(0, 10))

        self.artifact_vars = []
        self.suspicious_vars = []
        artifacts = [
            ('웹 아티팩트 처리', ['python', r'subroutine\web\web_complete.py'], 'web'),
            ('프리패치 아티팩트 처리', ['python', r'subroutine\prefetch\prefetch_complete.py'], 'prefetch'),
            ('이벤트 로그 아티팩트 처리', ['python', r'subroutine\event_log\evt_complete.py'], 'evt_log'),
            ('MFTJ 아티팩트 처리', ['python', r'subroutine\MFTJ\mftJ_complete.py'], 'mft'),
            ('LNK 아티팩트 처리', ['python', r'subroutine\LNK\LNK_complete.py'], 'lnk'),
        ]

        for i, (name, command, identifier) in enumerate(artifacts):
            var = tk.BooleanVar(value=True)
            susp_var = tk.BooleanVar(value=True)

            check = ttk.Checkbutton(self.main_frame, text=name, variable=var)
            check.grid(row=2+i*2, column=0, sticky='w', pady=3, padx=10)
            self.artifact_vars.append((var, identifier))

            susp_check = ttk.Checkbutton(self.main_frame, text=f"  의심스러운 {name} 포함", variable=susp_var)
            susp_check.grid(row=3+i*2, column=0, sticky='w', padx=20, pady=10)
            self.suspicious_vars.append((susp_var, identifier + '_sus'))

            def toggle_suspicious(var=var, susp_check=susp_check):
                if var.get():
                    susp_check.state(['!disabled'])
                    susp_check.configure(state='normal')
                else:
                    susp_check.state(['disabled'])
                    susp_check.configure(state='disabled')

            var.trace_add('write', lambda *args, var=var, susp_check=susp_check: toggle_suspicious(var, susp_check))
            toggle_suspicious(var, susp_check)

        self.csv_var = tk.BooleanVar(value=True)
        self.csv_check = ttk.Checkbutton(self.main_frame, text='CSV 파일 결합', variable=self.csv_var)
        self.csv_check.grid(row=12, column=0, columnspan=4, sticky='w', pady=10)

        self.current_task_label = ttk.Label(self.main_frame, text="대기 중...", font=('Arial', 12, 'bold'))
        self.current_task_label.grid(row=13, column=0, columnspan=4, pady=(15, 5))

        # 진행률 바
        self.progress_bar = ttk.Progressbar(self.main_frame, orient="horizontal", mode="determinate", style="Custom.Horizontal.TProgressbar")
        self.progress_bar.grid(row=14, column=0, columnspan=4, sticky='we', pady=(0, 10))
        self.progress_bar["maximum"] = 100

        self.progress_percent_label = ttk.Label(self.main_frame, text="진행률: 0%")
        self.progress_percent_label.grid(row=15, column=0, pady=(0, 5), padx=5)

        self.elapsed_time_label = ttk.Label(self.main_frame, text="경과 시간: 0분 0초")
        self.elapsed_time_label.grid(row=15, column=1, pady=(0, 5), padx=5)

        self.eta_label = ttk.Label(self.main_frame, text="예상 남은 시간: 계산 중...")
        self.eta_label.grid(row=15, column=2, pady=(0, 5), padx=5)

        self.output_frame = ttk.Frame(self.main_frame)
        self.output_frame.grid(row=16, column=0, columnspan=4, sticky='nsew', pady=(10, 0))
        self.output_frame.rowconfigure(0, weight=1)
        self.output_frame.columnconfigure(0, weight=1)

        self.output_text = tk.Text(self.output_frame, wrap='word', state=tk.DISABLED, font=('Arial', 10))
        self.output_text.grid(row=0, column=0, sticky='nsew')

        self.scrollbar = ttk.Scrollbar(self.output_frame, orient='vertical', command=self.output_text.yview)
        self.scrollbar.grid(row=0, column=1, sticky='ns')
        self.output_text['yscrollcommand'] = self.scrollbar.set

        self.button_frame = ttk.Frame(self.main_frame)
        self.button_frame.grid(row=17, column=0, columnspan=4, pady=(15, 0))

        self.start_button = ttk.Button(self.button_frame, text="추출 시작", command=self.start_extraction)
        self.start_button.grid(row=0, column=0, padx=10)

        self.stop_button = ttk.Button(self.button_frame, text="중지", command=self.stop_extraction, state=tk.DISABLED)
        self.stop_button.grid(row=0, column=1, padx=10)

        self.exit_button = ttk.Button(self.button_frame, text="종료", command=self.root.quit)
        self.exit_button.grid(row=0, column=2, padx=10)

        self.set_env_button = ttk.Button(self.button_frame, text="환경변수 설정", command=self.set_environment_variable)
        self.set_env_button.grid(row=0, column=3, padx=10)

        self.unset_env_button = ttk.Button(self.button_frame, text="환경변수 해제", command=self.unset_environment_variable)
        self.unset_env_button.grid(row=0, column=4, padx=10)

        self.main_frame.rowconfigure(16, weight=1)
        self.main_frame.columnconfigure(0, weight=1)

        self.artifacts_info = artifacts
        self.subroutines = []
        self.total_tasks = 0
        self.progress_queue = queue.Queue()
        self.message_queue = queue.Queue()
        self.log_file_path = "process_logs.txt"
        self.elapsed_times = []
        self.completed_tasks = 0
        self.lock = threading.Lock()
        self.file_lock = threading.Lock()
        self.current_task_index = 0
        self.stop_event = threading.Event()

        if os.path.exists(self.log_file_path):
            os.remove(self.log_file_path)

        self.original_stdout = sys.stdout  # 원래 stdout 저장
        self.pl = PrintLogger(self.output_text, self.message_queue)
        sys.stdout = self.pl  # 초기 설정

        self.load_image('Depohari_Refined_Logo.png')  # 로고 이미지 로드 추가

        self.root.after(100, self.process_queues)

    def load_image(self, image_path):
        image_path = resource_path(image_path)
        try:
            image = Image.open(image_path)
            image = image.resize((200, 200), Image.LANCZOS)  # 이미지 크기 조정
            self.logo_image = ImageTk.PhotoImage(image)

            logo_label = ttk.Label(self.main_frame, image=self.logo_image)
            logo_label.grid(row=2, column=2, rowspan=6, columnspan=2, sticky='n')
        except Exception as e:
            messagebox.showerror("오류", f"이미지 로드 실패: {e}")

    def process_queues(self):
        while not self.message_queue.empty():
            message = self.message_queue.get()
            if isinstance(message, tuple):
                # GUI 업데이트 명령 처리
                command, data = message
                if command == 'current_task':
                    self.current_task_label.config(text=data)
                elif command == 'update_buttons':
                    self.start_button.config(state=tk.NORMAL)
                    self.stop_button.config(state=tk.DISABLED)
                    self.exit_button.config(state=tk.NORMAL)
                elif command == 'log':
                    # 로그 메시지 처리
                    msg_content = data
                    self.output_text.config(state=tk.NORMAL)
                    self.output_text.insert(tk.END, msg_content)
                    self.output_text.see(tk.END)
                    self.output_text.config(state=tk.DISABLED)
            else:
                # 일반 문자열 메시지는 출력 창에 표시
                self.output_text.config(state=tk.NORMAL)
                self.output_text.insert(tk.END, message)
                self.output_text.see(tk.END)
                self.output_text.config(state=tk.DISABLED)

        # 진행률 업데이트를 위한 진행률 큐 처리
        while not self.progress_queue.empty():
            data = self.progress_queue.get()
            if len(data) == 3:
                index, elapsed_time, task_messages = data
            else:
                index, elapsed_time = data
                task_messages = []

            with self.lock:
                self.elapsed_times[index] = elapsed_time
                self.completed_tasks += 1
                # 작업의 메시지를 순차적으로 출력
                for msg in task_messages:
                    self.output_text.config(state=tk.NORMAL)
                    self.output_text.insert(tk.END, msg)
                    self.output_text.see(tk.END)
                    self.output_text.config(state=tk.DISABLED)

        self.root.after(100, self.process_queues)

    def start_extraction(self):
        if os.path.exists(self.log_file_path):
            os.remove(self.log_file_path)

        self.output_text.config(state=tk.NORMAL)
        self.output_text.delete(1.0, tk.END)
        self.output_text.config(state=tk.DISABLED)

        self.subroutines = []
        selected_artifacts = {}
        for (var, identifier), (susp_var, susp_identifier) in zip(self.artifact_vars, self.suspicious_vars):
            if var.get():
                artifact_info = next((item for item in self.artifacts_info if item[2] == identifier), None)
                if artifact_info:
                    args = []
                    task_name = artifact_info[0]
                    # 아티팩트 이름을 포함하여 task_name_for_info 설정
                    task_name_for_info = f"아티팩트 추출 중..."
                    if susp_var.get():
                        args.append('--suspicious')
                        task_name += " (의심스러운 아티팩트 포함)"
                        task_name_for_info = "아티팩트 (의심스러운 아티팩트 포함) 추출 중..."
                        selected_artifacts[susp_identifier] = True
                    self.subroutines.append((task_name, task_name_for_info, artifact_info[1], args))  # 수정된 부분
                    selected_artifacts[identifier] = True

        if not self.subroutines:
            messagebox.showwarning("경고", "최소한 하나의 아티팩트를 선택해야 합니다.")
            return

        self.total_tasks = len(self.subroutines)
        self.elapsed_times = [0] * self.total_tasks
        self.completed_tasks = 0
        self.current_task_index = 0
        self.stop_event.clear()

        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.exit_button.config(state=tk.DISABLED)

        # PrintLogger는 이미 초기화되었으므로 재할당하지 않음

        self.start_time = time.time()  # 경과 시간 측정을 위한 시작 시간 설정
        self.root.after(1000, self.update_progress_bar)

        # 작업들을 병렬로 실행
        self.threads = []
        for index, (task_name, task_name_for_info, command, args) in enumerate(self.subroutines):
            t = threading.Thread(target=run_subroutine, args=(
                task_name,
                task_name_for_info,  # 수정된 부분
                command,
                args,
                self.log_file_path,
                self.progress_queue,
                self.message_queue,
                index,
                self.stop_event,
                self.file_lock
            ))
            t.start()
            self.threads.append(t)

        # CSV 결합 작업이 필요한 경우 추가
        if self.csv_var.get():
            if selected_artifacts:
                args = [json.dumps(selected_artifacts)]
                self.csv_subroutine = ('CSV 파일 결합', 'CSV 파일 결합', ['python', 'csv_totaler.py'], args)  # 수정된 부분
                threading.Thread(target=self.wait_for_completion_and_run_csv).start()
            else:
                messagebox.showwarning("경고", "CSV 파일 결합을 선택하려면 최소한 하나의 아티팩트를 선택해야 합니다.")
                return
        else:
            threading.Thread(target=self.wait_for_completion).start()

    def wait_for_completion(self):
        for t in self.threads:
            t.join()
        total_time = time.time() - self.start_time
        if self.stop_event.is_set():
            self.message_queue.put(('current_task', "작업이 중지되었습니다."))
            self.message_queue.put("작업이 중지되었습니다.\n")
        else:
            self.message_queue.put(('current_task', "완료! 결과 파일을 확인하세요."))
            self.message_queue.put("모든 작업이 완료되었습니다.\n")
        self.message_queue.put(f"총 소요 시간: {int(total_time)}초\n")
        self.message_queue.put(f"모든 로그는 '{self.log_file_path}' 파일에 기록되었습니다.\n")
        # 버튼 상태 변경도 메인 스레드에서 수행
        self.message_queue.put(('update_buttons', None))
        # sys.stdout 원래대로 복구
        sys.stdout = self.original_stdout

    def wait_for_completion_and_run_csv(self):
        for t in self.threads:
            t.join()
        # CSV 결합 작업 실행
        index = self.total_tasks  # 다음 인덱스 사용
        self.total_tasks += 1
        self.elapsed_times.append(0)
        if not self.stop_event.is_set():
            self.message_queue.put(('current_task', "CSV 파일 결합 중..."))
            csv_task_name, csv_task_for_info, csv_command, csv_args = self.csv_subroutine  # 수정된 부분
            elapsed_time = run_subroutine(
                csv_task_name,
                csv_task_for_info,  # 수정된 부분
                csv_command,
                csv_args,
                self.log_file_path,
                self.progress_queue,
                self.message_queue,
                index,
                self.stop_event,
                self.file_lock
            )
            with self.lock:
                self.elapsed_times[index] = elapsed_time
                self.completed_tasks += 1
        total_time = time.time() - self.start_time
        if self.stop_event.is_set():
            self.message_queue.put(('current_task', "작업이 중지되었습니다."))
            self.message_queue.put("작업이 중지되었습니다.\n")
        else:
            self.message_queue.put(('current_task', "완료! 결과 파일을 확인하세요."))
            self.message_queue.put("모든 작업이 완료되었습니다.\n")
        self.message_queue.put(f"총 소요 시간: {int(total_time)}초\n")
        self.message_queue.put(f"모든 로그는 '{self.log_file_path}' 파일에 기록되었습니다.\n")
        # 버튼 상태 변경도 메인 스레드에서 수행
        self.message_queue.put(('update_buttons', None))
        # sys.stdout 원래대로 복구
        sys.stdout = self.original_stdout

    def stop_extraction(self):
        self.stop_event.set()
        self.stop_button.config(state=tk.DISABLED)
        self.current_task_label.config(text="작업 중지 중...")

    def update_progress_bar(self):
        with self.lock:
            elapsed = time.time() - self.start_time
            if self.total_tasks > 0:
                progress = (self.completed_tasks / self.total_tasks) * 100
                if progress > 100:
                    progress = 100
                self.progress_bar['value'] = progress
                self.progress_percent_label.config(text=f"진행률: {int(progress)}%")

                if self.completed_tasks < self.total_tasks:
                    # 남은 작업 시간 계산
                    average_time_per_task = elapsed / max(self.completed_tasks, 1)
                    remaining_tasks = self.total_tasks - self.completed_tasks
                    remaining_time = average_time_per_task * remaining_tasks
                    eta_formatted = time.strftime("%M분 %S초", time.gmtime(remaining_time))
                    self.eta_label.config(text=f"예상 남은 시간: {eta_formatted}")
                else:
                    self.eta_label.config(text="예상 남은 시간: 0분 0초")

                elapsed_formatted = time.strftime("%M분 %S초", time.gmtime(elapsed))
                self.elapsed_time_label.config(text=f"경과 시간: {elapsed_formatted}")
            else:
                # 총 작업 수가 0인 경우
                self.progress_bar['value'] = 0
                self.progress_percent_label.config(text="진행률: 0%")
                self.eta_label.config(text="예상 남은 시간: 0분 0초")
                self.elapsed_time_label.config(text="경과 시간: 0분 0초")

        if self.completed_tasks < self.total_tasks:
            # 1초 후에 다시 update_progress_bar 호출
            self.root.after(1000, self.update_progress_bar)
        else:
            # 작업이 완료되었을 때, 최종 업데이트
            self.progress_bar['value'] = 100
            self.progress_percent_label.config(text="진행률: 100%")
            self.eta_label.config(text="예상 남은 시간: 0분 0초")
            elapsed = time.time() - self.start_time
            elapsed_formatted = time.strftime("%M분 %S초", time.gmtime(elapsed))
            self.elapsed_time_label.config(text=f"경과 시간: {elapsed_formatted}")

    def set_environment_variable(self):
        target_paths = [
            os.path.join(os.getcwd(), 'sleuthkit', 'bin')
        ]
        
        original_path = os.environ.get('PATH', '')
        added_paths = []
        
        for target_path in target_paths:
            if os.path.exists(target_path) and target_path not in original_path.split(';'):
                added_paths.append(target_path)
        
        if added_paths:
            os.environ['PATH'] = f"{original_path};{';'.join(added_paths)}"
            messagebox.showinfo("정보", f"PATH에 다음 경로가 추가되었습니다: {', '.join(added_paths)}")
        else:
            messagebox.showwarning("경고", "추가할 경로가 없거나 이미 존재합니다.")

    def unset_environment_variable(self):
        target_paths = [
            os.path.join(os.getcwd(), 'sleuthkit', 'bin')
        ]
        
        original_path = os.environ.get('PATH', '')
        paths = original_path.split(';')
        removed_paths = []
        
        for target_path in target_paths:
            if target_path in paths:
                paths.remove(target_path)
                removed_paths.append(target_path)

        if removed_paths:
            os.environ['PATH'] = ';'.join(paths)
            messagebox.showinfo("정보", f"PATH에서 다음 경로가 제거되었습니다: {', '.join(removed_paths)}")
        else:
            messagebox.showwarning("경고", "제거할 경로가 없습니다.")

if __name__ == "__main__":
    root = tk.Tk()
    app = ArtifactExtractorApp(root)
    root.mainloop()
