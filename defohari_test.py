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

def get_first_disk_image_path(image_directory):
    # 디스크 이미지 파일 확장자 목록
    disk_image_extensions = ['.e01']
    
    # 지정된 디렉토리에서 모든 파일을 검색
    for filename in os.listdir(image_directory):
        # 파일 확장자를 소문자로 변환하여 확인
        if any(filename.lower().endswith(ext) for ext in disk_image_extensions):
            # 첫 번째 이미지 파일을 찾으면 그 경로 반환
            return os.path.join(image_directory, filename)

    # 이미지 파일이 없을 경우 None 반환
    return None

# 웹 아티팩트 분석 실행 함수
def run_hive_if_selected():
    """웹 아티팩트 분석이 선택된 경우 하이브 분석 실행"""
    if 'web' in selected_artifacts:
        image_path_directory = r"image_here"  # 이미지 파일 경로 설정
        image_path = get_first_disk_image_path(image_path_directory)

        if image_path:
            print(f"디스크 이미지 경로: {image_path}")
            run_hive(image_path)  # 하이브 분석 실행
        else:
            messagebox.showwarning("경고", "이미지 파일을 찾을 수 없습니다.")

def run_hive(image_path):
    """파싱한 하이브 파일을 저장"""
    hives_dir = os.path.join(os.getcwd(), r'subroutine\web\extracted_hives')
    if not os.path.exists(hives_dir):
        try:
            os.makedirs(hives_dir)
            print(f"'{hives_dir}' 폴더가 생성되었습니다.")
            subprocess.run(['python', r'subroutine\web\web_hive_parsing_Log_num.py', '-o', r'subroutine\web\extracted_hives', image_path], check=True)
        except Exception as e:
            print(f"폴더 생성 중 오류 발생: {e}")
    else:
        print(f"'{hives_dir}' 폴더가 이미 존재합니다.")
        subprocess.run(['python', r'subroutine\web\web_hive_parsing_Log_num.py', '-o', r'subroutine\web\extracted_hives', image_path], check=True)

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
        self.root.geometry("1000x800")

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

        # 이미지 로드 및 배치
        self.load_image('Depohari_Refined_Logo.png')

        # 메인 프레임의 열 가중치 설정
        for i in range(1, 11):
            self.main_frame.columnconfigure(i, weight=1)

        # 제목 라벨 수정 (가운데 정렬)
        self.header_label = ttk.Label(self.main_frame, text="Defohari Artifact Extractor",
                                      style='Header.TLabel', wraplength=600, anchor='center')
        self.header_label.grid(row=0, column=1, columnspan=10, pady=(0, 20), sticky='ew')

        # 아티팩트 선택 라벨 수정 (가운데 정렬)
        self.select_label = ttk.Label(self.main_frame, text="추출할 아티팩트를 선택해주세요", anchor='center')
        self.select_label.grid(row=1, column=1, columnspan=10, pady=(0, 10), sticky='ew')

        # 아티팩트 목록
        self.artifacts_info = [
            ('이벤트 로그 아티팩트', ['python', r'subroutine\event_log\evt_complete.py'], 'evt_log'),
            ('MFT & USN 아티팩트', ['python', r'subroutine\MFTJ\mftJ_complete.py'], 'mft'),
            ('웹 아티팩트', ['python', r'subroutine\web\web_complete.py'], 'web'),
            ('프리패치 아티팩트', ['python', r'subroutine\prefetch\prefetch_complete.py'], 'prefetch'),
            ('LNK 아티팩트', ['python', r'subroutine\LNK\LNK_complete.py'], 'lnk'),
            ('Defender 아티팩트', ['python', r'subroutine\defender_log\defender_evt_uncomplete.py'], 'defender'),
        ]

        # 아티팩트 선택 드롭다운 메뉴
        self.selected_artifacts = []
        self.remaining_artifacts = self.artifacts_info.copy()
        self.artifact_var = tk.StringVar()
        self.artifact_combobox = ttk.Combobox(self.main_frame, textvariable=self.artifact_var, state='readonly')
        self.update_artifact_combobox()
        self.artifact_combobox.grid(row=2, column=1, columnspan=7, sticky='ew', padx=10, pady=5)

        self.add_artifact_button = ttk.Button(self.main_frame, text="추가", command=self.add_artifact)
        self.add_artifact_button.grid(row=2, column=8, sticky='e', padx=(5, 15), pady=5)

        self.remove_artifact_button = ttk.Button(self.main_frame, text="해제", command=self.remove_selected_artifacts)
        self.remove_artifact_button.grid(row=2, column=9, sticky='e', padx=(15, 5), pady=5)

        self.clear_all_button = ttk.Button(self.main_frame, text="전체 해제", command=self.clear_all_artifacts)
        self.clear_all_button.grid(row=2, column=11, sticky='e', padx=5, pady=5)

        # 선택된 아티팩트 목록 표시
        self.selected_artifacts_frame = ttk.Frame(self.main_frame)
        self.selected_artifacts_frame.grid(row=3, column=1, columnspan=10, sticky='nsew', pady=10, padx=10)
        self.selected_artifacts_frame.columnconfigure(1, weight=1)
        self.selected_artifacts_labels = []
        self.suspicious_vars = {}
        self.artifact_remove_vars = {}

        self.csv_var = tk.BooleanVar(value=True)
        self.csv_check = ttk.Checkbutton(self.main_frame, text='CSV 파일 결합', variable=self.csv_var)
        self.csv_check.grid(row=12, column=1, columnspan=10, sticky='w', pady=10)

        self.current_task_label = ttk.Label(self.main_frame, text="대기 중...", font=('Arial', 12, 'bold'))
        self.current_task_label.grid(row=13, column=1, columnspan=10, pady=(15, 5))

        # 진행률 바
        self.progress_bar = ttk.Progressbar(self.main_frame, orient="horizontal", mode="determinate", style="Custom.Horizontal.TProgressbar")
        self.progress_bar.grid(row=14, column=1, columnspan=10, sticky='we', pady=(0, 10))
        self.progress_bar["maximum"] = 100

        # 진행률, 경과 시간, 예상 남은 시간 라벨 오른쪽 정렬
        self.progress_percent_label = ttk.Label(self.main_frame, text="진행률: 0%")
        self.progress_percent_label.grid(row=15, column=8, pady=(0, 5), padx=5, sticky='e')

        self.elapsed_time_label = ttk.Label(self.main_frame, text="경과 시간: 0분 0초")
        self.elapsed_time_label.grid(row=15, column=9, pady=(0, 5), padx=10, sticky='e')

        self.eta_label = ttk.Label(self.main_frame, text="예상 남은 시간: 계산 중...")
        self.eta_label.grid(row=15, column=10, pady=(0, 5), padx=5, sticky='e')

        self.output_frame = ttk.Frame(self.main_frame)
        self.output_frame.grid(row=16, column=1, columnspan=10, sticky='nsew', pady=(10, 0))
        self.output_frame.rowconfigure(0, weight=1)
        self.output_frame.columnconfigure(0, weight=1)

        self.output_text = tk.Text(self.output_frame, wrap='word', state=tk.DISABLED, font=('Arial', 10))
        self.output_text.grid(row=0, column=0, sticky='nsew')

        self.scrollbar = ttk.Scrollbar(self.output_frame, orient='vertical', command=self.output_text.yview)
        self.scrollbar.grid(row=0, column=1, sticky='ns')
        self.output_text['yscrollcommand'] = self.scrollbar.set

        self.button_frame = ttk.Frame(self.main_frame)
        self.button_frame.grid(row=17, column=1, columnspan=10, pady=(15, 0), sticky='ew')
        for i in range(5):
            self.button_frame.columnconfigure(i, weight=1)

        self.start_button = ttk.Button(self.button_frame, text="추출 시작", command=self.start_extraction)
        self.start_button.grid(row=0, column=0, padx=10)

        self.stop_button = ttk.Button(self.button_frame, text="중지", command=self.stop_extraction, state=tk.DISABLED)
        self.stop_button.grid(row=0, column=1, padx=10)

        self.exit_button = ttk.Button(self.button_frame, text="종료", command=self.root.quit)
        self.exit_button.grid(row=0, column=2, padx=10)

        self.set_env_button = ttk.Button(self.button_frame, text="환경변수 설정", command=self.set_environment_variable)
        self.set_env_button.grid(row=0, column=3, padx=10, sticky='e')

        self.unset_env_button = ttk.Button(self.button_frame, text="환경변수 해제", command=self.unset_environment_variable)
        self.unset_env_button.grid(row=0, column=4, padx=10, sticky='e')

        self.main_frame.rowconfigure(16, weight=1)
        for i in range(1, 11):
            self.main_frame.columnconfigure(i, weight=1)

        self.subroutines = []
        self.total_tasks = 0
        self.progress_queue = queue.Queue()
        self.message_queue = queue.Queue()
        self.elapsed_times = []
        self.completed_tasks = 0
        self.lock = threading.Lock()
        self.file_lock = threading.Lock()
        self.current_task_index = 0
        self.stop_event = threading.Event()

        self.defender_trace_active = False  # Defender 체크박스 재귀 호출 방지 플래그

        self.original_stdout = sys.stdout  # 원래 stdout 저장
        self.pl = PrintLogger(self.output_text, self.message_queue)
        sys.stdout = self.pl  # 초기 설정

        self.root.after(100, self.process_queues)

    def load_image(self, image_path):
        image_path = resource_path(image_path)
        try:
            image = Image.open(image_path)
            image = image.resize((200, 200), Image.LANCZOS)  # 이미지 크기 조정
            self.logo_image = ImageTk.PhotoImage(image)

            # 이미지 배치를 위해 새로운 프레임 생성
            self.image_frame = ttk.Frame(self.main_frame)
            self.image_frame.grid(row=0, column=0, rowspan=18, sticky='n')  # 다른 위젯들과 겹치지 않도록 배치
            logo_label = ttk.Label(self.image_frame, image=self.logo_image)
            logo_label.pack()
        except Exception as e:
            messagebox.showerror("오류", f"이미지 로드 실패: {e}")

    def update_artifact_combobox(self):
        artifact_names = [name for name, _, _ in self.remaining_artifacts]
        self.artifact_combobox['values'] = artifact_names
        if artifact_names:
            self.artifact_var.set(artifact_names[0])
        else:
            self.artifact_var.set('')

    def add_artifact(self):
        selected_name = self.artifact_var.get()
        if not selected_name:
            messagebox.showwarning("경고", "선택할 아티팩트가 없습니다.")
            return
        # 선택된 아티팩트를 목록에서 제거하고, 선택된 아티팩트에 추가
        for artifact in self.remaining_artifacts:
            if artifact[0] == selected_name:
                self.selected_artifacts.append(artifact)
                self.remaining_artifacts.remove(artifact)
                break
        self.update_artifact_combobox()
        self.display_selected_artifacts()

    def remove_selected_artifacts(self):
        # 선택된 아티팩트 중에서 제거 체크된 항목을 제거
        artifacts_to_remove = []
        for artifact in self.selected_artifacts:
            identifier = artifact[2]
            remove_var = self.artifact_remove_vars.get(identifier)
            if remove_var and remove_var.get():
                artifacts_to_remove.append(artifact)
        if not artifacts_to_remove:
            messagebox.showwarning("경고", "해제할 아티팩트를 선택하세요.")
            return
        for artifact in artifacts_to_remove:
            self.selected_artifacts.remove(artifact)
            self.remaining_artifacts.append(artifact)
            identifier = artifact[2]
            # 관련 변수 제거
            if identifier in self.suspicious_vars:
                del self.suspicious_vars[identifier]
            if identifier in self.artifact_remove_vars:
                del self.artifact_remove_vars[identifier]
        self.update_artifact_combobox()
        self.display_selected_artifacts()

    def clear_all_artifacts(self):
        if not self.selected_artifacts:
            messagebox.showwarning("경고", "선택된 아티팩트가 없습니다.")
            return
        self.remaining_artifacts.extend(self.selected_artifacts)
        self.selected_artifacts.clear()
        self.suspicious_vars.clear()
        self.artifact_remove_vars.clear()
        self.update_artifact_combobox()
        self.display_selected_artifacts()

    def display_selected_artifacts(self):
        # 기존 위젯 제거
        for widget in self.selected_artifacts_frame.winfo_children():
            widget.destroy()
        self.selected_artifacts_labels = []
        for i, (name, _, identifier) in enumerate(self.selected_artifacts):
            remove_var = self.artifact_remove_vars.get(identifier)
            if remove_var is None:
                remove_var = tk.BooleanVar(value=False)
                self.artifact_remove_vars[identifier] = remove_var
            remove_check = ttk.Checkbutton(self.selected_artifacts_frame, variable=remove_var)
            remove_check.grid(row=i, column=0, sticky='w', padx=5, pady=2)

            label = ttk.Label(self.selected_artifacts_frame, text=name)
            label.grid(row=i, column=1, sticky='w', padx=5, pady=2)
            self.selected_artifacts_labels.append(label)

            # 이미 존재하는 susp_var를 사용하여 상태 유지
            susp_var = self.suspicious_vars.get(identifier)
            if susp_var is None:
                susp_var = tk.BooleanVar(value=False)
                self.suspicious_vars[identifier] = susp_var

            susp_check = ttk.Checkbutton(self.selected_artifacts_frame, text="의심스러운 추출 포함", variable=susp_var)
            susp_check.grid(row=i, column=2, sticky='w', padx=5, pady=2)

            if identifier == 'defender':
                # Defender의 의심 추출은 아직 구현되지 않았음을 알림
                def defender_suspicious_trace(*args):
                    if self.defender_trace_active:
                        return  # 재귀 호출 방지
                    if susp_var.get():
                        self.defender_trace_active = True
                        messagebox.showinfo("알림", "Defender 로그의\n의심스러운 추출 기능은 아직 구현되지 않았습니다.", parent=self.root)
                        susp_var.set(False)
                        self.defender_trace_active = False
                susp_var.trace_add('write', defender_suspicious_trace)
                # [TODO] 나중에 이 부분을 제거하여 Defender의 의심 추출 기능을 활성화합니다.

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
        # 하이브 분석을 위한 디스크 이미지 파일 경로 설정
        image_path_directory = r"image_here"
        image_path = get_first_disk_image_path(image_path_directory)
        if not image_path:
            messagebox.showerror("오류", "이미지 파일을 찾을 수 없습니다.")
            return
        
        # 출력 창 초기화
        self.output_text.config(state=tk.NORMAL)
        self.output_text.delete(1.0, tk.END)
        self.output_text.config(state=tk.DISABLED)
        
        # 서브루틴 초기화 및 선택된 아티팩트 추적
        self.subroutines = []
        selected_artifacts = {}
        hive_not_required = False

        if not self.selected_artifacts:
            messagebox.showwarning("경고", "최소한 하나의 아티팩트를 선택해야 합니다.")
            return

        # 선택된 아티팩트 처리
        for index, (name, command, identifier) in enumerate(self.selected_artifacts):
            susp_var = self.suspicious_vars.get(identifier, tk.BooleanVar(value=False))

            # 하이브 추출이 필요한 경우 처리
            if identifier in ['web', 'lnk'] and not hive_not_required:
                try:
                    self.message_queue.put(('current_task', "하이브 추출 중..."))
                    start_time = time.time()
                    run_hive(image_path)  # 하이브 추출 실행  
                    elapsed_time = time.time() - start_time
                    self.message_queue.put(("log", f"하이브 추출 완료. 경과 시간: {elapsed_time:.2f}초\n"))
                    hive_not_required = True
                except Exception as e:
                    messagebox.showerror("오류", f"하이브 추출 중 오류 발생: {e}")
                    return  # 오류가 발생하면 중단

            args = []
            task_name = name
            task_name_for_info = f"{name} 추출 중..."

            selected_artifacts[identifier] = True  # 일반 아티팩트 추가

            if susp_var.get():
                args.append('--suspicious')
                task_name += " (의심스러운 아티팩트 포함)"
                task_name_for_info = f"{name} (의심스러운 아티팩트 포함) 추출 중..."
                selected_artifacts[identifier + '_sus'] = True  # 의심스러운 아티팩트 추가

            # 각 아티팩트별로 로그 파일 경로를 지정
            log_file_path = f"process_logs_{identifier}.txt"
            # 기존 로그 파일 삭제
            if os.path.exists(log_file_path):
                os.remove(log_file_path)

            self.subroutines.append((task_name, task_name_for_info, command, args, log_file_path))

        # 작업 상태 초기화
        self.total_tasks = len(self.subroutines)
        self.elapsed_times = [0] * self.total_tasks
        self.completed_tasks = 0
        self.current_task_index = 0
        self.stop_event.clear()

        # 버튼 상태 업데이트
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.exit_button.config(state=tk.DISABLED)
        
        # 경과 시간 측정을 위한 시작 시간 설정
        self.start_time = time.time() 
        self.root.after(1000, self.update_progress_bar)

        # 작업들을 병렬로 실행 (스레드로 실행)
        self.threads = []
        for index, (task_name, task_name_for_info, command, args, log_file_path) in enumerate(self.subroutines):
            t = threading.Thread(target=run_subroutine, args=(
                task_name,
                task_name_for_info,
                command,
                args,
                log_file_path,
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
                self.csv_subroutine = ('CSV 파일 결합', 'CSV 파일 결합 중...', ['python', 'csv_totaler.py'], args, 'process_logs_csv_totaler.txt')
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
        self.message_queue.put("모든 로그는 각 아티팩트별 로그 파일에 기록되었습니다.\n")
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
            csv_task_name, csv_task_for_info, csv_command, csv_args, csv_log_file = self.csv_subroutine
            elapsed_time = run_subroutine(
                csv_task_name,
                csv_task_for_info,
                csv_command,
                csv_args,
                csv_log_file,
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
        self.message_queue.put("모든 로그는 각 아티팩트별 로그 파일에 기록되었습니다.\n")
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