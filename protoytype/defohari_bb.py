import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import threading
import sys
import os
import time
import queue
import json
from concurrent.futures import ThreadPoolExecutor

# PrintLogger 클래스 정의
class PrintLogger:
    def __init__(self, text_widget, message_queue):
        self.text_widget = text_widget
        self.message_queue = message_queue
        self.update_text()

    def write(self, message):
        self.message_queue.put(message)

    def update_text(self):
        while not self.message_queue.empty():
            message = self.message_queue.get()
            self.text_widget.config(state=tk.NORMAL)
            self.text_widget.insert(tk.END, message)
            self.text_widget.see(tk.END)
            self.text_widget.config(state=tk.DISABLED)
        self.text_widget.after(100, self.update_text)

    def flush(self):
        pass

# 서브프로세스 실행 함수
def run_subroutine(task_name, command, args, log_file_path, progress_queue, message_queue, index, total_tasks, task_start_event, stop_event):
    
    # Windows에서 CMD 창 숨기기 설정
    creationflags = 0
    if sys.platform == 'win32':
        creationflags = subprocess.CREATE_NO_WINDOW
        
    # 작업 시작 이벤트 대기
    task_start_event.wait()
    if stop_event.is_set():
        progress_queue.put((index, 0))  # 진행률 업데이트를 위해 0초로 처리
        return 0
        
    start_time = time.time()
    
    # 작업 시작 메시지 출력
    message_queue.put(f"{task_name} 시작\n")
    message_queue.put(f"'{task_name}'의 로그가 '{log_file_path}' 파일에 기록됩니다.\n\n")
    try:
        command_with_args = command + args
        process = subprocess.Popen(
            command_with_args,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            universal_newlines=True,
            creationflags=creationflags  # 윈도우 cmd창 억제
        )
        # 로그 파일에 쓰기
        with open(log_file_path, 'a', encoding='utf-8') as f:
            f.write(f"===== {task_name} 시작 =====\n")
            while True:
                if stop_event.is_set():
                    process.terminate()
                    message_queue.put(f"{task_name} 중지됨\n")
                    progress_queue.put((index, time.time() - start_time))  # 진행률 업데이트
                    return time.time() - start_time
                line = process.stdout.readline()
                if not line:
                    break
                f.write(line)
            process.stdout.close()
            process.wait()
            if process.returncode != 0:
                error_message = process.stderr.read()
                f.write(f"Error: {error_message}\n")
                message_queue.put(f"{task_name}에서 오류 발생: {error_message}\n")
            else:
                message_queue.put(f"{task_name} 완료\n")
                f.write(f"===== {task_name} 종료 =====\n\n")
    except Exception as e:
        message_queue.put(f"{task_name} 실행 중 오류 발생: {e}\n")
    elapsed_time = time.time() - start_time
    progress_queue.put((index, elapsed_time))
    return elapsed_time

# GUI 클래스 정의
class ArtifactExtractorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Defohari Artifact Extractor")
        self.root.geometry("800x800")

        # 스타일 설정
        self.style = ttk.Style()
        self.style.theme_use('default')
        self.style.configure('TFrame', background='#f9f9f9')
        self.style.configure('TLabel', background='#f9f9f9', font=('Arial', 12))
        self.style.configure('TButton', font=('Arial', 12), padding=5)
        self.style.configure('Header.TLabel', font=('Arial', 18, 'bold'), background='#f9f9f9')

        # 메인 프레임 생성
        self.main_frame = ttk.Frame(self.root, padding="15 15 15 15")
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # 진행 상태 레이블 (헤더)
        self.header_label = ttk.Label(self.main_frame, text="Defohari Artifact Extractor", style='Header.TLabel')
        self.header_label.grid(row=0, column=0, columnspan=4, pady=(0, 20))

        # 아티팩트 선택 레이블
        self.select_label = ttk.Label(self.main_frame, text="추출할 아티팩트를 선택하세요:")
        self.select_label.grid(row=1, column=0, columnspan=4, pady=(0, 10))

        # 아티팩트 선택 체크박스
        self.artifact_vars = []
        self.suspicious_vars = []
        artifacts = [
            ('웹 아티팩트 처리', ['python', r'subroutine\web\web_complete.py'], 'web'),
            ('프리패치 아티팩트 처리', ['python', r'subroutine\prefetch\prefetch_complete.py'], 'prefetch'),
            ('이벤트 로그 아티팩트 처리', ['python', r'subroutine\event_log\evt_complete.py'], 'evt_log'),
            ('MFTJ 아티팩트 처리', ['python', r'subroutine\MFTJ\mftJ_complete.py'], 'mft'),
            ('LNK 아티팩트 처리', ['python', r'subroutine\LNK\LNK_complete.py'], 'lnk'),
        ]

        for i, (name, _, identifier) in enumerate(artifacts):
            var = tk.BooleanVar(value=True)
            susp_var = tk.BooleanVar(value=True)

            # 메인 아티팩트 체크박스
            check = ttk.Checkbutton(self.main_frame, text=name, variable=var)
            check.grid(row=2+i*2, column=0, columnspan=4, sticky='w', pady=2)
            self.artifact_vars.append((var, identifier))

            # 의심스러운 파일 체크박스 (들여쓰기)
            susp_check = ttk.Checkbutton(self.main_frame, text=f"  의심스러운 {name} 포함", variable=susp_var)
            susp_check.grid(row=3+i*2, column=0, columnspan=4, sticky='w', padx=20)
            self.suspicious_vars.append((susp_var, identifier + '_sus'))

            # 메인 아티팩트 선택 시 의심스러운 파일 체크박스 활성화/비활성화
            def toggle_suspicious(var=var, susp_check=susp_check):
                if var.get():
                    susp_check.state(['!disabled'])
                    susp_check.configure(state='normal')
                else:
                    susp_check.state(['disabled'])
                    susp_check.configure(state='disabled')

            var.trace_add('write', lambda *args, var=var, susp_check=susp_check: toggle_suspicious(var, susp_check))

            # 초기 토글 설정
            toggle_suspicious(var, susp_check)

        # CSV 파일 결합 체크박스
        self.csv_var = tk.BooleanVar(value=True)
        self.csv_check = ttk.Checkbutton(self.main_frame, text='CSV 파일 결합', variable=self.csv_var)
        self.csv_check.grid(row=12, column=0, columnspan=4, sticky='w', pady=10)

        # 현재 작업 레이블
        self.current_task_label = ttk.Label(self.main_frame, text="대기 중...", font=('Arial', 12, 'bold'))
        self.current_task_label.grid(row=13, column=0, columnspan=4, pady=(15, 5))

        # 진행률 바
        self.progress_bar = ttk.Progressbar(self.main_frame, orient="horizontal", mode="determinate")
        self.progress_bar.grid(row=14, column=0, columnspan=4, sticky='we', pady=(0, 10))
        self.progress_bar["maximum"] = 100

        # 진행률 퍼센트 레이블
        self.progress_percent_label = ttk.Label(self.main_frame, text="진행률: 0%")
        self.progress_percent_label.grid(row=15, column=0, pady=(0, 5), padx=5)

        # 경과 시간 레이블
        self.elapsed_time_label = ttk.Label(self.main_frame, text="경과 시간: 0분 0초")
        self.elapsed_time_label.grid(row=15, column=1, pady=(0, 5), padx=5)

        # 예상 남은 시간 레이블
        self.eta_label = ttk.Label(self.main_frame, text="예상 남은 시간: 계산 중...")
        self.eta_label.grid(row=15, column=2, pady=(0, 5), padx=5)

        # 출력 창
        self.output_frame = ttk.Frame(self.main_frame)
        self.output_frame.grid(row=16, column=0, columnspan=4, sticky='nsew', pady=(10, 0))
        self.output_frame.rowconfigure(0, weight=1)
        self.output_frame.columnconfigure(0, weight=1)

        self.output_text = tk.Text(self.output_frame, wrap='word', state=tk.DISABLED, font=('Arial', 10))
        self.output_text.grid(row=0, column=0, sticky='nsew')

        self.scrollbar = ttk.Scrollbar(self.output_frame, orient='vertical', command=self.output_text.yview)
        self.scrollbar.grid(row=0, column=1, sticky='ns')
        self.output_text['yscrollcommand'] = self.scrollbar.set

        # 버튼 프레임
        self.button_frame = ttk.Frame(self.main_frame)
        self.button_frame.grid(row=17, column=0, columnspan=4, pady=(15, 0))

        # 시작 버튼
        self.start_button = ttk.Button(self.button_frame, text="추출 시작", command=self.start_extraction)
        self.start_button.grid(row=0, column=0, padx=10)

        # 중지 버튼
        self.stop_button = ttk.Button(self.button_frame, text="중지", command=self.stop_extraction, state=tk.DISABLED)
        self.stop_button.grid(row=0, column=1, padx=10)

        # 종료 버튼
        self.exit_button = ttk.Button(self.button_frame, text="종료", command=self.root.quit)
        self.exit_button.grid(row=0, column=2, padx=10)

        # 그리드 행 및 열 구성
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
        self.task_start_events = []
        self.current_task_index = 0
        self.stop_event = threading.Event()

        # 기존의 로그 파일이 있다면 삭제
        if os.path.exists(self.log_file_path):
            os.remove(self.log_file_path)

        # 큐를 통한 GUI 업데이트를 위한 after 메서드 호출
        self.root.after(100, self.process_queues)

    # 큐를 통한 GUI 업데이트 함수
    def process_queues(self):
        # 메시지 큐 처리
        while not self.message_queue.empty():
            message = self.message_queue.get()
            self.output_text.config(state=tk.NORMAL)
            self.output_text.insert(tk.END, message)
            self.output_text.see(tk.END)
            self.output_text.config(state=tk.DISABLED)

        # 진행률 큐 처리
        while not self.progress_queue.empty():
            index, elapsed_time = self.progress_queue.get()
            with self.lock:
                self.elapsed_times[index] = elapsed_time
                self.completed_tasks += 1

            # 다음 작업 시작
            if self.current_task_index < self.total_tasks - 1:
                self.current_task_index += 1
                next_task_name = self.subroutines[self.current_task_index][0]
                self.current_task_label.config(text=f"{next_task_name} 진행 중...")
                # 다음 작업 시작
                self.task_start_events[self.current_task_index].set()
            else:
                self.current_task_label.config(text="모든 작업 완료")

        self.root.after(100, self.process_queues)

    # 추출 시작
    def start_extraction(self):

        # 로그 파일 초기화
        if os.path.exists(self.log_file_path):
            os.remove(self.log_file_path)
        
        # 출력 창 초기화
        self.output_text.config(state=tk.NORMAL)
        self.output_text.delete(1.0, tk.END)
        self.output_text.config(state=tk.DISABLED)
        
        # 선택된 아티팩트 가져오기
        self.subroutines = []
        selected_artifacts = {}
        for (var, identifier), (susp_var, susp_identifier) in zip(self.artifact_vars, self.suspicious_vars):
            if var.get():
                # 메인 아티팩트 추가
                artifact_info = next((item for item in self.artifacts_info if item[2] == identifier), None)
                if artifact_info:
                    self.subroutines.append((artifact_info[0], artifact_info[1], []))
                    selected_artifacts[identifier] = True

                # 의심스러운 아티팩트 추가
                if susp_var.get():
                    selected_artifacts[susp_identifier] = True

        # CSV 파일 결합 선택 여부 확인
        if self.csv_var.get():
            if selected_artifacts:
                # 선택된 아티팩트를 csv_totaler.py에 JSON 문자열로 전달
                args = [json.dumps(selected_artifacts)]
                self.subroutines.append(('CSV 파일 결합', ['python', 'csv_totaler.py'], args))
            else:
                messagebox.showwarning("경고", "CSV 파일 결합을 선택하려면 최소한 하나의 아티팩트를 선택해야 합니다.")
                return

        if not self.subroutines:
            messagebox.showwarning("경고", "최소한 하나의 아티팩트를 선택해야 합니다.")
            return

        # 초기화
        self.total_tasks = len(self.subroutines)
        self.elapsed_times = [0] * self.total_tasks
        self.completed_tasks = 0
        self.task_start_events = [threading.Event() for _ in range(self.total_tasks)]
        self.current_task_index = 0
        self.stop_event.clear()

        # 버튼 상태 변경
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.exit_button.config(state=tk.DISABLED)

        pl = PrintLogger(self.output_text, self.message_queue)
        sys.stdout = pl
        threading.Thread(target=self.run_subroutines).start()

    # 추출 중지
    def stop_extraction(self):
        self.stop_event.set()
        self.stop_button.config(state=tk.DISABLED)
        self.current_task_label.config(text="작업 중지 중...")

    # 모든 서브프로세스 병렬 실행
    def run_subroutines(self):
        self.start_time = time.time()
        self.executor = ThreadPoolExecutor(max_workers=self.total_tasks)
        futures = []
        for index, (task_name, command, args) in enumerate(self.subroutines):
            future = self.executor.submit(
                run_subroutine,
                task_name,
                command,
                args,
                self.log_file_path,
                self.progress_queue,
                self.message_queue,
                index,
                self.total_tasks,
                self.task_start_events[index],
                self.stop_event
            )
            futures.append(future)

        # 진행률 업데이트 스레드 시작
        self.progress_updater_running = True
        progress_thread = threading.Thread(target=self.update_progress_bar)
        progress_thread.start()

        # 첫 번째 작업 시작
        self.task_start_events[0].set()
        self.current_task_label.config(text=f"{self.subroutines[0][0]} 진행 중...")

        # 모든 작업이 완료되거나 중지될 때까지 대기
        for future in futures:
            future.result()
            if self.stop_event.is_set():
                break

        total_time = time.time() - self.start_time
        if self.stop_event.is_set():
            self.message_queue.put("작업이 중지되었습니다.\n")
            self.current_task_label.config(text="작업이 중지되었습니다.")
        else:
            self.message_queue.put("모든 작업이 완료되었습니다.\n")
            self.current_task_label.config(text="완료! 결과 파일을 확인하세요.")
        self.message_queue.put(f"총 소요 시간: {int(total_time)}초\n")
        self.message_queue.put(f"모든 로그는 '{self.log_file_path}' 파일에 기록되었습니다.\n")
        # 버튼 상태 변경
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.exit_button.config(state=tk.NORMAL)
        # 예상 남은 시간 0으로 설정
        self.eta_label.config(text="예상 남은 시간: 0분 0초")
        # 진행률 업데이트 스레드 종료
        self.progress_updater_running = False
        progress_thread.join()

    # 실시간 진행률 막대 및 시간 업데이트
    def update_progress_bar(self):
        while self.progress_updater_running:
            with self.lock:
                elapsed = time.time() - self.start_time
                if self.completed_tasks > 0:
                    average_time = sum(self.elapsed_times[:self.completed_tasks]) / self.completed_tasks
                    estimated_total_time = average_time * self.total_tasks
                else:
                    # 완료된 작업이 없을 경우, 현재 경과 시간을 사용하여 추정
                    estimated_total_time = elapsed * self.total_tasks / max(self.current_task_index + 1, 1)
                progress = (self.completed_tasks / self.total_tasks) * 100
                if progress > 100:
                    progress = 100
                self.progress_bar['value'] = progress
                self.progress_percent_label.config(text=f"진행률: {int(progress)}%")

                # 예상 남은 시간 업데이트
                remaining_time = estimated_total_time - elapsed
                if remaining_time < 0:
                    remaining_time = 0
                eta_formatted = time.strftime("%M분 %S초", time.gmtime(remaining_time))
                self.eta_label.config(text=f"예상 남은 시간: {eta_formatted}")

                # 경과 시간 업데이트
                elapsed_formatted = time.strftime("%M분 %S초", time.gmtime(elapsed))
                self.elapsed_time_label.config(text=f"경과 시간: {elapsed_formatted}")
            time.sleep(1)
        # 진행률 업데이트 스레드 종료 시 진행률을 완료로 설정
        self.progress_bar['value'] = 100
        self.progress_percent_label.config(text="진행률: 100%")
        self.eta_label.config(text="예상 남은 시간: 0분 0초")

if __name__ == "__main__":
    root = tk.Tk()
    app = ArtifactExtractorApp(root)
    root.mainloop()
