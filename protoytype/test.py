import tkinter as tk
from tkinter import ttk
import subprocess
import threading
import sys
import os
import time
import queue

# PrintLogger 클래스 정의
class PrintLogger:
    def __init__(self, text_widget):
        self.text_widget = text_widget
        self.queue = queue.Queue()
        self.update_text()
    
    def write(self, message):
        self.queue.put(message)
    
    def update_text(self):
        while not self.queue.empty():
            message = self.queue.get()
            self.text_widget.config(state=tk.NORMAL)
            self.text_widget.insert(tk.END, message)
            self.text_widget.see(tk.END)
            self.text_widget.config(state=tk.DISABLED)
        self.text_widget.after(100, self.update_text)
    
    def flush(self):
        pass

# 서브프로세스 실행 함수
def run_subroutine(command, update_progress, update_task_label):
    try:
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        for line in iter(process.stdout.readline, ''):
            print(line)
        process.stdout.close()
        process.wait()
        if process.returncode != 0:
            print(f"Error: {process.stderr.read()}")
        update_progress()
    except subprocess.CalledProcessError as e:
        print(f"Error occurred: {e}")
    finally:
        update_task_label("작업 완료")

# GUI 클래스 정의
class ArtifactExtractorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Defohari Artifact Extractor")
        
        # 진행 상태 레이블
        self.progress_label = tk.Label(root, text="진행 상황:")
        self.progress_label.pack(pady=10)
        
        # 현재 작업 레이블
        self.current_task_label = tk.Label(root, text="대기 중...", font=("Helvetica", 12))
        self.current_task_label.pack(pady=10)
        
        # 진행률 바
        self.progress_bar = ttk.Progressbar(root, orient="horizontal", length=600, mode="determinate")
        self.progress_bar.pack(pady=10)
        
        # 출력 창
        self.output_text = tk.Text(root, height=30, width=80)
        self.output_text.pack(pady=10)
        
        # 시작 버튼
        self.start_button = tk.Button(root, text="추출 시작", command=self.start_extraction)
        self.start_button.pack(pady=10)
        
        self.subroutines = [
            ('웹 아티팩트 추출 및 처리 중...', ['python', r'subroutine\web\web_complete.py']),
            ('프리패치 아티팩트 추출 및 처리 중...', ['python', r'subroutine\prefetch\prefetch_complete.py']),
            ('이벤트 로그 아티팩트 추출 및 처리 중...', ['python', r'subroutine\event_log\evt_complete.py']),
            ('MFTJ 아티팩트 추출 및 처리 중...', ['python', r'subroutine\MFTJ\mftJ_complete.py']),
            ('LNK 아티팩트 추출 및 처리 중...', ['python', r'subroutine\LNK\LNK_complete.py']),
            ('CSV 파일 결합 중...', ['python', 'csv_totaler.py'])
        ]
        self.total_tasks = len(self.subroutines)
        self.progress_bar["maximum"] = 100
        self.queue = queue.Queue()
        self.root.after(100, self.process_queue)
    
    # 큐를 통해 GUI 업데이트 처리
    def process_queue(self):
        while not self.queue.empty():
            func, args = self.queue.get()
            func(*args)
        self.root.after(100, self.process_queue)
    
    # 추출 시작
    def start_extraction(self):
        pl = PrintLogger(self.output_text)
        sys.stdout = pl
        threading.Thread(target=self.run_subroutines).start()
    
    # 모든 서브프로세스 실행
    def run_subroutines(self):
        for task_name, command in self.subroutines:
            self.update_task_label(task_name)
            print(f"명령 실행: {' '.join(command)}\n")
            run_subroutine(command, self.update_progress, self.update_task_label)
        print("모든 작업이 완료되었습니다.")
        self.update_task_label("완료! combined_analysis.xlsx 파일을 확인하세요.")
    
    # 작업 레이블 업데이트
    def update_task_label(self, task_name):
        self.queue.put((self.current_task_label.config, ({"text": task_name},)))
    
    # 진행률 업데이트
    def update_progress(self):
        progress_increment = 100 / self.total_tasks
        new_value = self.progress_bar["value"] + progress_increment
        self.queue.put((self.progress_bar.config, ({"value": new_value},)))

if __name__ == "__main__":
    root = tk.Tk()
    app = ArtifactExtractorApp(root)
    root.geometry("800x600")
    root.mainloop()
